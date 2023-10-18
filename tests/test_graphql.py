import pytest
from string import Template
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
            all_shots (limit: 10) {
                shots {
                    shot_id
                }
                page_meta {
                    next_cursor
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
    assert "all_shots" in data
    data = data["all_shots"]
    assert len(data["shots"]) == 10
    assert "shot_id" in data["shots"][0]
    assert "page_meta" in data
    assert data["page_meta"]["next_cursor"] is not None
    assert data["page_meta"]["total_items"] == 25556


def test_query_shots_pagination(client):
    def do_query(cursor: str = None):
        query = """
        query {
            all_signal_datasets (limit: 3, where: {name: {contains: "AMC"}}, ${cursor}) {
                signal_datasets {
                    name
                    dimensions
                }
                page_meta {
                    next_cursor
                    total_items
                    total_pages
                }
            }
        }
        """
        template = Template(query)
        query = template.substitute(
            cursor=f'cursor: "{cursor}"' if cursor is not None else ""
        )
        return client.post("graphql", json={"query": query})

    def iterate_responses():
        cursor = None
        while True:
            response = do_query(cursor)
            payload = response.json()
            yield payload
            cursor = payload["data"]["all_signal_datasets"]["page_meta"]["next_cursor"]
            if cursor is None:
                return

    responses = list(iterate_responses())
    assert len(responses) == 16


def test_query_signal_datasets_from_shot(client):
    query = """
        query {
            all_shots (limit: 10, where: {shot_id: {gt: 28648}}) {
                shots {
                    shot_id
                    signal_datasets (limit: 10) {
                        name
                    }
                }
            }
        }
    """
    response = client.post("graphql", json={"query": query})
    assert response.status_code == 200

    data = response.json()
    assert "errors" not in data

    data = data["data"]["all_shots"]
    assert "shots" in data
    assert len(data["shots"]) == 10
    assert "shot_id" in data["shots"][0]

    # Check we also got some signal_datasets
    assert "signal_datasets" in data["shots"][0]
    signal_datasets = data["shots"][0]["signal_datasets"]
    assert len(signal_datasets) == 10
    assert "name" in signal_datasets[0]


def test_query_signal_datasets(client):
    query = """
        query {
            all_signal_datasets (limit: 10) {
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

    data = data["data"]["all_signal_datasets"]
    assert "signal_datasets" in data
    assert len(data["signal_datasets"]) == 10
    assert "signal_dataset_id" in data["signal_datasets"][0]


def test_query_shots_from_signal_datasets(client):
    query = """
        query {
            all_signal_datasets (limit: 10) {
                signal_datasets {
                    signal_dataset_id
                    shots (limit: 10) {
                        shot_id
                    }
                }
            }
        }
    """
    response = client.post("graphql", json={"query": query})
    assert response.status_code == 200

    data = response.json()
    assert "errors" not in data

    data = data["data"]["all_signal_datasets"]
    assert "signal_datasets" in data
    assert len(data["signal_datasets"]) == 10
    assert "signal_dataset_id" in data["signal_datasets"][0]

    # Check we also got some shots
    shots = data["signal_datasets"][0]["shots"]
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
            all_sources {
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

    data = data["data"]["all_sources"]
    assert "sources" in data
    assert len(data["sources"]) == 92


def test_query_signals(client):
    query = """
        query {
            all_signals (limit: 10) {
                signals {
                    shot_id
                    shape
                }
            }
        }
    """
    response = client.post("graphql", json={"query": query})
    assert response.status_code == 200

    data = response.json()
    assert "errors" not in data

    data = data["data"]["all_signals"]
    assert "signals" in data
    assert len(data["signals"]) == 10


def test_query_signals_from_shot(client):
    query = """
        query {
            all_shots (limit: 10, where: {campaign: {eq: "M9"} }) {
                shots  {
                    shot_id
                    signals (limit: 10){
                        shape
                    }
                }
            }
        }
    """
    response = client.post("graphql", json={"query": query})
    assert response.status_code == 200

    data = response.json()
    assert "errors" not in data

    data = data["data"]["all_shots"]["shots"][0]
    assert "signals" in data
    assert len(data["signals"]) == 10


def test_benchmark_signal_datasets_for_shots(client, benchmark):
    def _do_query():
        query = """
            query {
                all_shots (limit: 100) {
                    shots  {
                        shot_id
                        signal_datasets (limit: 100) {
                            signal_dataset_id
                            name
                        }
                    }
                }
            }
        """
        response = client.post("graphql", json={"query": query})
        data = response.json()
        return data

    data = benchmark.pedantic(_do_query, rounds=1, iterations=5)
    assert "error" not in data


def test_benchmark_signals_for_shots(client, benchmark):
    def _do_query():
        query = """
            query {
                all_shots (limit: 100, where: {campaign: {eq: "M9"} }) {
                    shots  {
                        shot_id
                        signals (limit: 100) {
                            name
                        }   
                    }
                }
            }
        """
        response = client.post("graphql", json={"query": query})
        data = response.json()
        assert "error" not in data

    benchmark.pedantic(_do_query, rounds=1, iterations=5)


def test_benchmark_shots_for_signals(client, benchmark):
    def _do_query():
        query = """
            query {
                all_signals (limit: 1000) {
                    signals  {
                        name
                        shot {
                            shot_id
                            divertor_config
                        }
                    }
                }
            }
        """
        response = client.post("graphql", json={"query": query})
        data = response.json()
        return data

    data = benchmark.pedantic(_do_query, rounds=1, iterations=5)
    assert "error" not in data


def test_benchmark_signal_datasets_for_signals(client, benchmark):
    def _do_query():
        query = """
            query {
                all_signals (limit: 1000) {
                    signals  {
                        name
                        signal_dataset {
                            signal_dataset_id
                            name
                        }
                    }
                }
            }
        """
        response = client.post("graphql", json={"query": query})
        data = response.json()
        return data

    data = benchmark.pedantic(_do_query, rounds=1, iterations=5)
    assert "error" not in data


def test_benchmark_shots_for_signal_datasets(client, benchmark):
    def _do_query():
        query = """
            query {
                all_signal_datasets (limit: 100) {
                    signal_datasets  {
                        signal_dataset_id
                        shots (limit: 100) {
                            shot_id
                            divertor_config
                        }
                    }
                }
            }
        """
        response = client.post("graphql", json={"query": query})
        data = response.json()
        return data

    data = benchmark.pedantic(_do_query, rounds=1, iterations=5)
    assert "error" not in data
