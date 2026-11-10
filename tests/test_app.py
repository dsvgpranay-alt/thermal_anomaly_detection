
import pytest
from app import app, db
from model import Alert


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"

    with app.app_context():
        db.drop_all()
        db.create_all()

        yield app.test_client()

        db.session.remove()
        db.drop_all()


def create_asset(client):
    data = {
        "asset_id": 1,
        "name": "Boiler",
        "type": "Industrial",
        "location": "Chennai",
        "warning_limit_C": 70,
        "critical_limit_C": 90
    }

    return client.post("/assets", json=data)


def test_create_asset(client):
    response = create_asset(client)
    assert response.status_code == 201


def test_warning_alert(client):
    create_asset(client)

    data = {
        "asset_id": 1,
        "timestamp": "2026-11-10T10:00:00",
        "max_temp_C": 75,
        "mean_temp_C": 65,
        "idempotency_key": "warning-test-001"
    }

    response = client.post("/inspections", json=data)

    assert response.status_code == 201
    assert response.json["alert"]["severity"] == "warning"
    assert response.json["alert"]["status"] == "open"


def test_critical_alert(client):
    create_asset(client)

    data = {
        "asset_id": 1,
        "timestamp": "2026-11-10T10:05:00",
        "max_temp_C": 95,
        "mean_temp_C": 80,
        "idempotency_key": "critical-test-001"
    }

    response = client.post("/inspections", json=data)

    assert response.status_code == 201
    assert response.json["alert"]["severity"] == "critical"
    assert response.json["alert"]["status"] == "open"


def test_no_alert_below_warning(client):
    create_asset(client)

    data = {
        "asset_id": 1,
        "timestamp": "2026-11-10T10:10:00",
        "max_temp_C": 60,
        "mean_temp_C": 50,
        "idempotency_key": "normal-test-001"
    }

    response = client.post("/inspections", json=data)

    assert response.status_code == 201
    assert response.json["alert"] is None


def test_unknown_asset(client):
    data = {
        "asset_id": 99,
        "timestamp": "2026-11-10T10:15:00",
        "max_temp_C": 95,
        "mean_temp_C": 80,
        "idempotency_key": "unknown-asset-test-001"
    }

    response = client.post("/inspections", json=data)

    assert response.status_code == 404


def test_acknowledge_alert(client):
    create_asset(client)

    data = {
        "asset_id": 1,
        "timestamp": "2026-11-10T10:20:00",
        "max_temp_C": 95,
        "mean_temp_C": 80,
        "idempotency_key": "acknowledge-test-001"
    }

    client.post("/inspections", json=data)

    alert = Alert.query.first()

    response = client.patch(
        f"/alerts/{alert.id}/acknowledge",
        json={"acknowledged_by": "Pranay"}
    )

    assert response.status_code == 200
    assert response.json["new_status"] == "acknowledged"
