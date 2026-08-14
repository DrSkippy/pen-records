import csv

import pytest
from sqlalchemy import func, select

from pen_records.importer import import_csv, load_image_manifest
from pen_records.models import Pen, PenImage

HEADERS = [
    "Date Acquired",
    "Pen",
    "Original Nib",
    "Orig Nib Material",
    "Nib Size",
    "Current Nib",
    "Curr Nib Material",
    "Maker",
    "Source",
    "Picture",
    "Price",
    "Notes",
    "Date Disposessed",
]


def write_pen_csv(path):
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(HEADERS)
        writer.writerow(
            [
                "2024-01-02",
                "Model A",
                "F",
                "Steel",
                "#6",
                "",
                "",
                "Maker",
                "Shop",
                "https://legacy.test/image",
                "$20.00",
                "",
                "",
            ]
        )


def write_manifest(directory, filename="model-a.png"):
    directory.mkdir()
    with (directory / "manifest.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["filename", "maker", "model", "acquired_on", "caption", "sort_order"])
        writer.writerow([filename, "Maker", "Model A", "2024-01-02", "Local photo", "2"])


def test_rerun_enriches_existing_pen_without_duplicates(session, tmp_path, png_bytes):
    csv_path = tmp_path / "pens.csv"
    write_pen_csv(csv_path)
    first = import_csv(session, csv_path, download_images=False)
    assert first["created"] == 1
    assert first["local_images_added"] == 0

    image_dir = tmp_path / "images"
    write_manifest(image_dir)
    (image_dir / "model-a.png").write_bytes(png_bytes)

    second = import_csv(session, csv_path, download_images=False)
    assert second["created"] == 0
    assert second["skipped"] == 1
    assert second["local_images_added"] == 1
    images = list(session.scalars(select(PenImage).where(PenImage.filename.is_not(None))))
    assert len(images) == 1
    assert images[0].original_filename == "local:model-a.png"
    assert images[0].caption == "Local photo"

    third = import_csv(session, csv_path, download_images=False)
    assert third["local_images_added"] == 0
    assert third["local_images_skipped"] == 1
    assert session.scalar(select(func.count(Pen.id))) == 1
    assert session.scalar(select(func.count(PenImage.id))) == 1


def test_manifest_rejects_missing_fields_and_escaping_paths(tmp_path):
    csv_path = tmp_path / "pens.csv"
    csv_path.write_text("")
    image_dir = tmp_path / "images"
    image_dir.mkdir()
    (image_dir / "manifest.csv").write_text("filename,maker,model\n,Maker,Model\n")
    with pytest.raises(ValueError, match="Invalid local image manifest"):
        load_image_manifest(csv_path)
    (image_dir / "manifest.csv").write_text("filename,maker,model\n../secret,Maker,Model\n")
    with pytest.raises(ValueError, match="escapes"):
        load_image_manifest(csv_path)


def test_missing_manifest_file_is_reported(session, tmp_path):
    csv_path = tmp_path / "pens.csv"
    write_pen_csv(csv_path)
    image_dir = tmp_path / "images"
    write_manifest(image_dir, "missing.png")
    result = import_csv(session, csv_path, download_images=False)
    assert result["local_images_added"] == 0
    assert result["local_image_failures"][0]["file"] == "missing.png"
