import io

import pytest
from PIL import Image

from pen_records.config import get_settings
from pen_records.models import PenImage
from pen_records.services import delete_image_files, image_urls, save_image


@pytest.fixture
def png_bytes():
    stream = io.BytesIO()
    Image.new("RGB", (120, 80), "navy").save(stream, "PNG")
    return stream.getvalue()


def test_save_image_urls_and_cleanup(png_bytes):
    saved = save_image(png_bytes, "phone.png", "Blue pen", 3)
    directory = get_settings().image_dir
    assert saved.width == 120 and saved.height == 80
    assert (directory / saved.filename).exists()
    url, thumb = image_urls(saved)
    assert url.endswith(saved.filename)
    assert thumb.endswith(saved.thumbnail_filename)
    delete_image_files(saved)
    assert not (directory / saved.filename).exists()


def test_external_url_and_invalid_images(monkeypatch, png_bytes):
    external = PenImage(source_url="https://example.test/legacy.jpg")
    assert image_urls(external) == (external.source_url, external.source_url)
    with pytest.raises(ValueError, match="invalid"):
        save_image(b"not an image", "bad", None, 0)
    monkeypatch.setattr(get_settings(), "max_upload_bytes", 2)
    with pytest.raises(ValueError, match="20 MB"):
        save_image(png_bytes, "big.png", None, 0)
