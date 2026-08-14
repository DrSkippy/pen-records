import io
import os
from pathlib import Path

os.environ["PENS_DATABASE_URL"] = "sqlite+pysqlite:////tmp/pen-records-tests.db"
os.environ["PENS_IMAGE_DIR"] = "/tmp/pen-records-test-images"
os.environ["PENS_RESOURCE_BASE_URL"] = "https://resources.test/pens"

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from pen_records.database import Base, SessionLocal, engine, get_db
from pen_records.main import app


@pytest.fixture(autouse=True)
def clean_database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    image_dir = Path(os.environ["PENS_IMAGE_DIR"])
    image_dir.mkdir(exist_ok=True)
    for child in image_dir.iterdir():
        child.unlink()
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def session():
    with SessionLocal() as value:
        yield value


@pytest.fixture
def client(session):
    def override_db():
        yield session

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as value:
        yield value
    app.dependency_overrides.clear()


@pytest.fixture
def png_bytes():
    stream = io.BytesIO()
    Image.new("RGB", (120, 80), "navy").save(stream, "PNG")
    return stream.getvalue()
