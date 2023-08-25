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
    assert "column_metadata" in data
    assert "items" in data
    assert len(data["items"]) == 50


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


def test_file_api(client):
    response = client.get("files/shots")
    assert response.status_code == 200
    response = client.get("files/signals")
    assert response.status_code == 200
    response = client.get("files/signal_datasets")
    assert response.status_code == 200
    response = client.get("files/sources")
    assert response.status_code == 200
    response = client.get("files/cpf_summary")
    assert response.status_code == 200
    response = client.get("files/scenarios")
    assert response.status_code == 200

    response = client.get("files/shots?format=csv")
    assert response.status_code == 200
    response = client.get("files/signals?format=csv")
    assert response.status_code == 200
    response = client.get("files/signal_datasets?format=csv")
    assert response.status_code == 200
    response = client.get("files/sources?format=csv")
    assert response.status_code == 200
    response = client.get("files/cpf_summary?format=csv")
    assert response.status_code == 200
    response = client.get("files/scenarios?format=csv")
    assert response.status_code == 200
