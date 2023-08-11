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
            get_shots {
                shots {
                    shot_id
                }
                page_meta {
                    last_cursor
                    total_items
                }
            }
        }
    """
    response = client.post("graphql", json={"query": query})
    assert response.status_code == 200

    data = response.json()
    assert "errors" not in data

    data = data["data"]
    print(data)
    assert "get_shots" in data
    data = data["get_shots"]
    assert len(data["shots"]) == 10
    assert "shot_id" in data["shots"][0]
    assert "page_meta" in data
    assert data["page_meta"]["last_cursor"] is not None
    assert data["page_meta"]["total_items"] == 25556


def test_query_signal_datasets_from_shot(client):
    query = """
        query {
            get_shots (limit: 10) {
                shots {
                    shot_id
                    get_signal_datasets (limit: 10) {
                        signal_datasets {
                            signal_dataset_id
                        }
                    }
                }
            }
        }
    """
    response = client.post("graphql", json={"query": query})
    assert response.status_code == 200

    data = response.json()
    assert "errors" not in data

    data = data["data"]["get_shots"]
    assert "shots" in data
    assert len(data["shots"]) == 10
    assert "shot_id" in data["shots"][0]

    # Check we also got some signal_datasets
    assert "signal_datasets" in data["shots"][0]["get_signal_datasets"]
    signal_datasets = data["shots"][0]["get_signal_datasets"]["signal_datasets"]
    assert len(signal_datasets) == 10
    assert "signal_dataset_id" in signal_datasets[0]


def test_query_signal_datasets(client):
    query = """
        query {
            get_signal_datasets (limit: 10) {
                signal_datasets {
                    signal_dataset_id
                }
            }
        }
    """
    response = client.post("graphql", json={"query": query})
    assert response.status_code == 200

    data = response.json()
    assert "errors" not in data

    data = data["data"]["get_signal_datasets"]
    assert "signal_datasets" in data
    assert len(data["signal_datasets"]) == 10
    assert "signal_dataset_id" in data["signal_datasets"][0]


def test_query_shots_from_signal_datasets(client):
    query = """
        query {
            get_signal_datasets (limit: 10) {
                signal_datasets {
                    signal_dataset_id
                    get_shots (limit: 10) {
                        shots {
                            shot_id
                        }
                    }
                }
            }
        }
    """
    response = client.post("graphql", json={"query": query})
    assert response.status_code == 200

    data = response.json()
    assert "errors" not in data

    data = data["data"]["get_signal_datasets"]
    assert "signal_datasets" in data
    assert len(data["signal_datasets"]) == 10
    assert "signal_dataset_id" in data["signal_datasets"][0]

    # Check we also got some shots
    assert "get_shots" in data["signal_datasets"][0]
    shots = data["signal_datasets"][0]["get_shots"]["shots"]
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
            get_sources {
                sources {
                    description
                }
            }
        }
    """
    response = client.post("graphql", json={"query": query})
    assert response.status_code == 200

    data = response.json()
    assert "errors" not in data

    data = data["data"]["get_sources"]
    assert "sources" in data
    assert len(data["sources"]) == 92
