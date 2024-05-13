import pytest
import pandas as pd
from fastapi.testclient import TestClient
from src.api.main import app, get_db, add_pagination


@pytest.fixture(scope="module")
def client():
    get_db()
    client = TestClient(app, base_url="http://localhost:8081")
    # Need to re-add pagination after creating the client
    add_pagination(app)
    return client


def test_get_shots(client):
    response = client.get("json/shots")
    data = response.json()
    assert response.status_code == 200
    assert len(data['items']) == 50
    assert data['previous_page'] == None


def test_get_shots_filter_shot_id(client):
    response = client.get("json/shots?filters=shot_id$geq:30000")
    data = response.json()
    assert response.status_code == 200
    assert len(data['items']) == 50


def test_get_shot(client):
    response = client.get("json/shots/30420")
    data = response.json()
    assert response.status_code == 200
    assert data["shot_id"] == 30420


def test_get_shot_aggregate(client):
    response = client.get(
        "json/shots/aggregate?data=shot_id$min:,shot_id$max:&groupby=campaign&sort=-min_shot_id"
    )
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 1
    assert data[0]["campaign"] == "M9"


def test_get_signals_aggregate(client):
    response = client.get("json/signals/aggregate?data=shot_id$count:&groupby=quality")
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 1


def test_get_signals_for_shot(client):
    response = client.get("json/shots/30471/signals")
    data = response.json()
    assert response.status_code == 200
    assert len(data['items']) == 50
    assert data['previous_page'] == None


def test_get_signals(client):
    response = client.get("json/signals")
    data = response.json()
    assert response.status_code == 200
    assert "name" in data['items'][0]
    assert "quality" in data['items'][0]
    assert len(data['items']) == 50


def test_get_cpf_summary(client):
    response = client.get("json/cpf_summary")
    data = response.json()
    assert response.status_code == 200
    assert len(data['items']) == 50


def test_get_scenarios(client):
    response = client.get("json/scenarios")
    data = response.json()
    assert response.status_code == 200
    assert len(data['items']) == 34


def test_get_sources(client):
    response = client.get("json/sources")
    data = response.json()
    assert response.status_code == 200
    assert len(data['items']) == 50

def test_get_cursor(client):
    response = client.get("json/signals")
    first_page_data = response.json()
    next_cursor = first_page_data['next_page']
    next_response = client.get(f"json/signals?cursor={next_cursor}")
    next_page_data = next_response.json()
    assert next_page_data['current_page'] == next_cursor

def test_cursor_response(client):
    response = client.get("json/signals")
    data = response.json()
    assert data['previous_page'] == None

def test_stream_response_shots(client):
    df = pd.read_json(str(client.base_url) + '/json/stream/shots', lines=True)
    assert isinstance(df, pd.DataFrame)

def test_stream_response_signals(client):
    df = pd.read_json(str(client.base_url) + '/json/stream/signals?shot_id=30420', lines=True)
    assert isinstance(df, pd.DataFrame)