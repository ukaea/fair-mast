import pytest
from fastapi.testclient import TestClient
from src.api.main import app, get_db, add_pagination


@pytest.fixture(scope="module")
def client():
    get_db()
    client = TestClient(app)
    # Need to re-add pagination after creating the client
    add_pagination(app)
    return client


def test_query_shots(client):
    query = """
        query {
            shots (limit: 10) {
                shot_id
            }
        }
    """
    response = client.post("graphql", json={"query": query})
    assert response.status_code == 200

    data = response.json()
    assert "errors" not in data

    data = data["data"]
    assert "shots" in data
    assert len(data["shots"]) == 10
    assert "shot_id" in data["shots"][0]


def test_query_signals_from_shot(client):
    query = """
        query {
            shots (limit: 10) {
                shot_id
                signals (limit: 10) {
                    signal_id
                }
            }
        }
    """
    response = client.post("graphql", json={"query": query})
    assert response.status_code == 200

    data = response.json()
    assert "errors" not in data

    data = data["data"]
    assert "shots" in data
    assert len(data["shots"]) == 10
    assert "shot_id" in data["shots"][0]

    # Check we also got some signals
    assert "signals" in data["shots"][0]
    signals = data["shots"][0]["signals"]
    assert len(signals) == 10
    assert "signal_id" in signals[0]


def test_query_signals(client):
    query = """
        query {
            signals (limit: 10) {
                signal_id
            }
        }
    """
    response = client.post("graphql", json={"query": query})
    assert response.status_code == 200

    data = response.json()
    assert "errors" not in data

    data = data["data"]
    assert "signals" in data
    assert len(data["signals"]) == 10
    assert "signal_id" in data["signals"][0]


def test_query_shots_from_signals(client):
    query = """
        query {
            signals (limit: 10) {
                signal_id
                shots (limit: 10) {
                    shot_id
                }
            }
        }
    """
    response = client.post("graphql", json={"query": query})
    assert response.status_code == 200

    data = response.json()
    assert "errors" not in data

    data = data["data"]
    assert "signals" in data
    assert len(data["signals"]) == 10
    assert "signal_id" in data["signals"][0]

    # Check we also got some shots
    assert "shots" in data["signals"][0]
    shots = data["signals"][0]["shots"]
    assert len(shots) == 10
    assert "shot_id" in shots[0]


def test_query_cpf_summary(client):
    query = """
        query {
            cpf_summary {
                description
            }
        }
    """
    response = client.post("graphql", json={"query": query})
    assert response.status_code == 200

    data = response.json()
    assert "errors" not in data

    data = data["data"]
    assert "cpf_summary" in data
    assert len(data["cpf_summary"]) == 265


def test_query_scenarios(client):
    query = """
        query {
            scenarios {
                name
            }
        }
    """
    response = client.post("graphql", json={"query": query})
    assert response.status_code == 200

    data = response.json()
    assert "errors" not in data

    data = data["data"]
    assert "scenarios" in data
    assert len(data["scenarios"]) == 34


def test_query_sources(client):
    query = """
        query {
            sources {
                name
            }
        }
    """
    response = client.post("graphql", json={"query": query})
    assert response.status_code == 200

    data = response.json()
    assert "errors" not in data

    data = data["data"]
    assert "sources" in data
    assert len(data["sources"]) == 92
