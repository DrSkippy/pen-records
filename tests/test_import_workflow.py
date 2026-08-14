import csv
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from sqlalchemy import func, select

from pen_records.importer import import_csv
from pen_records.models import Nib, Pen, PenImage, PenNote

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


def write_csv(path: Path, rows: list[list[str]]):
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(HEADERS)
        writer.writerows(rows)


def test_full_import_is_idempotent_and_normalizes(session, tmp_path):
    path = tmp_path / "pens.csv"
    write_csv(
        path,
        [
            [
                "2024-01-02",
                "Model A",
                "F",
                "14k Gold",
                "-",
                "M",
                "Steel",
                "Maker",
                "Shop",
                "https://bad.test/a",
                "$1,200.00",
                "First note",
                "",
            ],
            ["2023-01-01", "Model B", "EF", "Steel", "#6", "", "", "Maker", "", "", "$0.00", "", "2024-01-01"],
        ],
    )
    with patch("pen_records.importer.httpx.get", side_effect=RuntimeError("offline")):
        result = import_csv(session, path)
    assert result["created"] == 2 and len(result["image_failures"]) == 1
    assert session.scalar(select(func.count(Pen.id))) == 2
    assert session.scalar(select(func.count(Nib.id))) == 3
    assert session.scalar(select(func.count(PenNote.id))) == 1
    assert session.scalar(select(PenImage)).source_url == "https://bad.test/a"
    assert import_csv(session, path, download_images=False)["skipped"] == 2


def test_import_downloads_valid_image(session, tmp_path, png_bytes):
    path = tmp_path / "pens.csv"
    write_csv(
        path,
        [
            [
                "2024-01-02",
                "Model",
                "F",
                "Gold",
                "#6",
                "",
                "",
                "Maker",
                "Shop",
                "https://drive.google.com/open?id=abc",
                "$10.00",
                "",
                "",
            ]
        ],
    )
    response = Mock(content=png_bytes)
    response.raise_for_status.return_value = None
    with patch("pen_records.importer.httpx.get", return_value=response) as get:
        result = import_csv(session, path)
    assert result["images_downloaded"] == 1
    assert session.scalar(select(PenImage)).filename.endswith(".webp")
    assert "drive.usercontent.google.com" in get.call_args.args[0]


def test_import_rolls_back_bad_rows(session, tmp_path):
    path = tmp_path / "bad.csv"
    write_csv(path, [["bad-date", "Model", "F", "Steel", "#6", "", "", "Maker", "Shop", "", "$10", "", ""]])
    with pytest.raises(ValueError):
        import_csv(session, path)
    assert session.scalar(select(func.count(Pen.id))) == 0
