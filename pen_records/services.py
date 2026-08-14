import io
import uuid
from pathlib import Path

from PIL import Image, ImageOps
from pillow_heif import register_heif_opener
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import get_settings
from .models import Maker, NibMaterial, PenImage, Source

register_heif_opener()


def lookup(session: Session, model, name: str | None):
    if not name or not name.strip():
        return None
    clean = " ".join(name.split())
    found = session.scalar(select(model).where(model.name.ilike(clean)))
    if found:
        return found
    found = model(name=clean)
    session.add(found)
    session.flush()
    return found


def maker(session: Session, name: str) -> Maker:
    return lookup(session, Maker, name)


def source(session: Session, name: str | None) -> Source | None:
    return lookup(session, Source, name)


def material(session: Session, name: str) -> NibMaterial:
    aliases = {"14k gold": "14K Gold", "18k gold": "18K Gold", "21k gold": "21K Gold"}
    return lookup(session, NibMaterial, aliases.get(name.strip().lower(), name))


def image_urls(image: PenImage) -> tuple[str, str]:
    base = get_settings().resource_base_url.rstrip("/")
    url = f"{base}/{image.filename}" if image.filename else image.source_url or ""
    thumb = f"{base}/{image.thumbnail_filename}" if image.thumbnail_filename else url
    return url, thumb


def save_image(data: bytes, original_filename: str | None, caption: str | None, order: int) -> PenImage:
    settings = get_settings()
    if len(data) > settings.max_upload_bytes:
        raise ValueError("Image exceeds the 20 MB upload limit")
    try:
        image = Image.open(io.BytesIO(data))
        image.load()
    except Exception as exc:
        raise ValueError("Unsupported or invalid image") from exc
    image = ImageOps.exif_transpose(image).convert("RGB")
    image.thumbnail((2400, 2400))
    token = uuid.uuid4().hex
    filename, thumbnail = f"{token}.webp", f"{token}-thumb.webp"
    directory: Path = settings.image_dir
    directory.mkdir(parents=True, exist_ok=True)
    image.save(directory / filename, "WEBP", quality=88, method=6)
    thumb = image.copy()
    thumb.thumbnail((480, 480))
    thumb.save(directory / thumbnail, "WEBP", quality=82, method=6)
    return PenImage(
        filename=filename,
        thumbnail_filename=thumbnail,
        original_filename=original_filename,
        media_type="image/webp",
        width=image.width,
        height=image.height,
        byte_size=(directory / filename).stat().st_size,
        caption=caption,
        sort_order=order,
    )


def delete_image_files(image: PenImage) -> None:
    directory = get_settings().image_dir
    for name in (image.filename, image.thumbnail_filename):
        if name:
            (directory / Path(name).name).unlink(missing_ok=True)
