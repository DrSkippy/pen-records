from decimal import Decimal

import pytest

from pen_records.importer import drive_download_url, normalize_nib_description, normalize_size, parse_price


def test_price_parser():
    assert parse_price("$1,234.50") == Decimal("1234.50")
    assert parse_price("$0.00") == Decimal("0.00")


def test_price_parser_rejects_invalid_value():
    with pytest.raises(ValueError):
        parse_price("free")


def test_size_normalization():
    assert normalize_size("-") is None
    assert normalize_size("") is None
    assert normalize_size(" #6 ") == "#6"

def test_nib_description_normalization():
    assert normalize_nib_description("Bock Titan EF") == ("Bock Titan", "EF")
    assert normalize_nib_description("TWSBI B - Arch Grind") == ("TWSBI - Arch Grind", "B")
    assert normalize_nib_description("M Cursive Italic") == ("Cursive Italic", "M")
    assert normalize_nib_description("F") == (None, "F")
    assert normalize_nib_description("ASA") == ("ASA", None)
    assert normalize_nib_description("Nemosyne 0.6 Italic") == ("Nemosyne", "MF")



def test_google_drive_download_url():
    result = drive_download_url("https://drive.google.com/open?id=abc123")
    assert result == "https://drive.usercontent.google.com/download?id=abc123&export=download"
