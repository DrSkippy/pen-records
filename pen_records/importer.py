import csv
import hashlib
import re
from collections import defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Nib, NibInstallation, Pen, PenImage, PenNote
from .services import maker, material, save_image, source


def parse_price(value: str) -> Decimal:
    try:
        return Decimal(value.replace("$", "").replace(",", "").strip()).quantize(Decimal("0.01"))
    except InvalidOperation as exc:
        raise ValueError(f"Invalid price: {value}") from exc


def normalize_size(value: str) -> str | None:
    value = value.strip()
    return None if not value or value == "-" else value


LINE_WIDTH_PATTERN = re.compile(r"(?<![A-Za-z0-9])(EF|MF|BB|F|M|B)(?![A-Za-z0-9])", re.IGNORECASE)

def normalize_nib_description(value: str) -> tuple[str | None, str | None]:
    description = " ".join(value.split())
    if description.casefold() == "nemosyne 0.6 italic":
        return "Nemosyne", "MF"
    match = LINE_WIDTH_PATTERN.search(description)
    if not match:
        return description or None, None
    cleaned = (description[: match.start()] + description[match.end() :]).strip(" -")
    return " ".join(cleaned.split()) or None, match.group(1).upper()


def drive_download_url(url: str) -> str:
    if "drive.google.com/open?id=" in url:
        return "https://drive.usercontent.google.com/download?id=" + url.split("id=", 1)[1] + "&export=download"
    return url


def normalized(value: str) -> str:
    return " ".join(value.casefold().split())


def load_image_manifest(csv_path: Path) -> tuple[Path, dict[tuple[str, str], list[dict]]]:
    image_dir = csv_path.parent / "images"
    manifest_path = image_dir / "manifest.csv"
    matches: dict[tuple[str, str], list[dict]] = defaultdict(list)
    if not manifest_path.is_file():
        return image_dir, matches
    with manifest_path.open(newline="", encoding="utf-8-sig") as handle:
        for row_number, row in enumerate(csv.DictReader(handle), start=2):
            filename = (row.get("filename") or "").strip()
            maker_name = (row.get("maker") or "").strip()
            model = (row.get("model") or "").strip()
            if not filename or not maker_name or not model:
                raise ValueError(f"Invalid local image manifest row {row_number}")
            candidate = (image_dir / filename).resolve()
            if image_dir.resolve() not in candidate.parents:
                raise ValueError(f"Image path escapes import_data/images on manifest row {row_number}")
            row["filename"] = filename
            matches[(normalized(maker_name), normalized(model))].append(row)
    return image_dir, matches


def attach_local_images(pen: Pen, row: dict, image_dir: Path, manifest: dict, result: dict) -> bool:
    entries = manifest.get((normalized(row["Maker"]), normalized(row["Pen"])), [])
    acquired_on = row["Date Acquired"].strip()
    existing = {image.original_filename for image in pen.images}
    local_available = False
    for entry in entries:
        entry_date = (entry.get("acquired_on") or "").strip()
        if entry_date and entry_date != acquired_on:
            continue
        marker = f"local:{entry['filename']}"
        if marker in existing:
            local_available = True
            result["local_images_skipped"] += 1
            continue
        path = image_dir / entry["filename"]
        try:
            image = save_image(
                path.read_bytes(),
                marker,
                (entry.get("caption") or "").strip() or None,
                int((entry.get("sort_order") or "0").strip()),
            )
            pen.images.append(image)
            existing.add(marker)
            result["local_images_added"] += 1
            local_available = True
        except Exception as exc:
            result["local_image_failures"].append({"file": entry["filename"], "error": str(exc)})
    if local_available:
        legacy = [
            image for image in pen.images if image.filename is None and image.source_url == row["Picture"].strip()
        ]
        for image in legacy:
            pen.images.remove(image)
            result["legacy_image_links_removed"] += 1
    return local_available


def import_csv(session: Session, path: Path, download_images: bool = True) -> dict:
    result = {
        "created": 0,
        "skipped": 0,
        "local_images_added": 0,
        "local_images_skipped": 0,
        "legacy_image_links_removed": 0,
        "local_image_failures": [],
        "images_downloaded": 0,
        "image_failures": [],
    }
    image_dir, manifest = load_image_manifest(path)
    with path.open(newline="", encoding="utf-8-sig") as source_file:
        for row_number, row in enumerate(csv.DictReader(source_file), start=2):
            fingerprint = hashlib.sha256("\x1f".join(row.values()).encode()).hexdigest()
            pen = session.scalar(select(Pen).where(Pen.legacy_import_key == fingerprint))
            if pen:
                attach_local_images(pen, row, image_dir, manifest, result)
                session.commit()
                result["skipped"] += 1
                continue
            try:
                pen = Pen(
                    model=row["Pen"].strip(),
                    maker=maker(session, row["Maker"]),
                    source=source(session, row["Source"]),
                    acquired_on=date.fromisoformat(row["Date Acquired"]),
                    disposed_on=date.fromisoformat(row["Date Disposessed"])
                    if row["Date Disposessed"].strip()
                    else None,
                    purchase_price=parse_price(row["Price"]),
                    legacy_import_key=fingerprint,
                    import_payload=row,
                )
                original_description, original_line_width = normalize_nib_description(row["Original Nib"])
                original = Nib(
                    pen=pen,
                    description=original_description,
                    material=material(session, row["Orig Nib Material"]),
                    nib_size=normalize_size(row["Nib Size"]),
                    line_width=original_line_width,
                    is_original=True,
                )
                current_desc = row["Current Nib"].strip()
                if current_desc:
                    NibInstallation(pen=pen, nib=original, installed_on=pen.acquired_on, is_current=False)
                    current_description, current_line_width = normalize_nib_description(current_desc)
                    alternate = Nib(
                        pen=pen,
                        description=current_description,
                        material=material(session, row["Curr Nib Material"]),
                        nib_size=normalize_size(row["Nib Size"]),
                        line_width=current_line_width,
                        is_original=False,
                    )
                    NibInstallation(pen=pen, nib=alternate, installed_on=None, is_current=True)
                else:
                    NibInstallation(pen=pen, nib=original, installed_on=pen.acquired_on, is_current=True)
                if row["Notes"].strip():
                    pen.notes.append(PenNote(text=row["Notes"].strip()))
                session.add(pen)
                session.flush()
                matched_local = attach_local_images(pen, row, image_dir, manifest, result)
                picture = row["Picture"].strip()
                if picture and not matched_local:
                    image = None
                    if download_images:
                        try:
                            response = httpx.get(drive_download_url(picture), follow_redirects=True, timeout=30)
                            response.raise_for_status()
                            image = save_image(response.content, f"legacy-row-{row_number}", None, 0)
                            result["images_downloaded"] += 1
                        except Exception as exc:
                            result["image_failures"].append({"row": row_number, "url": picture, "error": str(exc)})
                    pen.images.append(image or PenImage(source_url=picture, sort_order=0))
                session.commit()
                result["created"] += 1
            except Exception:
                session.rollback()
                raise
    return result
