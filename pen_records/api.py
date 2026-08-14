import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import func, or_, select, text
from sqlalchemy.orm import Session, selectinload

from .database import get_db
from .models import Maker, Nib, NibInstallation, NibMaterial, Pen, PenImage, PenNote, Source
from .schemas import InstallInput, NibInput, NoteInput, PenCreate, PenUpdate
from .services import delete_image_files, image_urls, maker, material, save_image, source

router = APIRouter(prefix="/api/v1")


def pen_query():
    return select(Pen).options(
        selectinload(Pen.nibs).selectinload(Nib.material),
        selectinload(Pen.installations),
        selectinload(Pen.notes),
        selectinload(Pen.images),
    )


def get_pen(db: Session, pen_id: uuid.UUID) -> Pen:
    pen = db.scalar(pen_query().where(Pen.id == pen_id))
    if not pen:
        raise HTTPException(404, "Pen not found")
    return pen


def pen_dict(pen: Pen) -> dict:
    images = []
    for item in sorted(pen.images, key=lambda image: image.sort_order):
        url, thumbnail_url = image_urls(item)
        images.append(
            {
                "id": item.id,
                "url": url,
                "thumbnail_url": thumbnail_url,
                "caption": item.caption,
                "sort_order": item.sort_order,
            }
        )
    return {
        "id": pen.id,
        "model": pen.model,
        "maker": {"id": pen.maker.id, "name": pen.maker.name},
        "source": {"id": pen.source.id, "name": pen.source.name} if pen.source else None,
        "acquired_on": pen.acquired_on,
        "acquired_on_approximate": pen.acquired_on_approximate,
        "disposed_on": pen.disposed_on,
        "disposed_on_approximate": pen.disposed_on_approximate,
        "purchase_price": pen.purchase_price,
        "currency": pen.currency,
        "nibs": [
            {
                "id": nib.id,
                "description": nib.description,
                "material": {"id": nib.material.id, "name": nib.material.name},
                "size": nib.size,
                "is_original": nib.is_original,
            }
            for nib in pen.nibs
        ],
        "installations": [
            {
                "id": item.id,
                "nib_id": item.nib_id,
                "installed_on": item.installed_on,
                "removed_on": item.removed_on,
                "is_current": item.is_current,
            }
            for item in pen.installations
        ],
        "notes": [
            {
                "id": note.id,
                "text": note.text,
                "event_on": note.event_on,
                "created_at": note.created_at,
                "updated_at": note.updated_at,
            }
            for note in sorted(pen.notes, key=lambda note: note.created_at, reverse=True)
        ],
        "images": images,
    }


@router.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok"}


@router.get("/lookups")
def lookups(db: Session = Depends(get_db)):
    def values(model):
        return [{"id": row.id, "name": row.name} for row in db.scalars(select(model).order_by(model.name))]

    return {"makers": values(Maker), "sources": values(Source), "materials": values(NibMaterial)}


@router.get("/pens")
def list_pens(
    q: str | None = None,
    maker_id: int | None = None,
    material_id: int | None = None,
    include_disposed: bool = False,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    stmt = pen_query().order_by(Pen.acquired_on.desc(), Pen.model).limit(limit).offset(offset)
    count = select(func.count(Pen.id))
    filters = []
    if not include_disposed:
        filters.append(Pen.disposed_on.is_(None))
    if q:
        filters.append(or_(Pen.model.ilike(f"%{q}%"), Pen.maker.has(Maker.name.ilike(f"%{q}%"))))
    if maker_id:
        filters.append(Pen.maker_id == maker_id)
    if material_id:
        filters.append(Pen.nibs.any((Nib.material_id == material_id) & Nib.is_original))
    if filters:
        stmt, count = stmt.where(*filters), count.where(*filters)
    return {
        "items": [pen_dict(pen) for pen in db.scalars(stmt).unique()],
        "total": db.scalar(count),
        "limit": limit,
        "offset": offset,
    }


@router.post("/pens", status_code=status.HTTP_201_CREATED)
def create_pen(payload: PenCreate, db: Session = Depends(get_db)):
    pen = Pen(
        model=payload.model.strip(),
        maker=maker(db, payload.maker),
        source=source(db, payload.source),
        acquired_on=payload.acquired_on,
        acquired_on_approximate=payload.acquired_on_approximate,
        disposed_on=payload.disposed_on,
        disposed_on_approximate=payload.disposed_on_approximate,
        purchase_price=payload.purchase_price,
    )
    nib = Nib(
        description=payload.original_nib.description.strip(),
        material=material(db, payload.original_nib.material),
        size=payload.original_nib.size,
        is_original=True,
        pen=pen,
    )
    NibInstallation(
        pen=pen, nib=nib, installed_on=payload.original_nib.installed_on or payload.acquired_on, is_current=True
    )
    db.add(pen)
    db.commit()
    return pen_dict(get_pen(db, pen.id))


@router.get("/pens/{pen_id}")
def read_pen(pen_id: uuid.UUID, db: Session = Depends(get_db)):
    return pen_dict(get_pen(db, pen_id))


@router.patch("/pens/{pen_id}")
def update_pen(pen_id: uuid.UUID, payload: PenUpdate, db: Session = Depends(get_db)):
    pen = get_pen(db, pen_id)
    changes = payload.model_dump(exclude_unset=True)
    if "maker" in changes:
        pen.maker = maker(db, changes.pop("maker"))
    if "source" in changes:
        pen.source = source(db, changes.pop("source"))
    if changes.pop("clear_disposed_on", False):
        pen.disposed_on = None
    for key, value in changes.items():
        setattr(pen, key, value)
    if pen.disposed_on and pen.disposed_on < pen.acquired_on:
        db.rollback()
        raise HTTPException(422, "disposed_on cannot precede acquired_on")
    db.commit()
    return pen_dict(get_pen(db, pen.id))


@router.delete("/pens/{pen_id}", status_code=204)
def delete_pen(pen_id: uuid.UUID, db: Session = Depends(get_db)):
    pen = get_pen(db, pen_id)
    for image in pen.images:
        delete_image_files(image)
    db.delete(pen)
    db.commit()


@router.post("/pens/{pen_id}/nibs", status_code=201)
def add_nib(pen_id: uuid.UUID, payload: NibInput, db: Session = Depends(get_db)):
    pen = get_pen(db, pen_id)
    nib = Nib(
        pen=pen,
        description=payload.description.strip(),
        material=material(db, payload.material),
        size=payload.size,
        is_original=False,
    )
    db.add(nib)
    db.commit()
    db.refresh(nib)
    return {
        "id": nib.id,
        "description": nib.description,
        "material": nib.material,
        "size": nib.size,
        "is_original": False,
    }


@router.post("/pens/{pen_id}/nibs/{nib_id}/install", status_code=201)
def install_nib(pen_id: uuid.UUID, nib_id: uuid.UUID, payload: InstallInput, db: Session = Depends(get_db)):
    pen = get_pen(db, pen_id)
    nib = next((item for item in pen.nibs if item.id == nib_id), None)
    if not nib:
        raise HTTPException(404, "Nib not found on this pen")
    current = next((item for item in pen.installations if item.is_current), None)
    if current and current.nib_id == nib_id:
        raise HTTPException(409, "Nib is already installed")
    if current:
        current.is_current = False
        current.removed_on = payload.previous_removed_on or payload.installed_on
    installation = NibInstallation(pen=pen, nib=nib, installed_on=payload.installed_on, is_current=True)
    db.add(installation)
    db.commit()
    db.refresh(installation)
    return installation


@router.post("/pens/{pen_id}/notes", status_code=201)
def add_note(pen_id: uuid.UUID, payload: NoteInput, db: Session = Depends(get_db)):
    note = PenNote(pen=get_pen(db, pen_id), **payload.model_dump())
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.delete("/pens/{pen_id}/notes/{note_id}", status_code=204)
def delete_note(pen_id: uuid.UUID, note_id: uuid.UUID, db: Session = Depends(get_db)):
    note = db.scalar(select(PenNote).where(PenNote.id == note_id, PenNote.pen_id == pen_id))
    if not note:
        raise HTTPException(404, "Note not found")
    db.delete(note)
    db.commit()


@router.post("/pens/{pen_id}/images", status_code=201)
def upload_image(
    pen_id: uuid.UUID,
    file: UploadFile = File(),
    caption: str | None = Form(None),
    sort_order: int = Form(0),
    db: Session = Depends(get_db),
):
    pen = get_pen(db, pen_id)
    try:
        image = save_image(file.file.read(), file.filename, caption, sort_order)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    image.pen = pen
    db.add(image)
    db.commit()
    db.refresh(image)
    url, thumb = image_urls(image)
    return {
        "id": image.id,
        "url": url,
        "thumbnail_url": thumb,
        "caption": image.caption,
        "sort_order": image.sort_order,
    }


@router.delete("/pens/{pen_id}/images/{image_id}", status_code=204)
def delete_image(pen_id: uuid.UUID, image_id: uuid.UUID, db: Session = Depends(get_db)):
    image = db.scalar(select(PenImage).where(PenImage.id == image_id, PenImage.pen_id == pen_id))
    if not image:
        raise HTTPException(404, "Image not found")
    delete_image_files(image)
    db.delete(image)
    db.commit()


REPORT_FILTER = "" if False else " AND p.disposed_on IS NULL"


def report_rows(db: Session, query: str, include_disposed: bool):
    condition = "" if include_disposed else " AND p.disposed_on IS NULL"
    return [dict(row._mapping) for row in db.execute(text(query.replace("/*status*/", condition)))]


@router.get("/reports")
def reports(include_disposed: bool = False, db: Session = Depends(get_db)):
    where = None if include_disposed else Pen.disposed_on.is_(None)
    stmt = select(
        func.count(Pen.id),
        func.coalesce(func.sum(Pen.purchase_price), 0),
        func.coalesce(func.avg(Pen.purchase_price), 0),
    )
    if where is not None:
        stmt = stmt.where(where)
    count, total, average = db.execute(stmt).one()
    maker_rows = report_rows(
        db,
        "SELECT m.name, count(*) count, sum(p.purchase_price) total, avg(p.purchase_price) average FROM pens p JOIN makers m ON m.id=p.maker_id WHERE true /*status*/ GROUP BY m.name ORDER BY total DESC",
        include_disposed,
    )
    material_rows = report_rows(
        db,
        "SELECT nm.name, count(*) count, sum(p.purchase_price) total, avg(p.purchase_price) average FROM pens p JOIN nibs n ON n.pen_id=p.id AND n.is_original JOIN nib_materials nm ON nm.id=n.material_id WHERE true /*status*/ GROUP BY nm.name ORDER BY total DESC",
        include_disposed,
    )
    quarterly = report_rows(
        db,
        "SELECT to_char(date_trunc('quarter', p.acquired_on), 'YYYY-\"Q\"Q') quarter, count(*) count, sum(p.purchase_price) total FROM pens p WHERE true /*status*/ GROUP BY 1 ORDER BY 1",
        include_disposed,
    )
    scatter = report_rows(
        db,
        "SELECT p.id, p.acquired_on, p.purchase_price price, m.name maker, p.model FROM pens p JOIN makers m ON m.id=p.maker_id WHERE true /*status*/ ORDER BY p.acquired_on",
        include_disposed,
    )
    pivot = report_rows(
        db,
        "SELECT n.description, nm.name material, sum(p.purchase_price) total FROM pens p JOIN nibs n ON n.pen_id=p.id AND n.is_original JOIN nib_materials nm ON nm.id=n.material_id WHERE true /*status*/ GROUP BY n.description,nm.name ORDER BY n.description,nm.name",
        include_disposed,
    )
    return {
        "summary": {"count": count, "total": total, "average": average},
        "makers": maker_rows,
        "materials": material_rows,
        "quarterly": quarterly,
        "scatter": scatter,
        "pivot": pivot,
    }
