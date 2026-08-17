from datetime import date
from unittest.mock import patch

from pen_records import api

PEN = {
    "model": "Custom 823",
    "maker": "Pilot",
    "source": "Local shop",
    "acquired_on": "2024-02-03",
    "purchase_price": "250.00",
    "original_nib": {"description": "Pilot", "material": "14k gold", "nib_size": "#15", "line_width": "F"},
}


def create_pen(client, **changes):
    payload = PEN | changes
    response = client.post("/api/v1/pens", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_root_health_lookups_and_pen_crud(client):
    assert client.get("/").json()["name"] == "Pen Records API"
    assert client.get("/api/v1/health").json() == {"status": "ok"}
    pen = create_pen(client)
    pen_id = pen["id"]
    assert pen["maker"]["name"] == "Pilot"
    assert pen["nibs"][0]["material"]["name"] == "14K Gold"
    assert pen["nibs"][0]["nib_size"] == "#15"
    assert pen["nibs"][0]["line_width"] == "F"
    assert pen["installations"][0]["is_current"] is True

    detail = client.get(f"/api/v1/pens/{pen_id}")
    assert detail.status_code == 200
    listing = client.get("/api/v1/pens?q=pilot&maker_id=1&material_id=1")
    assert listing.json()["total"] == 1
    assert client.get("/api/v1/pens?q=missing").json()["total"] == 0
    lookups = client.get("/api/v1/lookups").json()
    assert [item["name"] for item in lookups["makers"]] == ["Pilot"]

    changed = client.patch(
        f"/api/v1/pens/{pen_id}",
        json={
            "model": "Custom 823 Amber",
            "maker": "Pilot",
            "source": "Pen show",
            "purchase_price": "275.50",
            "disposed_on": "2025-01-01",
        },
    )
    assert changed.status_code == 200
    assert changed.json()["model"] == "Custom 823 Amber"
    assert client.get("/api/v1/pens").json()["total"] == 0
    assert client.get("/api/v1/pens?include_disposed=true").json()["total"] == 1
    restored = client.patch(f"/api/v1/pens/{pen_id}", json={"clear_disposed_on": True})
    assert restored.json()["disposed_on"] is None
    assert client.patch(f"/api/v1/pens/{pen_id}", json={"disposed_on": "2020-01-01"}).status_code == 422

    assert client.delete(f"/api/v1/pens/{pen_id}").status_code == 204
    assert client.get(f"/api/v1/pens/{pen_id}").status_code == 404


def test_duplicate_names_reuse_lookups(client):
    create_pen(client)
    second = create_pen(client, model="Vanishing Point")
    assert second["maker"]["id"] == 1
    assert len(client.get("/api/v1/lookups").json()["makers"]) == 1


def test_nibs_installations_and_notes(client):
    pen = create_pen(client)
    pen_id = pen["id"]
    added = client.post(
        f"/api/v1/pens/{pen_id}/nibs", json={"description": "Bock", "material": "Steel", "nib_size": "#6", "line_width": "M"}
    )
    assert added.status_code == 201
    nib_id = added.json()["id"]
    edited = client.patch(f"/api/v1/pens/{pen_id}/nibs/{nib_id}", json={"description": "Bock tuned", "material": "Titanium", "nib_size": "#8", "line_width": "F"})
    assert edited.status_code == 200
    assert edited.json()["description"] == "Bock tuned"
    assert edited.json()["material"]["name"] == "Titanium"
    assert edited.json()["nib_size"] == "#8" and edited.json()["line_width"] == "F"
    installed = client.post(
        f"/api/v1/pens/{pen_id}/nibs/{nib_id}/install",
        json={"installed_on": "2025-03-04", "previous_removed_on": "2025-03-03"},
    )
    assert installed.status_code == 201
    assert installed.json()["is_current"] is True
    assert client.post(f"/api/v1/pens/{pen_id}/nibs/{nib_id}/install", json={}).status_code == 409
    assert (
        client.post(f"/api/v1/pens/{pen_id}/nibs/00000000-0000-0000-0000-000000000000/install", json={}).status_code
        == 404
    )

    note = client.post(f"/api/v1/pens/{pen_id}/notes", json={"text": "Tuned", "event_on": "2025-03-04"})
    assert note.status_code == 201
    note_id = note.json()["id"]
    edited_note = client.patch(f"/api/v1/pens/{pen_id}/notes/{note_id}", json={"text": "Tuned twice", "event_on": None})
    assert edited_note.status_code == 200
    assert edited_note.json()["text"] == "Tuned twice" and edited_note.json()["event_on"] is None
    assert client.delete(f"/api/v1/pens/{pen_id}/notes/{note_id}").status_code == 204
    assert client.delete(f"/api/v1/pens/{pen_id}/notes/{note_id}").status_code == 404


def test_image_upload_and_delete(client, png_bytes):
    pen = create_pen(client)
    pen_id = pen["id"]
    upload = client.post(
        f"/api/v1/pens/{pen_id}/images",
        files={"file": ("pen.png", png_bytes, "image/png")},
        data={"caption": "Amber", "sort_order": "2"},
    )
    assert upload.status_code == 201
    image = upload.json()
    assert image["url"].startswith("https://resources.test/pens/")
    assert client.delete(f"/api/v1/pens/{pen_id}/images/{image['id']}").status_code == 204
    assert client.delete(f"/api/v1/pens/{pen_id}/images/{image['id']}").status_code == 404
    bad = client.post(f"/api/v1/pens/{pen_id}/images", files={"file": ("bad.txt", b"no", "text/plain")})
    assert bad.status_code == 422


def test_report_endpoint_and_report_rows(client, session):
    create_pen(client)
    create_pen(client, model="Vanishing Point", purchase_price="150.00")
    with patch.object(
        api,
        "report_rows",
        side_effect=[
            [{"name": "Pilot", "count": 2, "total": 400, "average": 200}],
            [{"name": "14K Gold", "count": 2, "total": 400, "average": 200}],
            [{"quarter": "2024-Q1", "count": 2, "total": 400}],
            [{"id": "x", "acquired_on": date(2024, 2, 3), "price": 250, "maker": "Pilot", "model": "Custom 823"}],
            [{"line_width": "F", "material": "14K Gold", "total": 400}],
        ],
    ):
        response = client.get("/api/v1/reports")
    assert response.status_code == 200
    assert response.json()["summary"]["count"] == 2
    assert response.json()["nib_spend"] == [{"line_width": "F", "material": "14K Gold", "total": 400}]
    rows = api.report_rows(session, "SELECT model FROM pens p WHERE true /*status*/", True)
    assert len(rows) == 2
    rows = api.report_rows(session, "SELECT model FROM pens p WHERE true /*status*/", False)
    assert len(rows) == 2


def test_validation_and_missing_records(client):
    custom = create_pen(client, model="Custom width", original_nib={"description": None, "material": "Steel", "nib_size": "#7", "line_width": "0.7 Stub"})
    assert custom["nibs"][0] | {"description": None, "nib_size": "#7", "line_width": "0.7 Stub"} == custom["nibs"][0]
    invalid = PEN | {"disposed_on": "2020-01-01"}
    assert client.post("/api/v1/pens", json=invalid).status_code == 422
    missing = "00000000-0000-0000-0000-000000000000"
    existing = create_pen(client, model="Endpoint ownership")
    assert client.patch(f"/api/v1/pens/{existing['id']}/nibs/{missing}", json={"line_width": "BB"}).status_code == 404
    assert client.patch(f"/api/v1/pens/{existing['id']}/notes/{missing}", json={"text": "Missing"}).status_code == 404
    assert client.get(f"/api/v1/pens/{missing}").status_code == 404
