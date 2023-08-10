import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
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
