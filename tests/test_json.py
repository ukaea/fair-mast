import pytest
import pandas as pd
from fastapi.testclient import TestClient
from src.api.main import app, get_db, add_pagination


@pytest.fixture(scope="module")
def client():
    get_db()
    client = TestClient(app)
    # Need to re-add pagination after creating the client
    add_pagination(app)
    return client


def test_get_shots(client):
    response = client.get("json/shots")
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 50
    assert response.headers["x-total-pages"] == "512"


def test_get_shot(client):
    response = client.get("json/shots/30420")
    data = response.json()
    assert response.status_code == 200
    assert data["shot_id"] == 30420


def test_get_shot_aggregate(client):
    response = client.get(
        "json/shots/aggregate?data=shot_id$min,shot_id$max&groupby=campaign&sort=-min_shot_id"
    )
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 8
    assert data[0]["campaign"] == "MU3"


def test_get_signal_datasets_aggregate(client):
    response = client.get(
        "json/signal_datasets/aggregate?data=name$count&groupby=quality"
    )
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 1


def test_get_signals_aggregate(client):
    response = client.get("json/signals/aggregate?data=shot_id$count&groupby=quality")
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 1


def test_get_signals_for_shot(client):
    response = client.get("json/shots/30420/signals")
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 50
    assert response.headers["x-total-count"] == "512"


def test_get_signal_datasets_for_shot(client):
    assert False


def test_get_signals(client):
    response = client.get("json/signals")
    data = response.json()
    assert response.status_code == 200
    assert "column_metadata" in data
    assert "items" in data
    assert len(data["items"]) == 50


def test_get_signal_datasets(client):
    response = client.get("json/signal_datasets")
    data = response.json()
    assert response.status_code == 200
    assert "column_metadata" in data
    assert "items" in data
    assert len(data["items"]) == 50


def test_get_cpf_summary(client):
    response = client.get("json/cpf_summary")
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 265


def test_get_scenarios(client):
    response = client.get("json/scenarios")
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 34


def test_get_sources(client):
    response = client.get("json/sources")
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 92
