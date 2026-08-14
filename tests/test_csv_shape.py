import csv
from pathlib import Path

import pytest


def test_source_csv_baseline():
    path = Path("import_data/Pen Collection - Pen Data.csv")
    if not path.exists():
        pytest.skip("private import data is not present")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 48
    assert sum(bool(row["Current Nib"].strip()) for row in rows) == 15
    assert sum(bool(row["Notes"].strip()) for row in rows) == 43
    assert sum(bool(row["Date Disposessed"].strip()) for row in rows) == 19
    assert sum(bool(row["Picture"].strip()) for row in rows) == 29
