import io

import pandas as pd


def test_get_cpf(client, override_get_db):
    response = client.get("/json/cpf_summary")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 50
    assert "description" in data["items"][0]


def test_get_shots(client, override_get_db):
    response = client.get("json/level1/shots")
    data = response.json()
    assert response.status_code == 200
    assert len(data["items"]) == 15
    assert data["previous_page"] is None


def test_get_shots_filter_shot_id(client, override_get_db):
    response = client.get("json/level1/shots?filters=shot_id$leq:20000")
    data = response.json()
    assert response.status_code == 200
    assert len(data["items"]) == 15


def test_get_shot(client, override_get_db):
    response = client.get("json/level1/shots/11699")
    data = response.json()
    assert response.status_code == 200
    assert data["shot_id"] == 11699


def test_get_shot_aggregate(client, override_get_db):
    response = client.get(
        "json/level1/shots/aggregate?data=shot_id$min:,shot_id$max:&groupby=campaign&sort=-min_shot_id"
    )
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 1
    assert data[0]["campaign"] == "M5"


def test_get_signals_aggregate(client, override_get_db):
    response = client.get("json/level1/signals/aggregate?data=shot_id$count:&groupby=source")
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 4


def test_get_signals_for_shot(client, override_get_db):
    response = client.get("json/level1/shots/11695/signals")
    data = response.json()
    assert response.status_code == 200
    assert len(data["items"]) == 50
    assert data["previous_page"] is None


def test_get_signals(client, override_get_db):
    response = client.get("json/level1/signals")
    data = response.json()
    assert response.status_code == 200
    assert "name" in data["items"][0]
    assert "quality" in data["items"][0]
    assert len(data["items"]) == 50


def test_get_cpf_summary(client, override_get_db):
    response = client.get("json/cpf_summary")
    data = response.json()
    assert response.status_code == 200
    assert len(data["items"]) == 50


def test_get_scenarios(client, override_get_db):
    response = client.get("json/scenarios")
    data = response.json()
    assert response.status_code == 200
    assert len(data["items"]) == 34


def test_get_sources(client, override_get_db):
    response = client.get("json/level1/sources")
    data = response.json()
    assert response.status_code == 200
    assert len(data["items"]) == 50


def test_get_cursor(client, override_get_db):
    response = client.get("json/level1/signals")
    first_page_data = response.json()
    next_cursor = first_page_data["next_page"]
    next_response = client.get(f"json/level1/signals?cursor={next_cursor}")
    next_page_data = next_response.json()
    assert next_page_data["current_page"] == next_cursor


def test_cursor_response(client, override_get_db):
    response = client.get("json/level1/signals")
    data = response.json()
    assert data["previous_page"] is None


def test_get_ndjson_response_shots(client, override_get_db):
    response = client.get("ndjson/shots")
    text = io.StringIO(response.text)
    df = pd.read_json(text, lines=True)
    assert isinstance(df, pd.DataFrame)


def test_get_ndjson_response_sources(client, override_get_db):
    response = client.get("ndjson/sources")
    text = io.StringIO(response.text)
    df = pd.read_json(text, lines=True)
    assert isinstance(df, pd.DataFrame)


def test_get_ndjson_response_signals(client, override_get_db):
    response = client.get("ndjson/signals?shot_id=30420")
    text = io.StringIO(response.text)
    df = pd.read_json(text, lines=True)
    assert isinstance(df, pd.DataFrame)


def test_get_parquet_response_shots(client, override_get_db):
    response = client.get("parquet/level1/shots")
    content = response.read()
    buffer = io.BytesIO(content)
    df = pd.read_parquet(buffer)
    assert isinstance(df, pd.DataFrame)


def test_get_parquet_response_signals(client, override_get_db):
    response = client.get("parquet/level1/signals?shot_id=30420")
    buffer = io.BytesIO(response.read())
    df = pd.read_parquet(buffer)
    assert isinstance(df, pd.DataFrame)


def test_get_parquet_response_sources(client, override_get_db):
    response = client.get("parquet/level1/sources")
    buffer = io.BytesIO(response.read())
    df = pd.read_parquet(buffer)
    assert isinstance(df, pd.DataFrame)


# def test_get_ndjson_response_signals(client, override_get_db):
#     response = client.get("ndjson/signals?shot_id=30420")
#     text = io.StringIO(response.text)
#     df = pd.read_json(text, lines=True)
#     assert isinstance(df, pd.DataFrame)


def test_exception_handler(client, override_get_db):
    response = client.get("/json/level1/shots/filters=shot_id$geq:30000")
    data = response.json()
    assert data["message"] == [
        "Unprocessable entity. Please check your query and/or filter."
    ]
