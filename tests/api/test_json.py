import io

import pandas as pd
import pytest
from keycloak.exceptions import KeycloakAuthorizationConfigError
from requests.auth import HTTPBasicAuth

from src.api.environment import TEST_PASSWORD, TEST_USERNAME, UNAUTHORIZED_USER


def test_get_cpf(client, override_get_db):
    response = client.get("/json/cpf_summary")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 50
    assert "description" in data["items"][0]


def test_get_shots(client, override_get_db):
    response = client.get("json/shots")
    data = response.json()
    assert response.status_code == 200
    assert len(data["items"]) == 50
    assert data["previous_page"] is None


def test_get_shots_filter_shot_id(client, override_get_db):
    response = client.get("json/shots?filters=shot_id$geq:30000")
    data = response.json()
    assert response.status_code == 200
    assert len(data["items"]) == 50


def test_get_shot(client, override_get_db):
    response = client.get("json/shots/30420")
    data = response.json()
    assert response.status_code == 200
    assert data["shot_id"] == 30420


def test_get_shot_aggregate(client, override_get_db):
    response = client.get(
        "json/shots/aggregate?data=shot_id$min:,shot_id$max:&groupby=campaign&sort=-min_shot_id"
    )
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 1
    assert data[0]["campaign"] == "M9"


def test_get_signals_aggregate(client, override_get_db):
    response = client.get("json/signals/aggregate?data=shot_id$count:&groupby=quality")
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 2


def test_get_signals_for_shot(client, override_get_db):
    response = client.get("json/shots/30471/signals")
    data = response.json()
    assert response.status_code == 200
    assert len(data["items"]) == 50
    assert data["previous_page"] is None


def test_get_signals(client, override_get_db):
    response = client.get("json/signals")
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
    response = client.get("json/sources")
    data = response.json()
    assert response.status_code == 200
    assert len(data["items"]) == 50


def test_get_cursor(client, override_get_db):
    response = client.get("json/signals")
    first_page_data = response.json()
    next_cursor = first_page_data["next_page"]
    next_response = client.get(f"json/signals?cursor={next_cursor}")
    next_page_data = next_response.json()
    assert next_page_data["current_page"] == next_cursor


def test_cursor_response(client, override_get_db):
    response = client.get("json/signals")
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
    response = client.get("parquet/shots")
    content = response.read()
    buffer = io.BytesIO(content)
    df = pd.read_parquet(buffer)
    assert isinstance(df, pd.DataFrame)


def test_get_parquet_response_signals(client, override_get_db):
    response = client.get("parquet/signals?shot_id=30420")
    buffer = io.BytesIO(response.read())
    df = pd.read_parquet(buffer)
    assert isinstance(df, pd.DataFrame)


def test_get_parquet_response_sources(client, override_get_db):
    response = client.get("parquet/sources")
    buffer = io.BytesIO(response.read())
    df = pd.read_parquet(buffer)
    assert isinstance(df, pd.DataFrame)


def test_exception_handler(client, override_get_db):
    response = client.get("/json/shots/filters=shot_id$geq:30000")
    data = response.json()
    assert data["message"] == [
        "Unprocessable entity. Please check your query and/or filter."
    ]


def test_post_shots(client):
    endpoint = "http://localhost:8081/json/shots"

    payload = {
        "shot_id": 90121,
        "uuid": "883382e6-df26-55f2-af85-ad7bdec24835",
        "url": "s3://mast/level1/shots/30122.zarr",
        "timestamp": "2013-09-09T14:24:00",
        "preshot_description": "extend CHFS to 500 ms - increase zref to +0.75 - ramp current from set value of 0.5 at 220ms to a set value of 0.75 at 310ms",
        "postshot_description": "1 breakdown on SS at 100 ms - good deep H-mode - disrupts during the current ramp - but still in H-mode",
        "campaign": "M9",
        "reference_shot": 29495,
        "scenario": 3,
        "heating": "2 Beams,SS Beam,SW Beam",
        "pellets": "false",
        "rmp_coil": "false",
        "current_range": "700 kA",
        "divertor_config": "Conventional",
        "plasma_shape": "Connected Double Null",
        "comissioner": "null",
        "facility": "MAST",
    }

    response = client.post(
        endpoint,
        auth=HTTPBasicAuth(username=TEST_USERNAME, password=TEST_PASSWORD),
        json=payload,
    )
    assert response.status_code == 200


def test_post_signals(client, override_get_db):
    endpoint = "/json/signals"

    payload = {
        "uuid": "005fe9da-964a-5563-af2c-dffe3d99ed89",
        "shot_id": 90121,
        "name": "alp/inner_lo_powpeakval",
        "version": 0,
        "rank": 1,
        "url": "s3://mast/level1/shots/30398.zarr/alp/inner_lo_powpeakval",
        "source": "alp",
        "quality": "Not Checked",
        "shape": [288],
        "provenance": "null",
        "units": "null",
        "description": "",
        "signal_type": "Analysed",
        "dimensions": ["time"],
    }

    response = client.post(
        endpoint,
        auth=HTTPBasicAuth(username=TEST_USERNAME, password=TEST_PASSWORD),
        json=payload,
    )
    assert response.status_code == 200


def test_post_sources(client, override_get_db):
    endpoint = "/json/sources"

    payload = {
        "uuid": "a2ecc848-21bf-5137-bd8c-bfcf06020cc9",
        "shot_id": 90121,
        "name": "abm",
        "url": "s3://mast/level1/shots/30119.zarr/abm",
        "description": "multi-chord bolometers",
        "quality": "Not Checked",
    }

    response = client.post(
        endpoint,
        auth=HTTPBasicAuth(username=TEST_USERNAME, password=TEST_PASSWORD),
        json=payload,
    )
    assert response.status_code == 200


def test_post_scenarios(client, override_get_db):
    endpoint = "/json/scenarios"

    payload = {"id": 80, "name": "S1"}

    response = client.post(
        endpoint,
        auth=HTTPBasicAuth(username=TEST_USERNAME, password=TEST_PASSWORD),
        json=payload,
    )
    assert response.status_code == 200


def test_post_cpf_summary(client, override_get_db):
    endpoint = "/json/cpf_summary"

    payload = {"index": 0, "name": "P12450", "description": "CP3c Set Volts"}

    response = client.post(
        endpoint,
        auth=HTTPBasicAuth(username=TEST_USERNAME, password=TEST_PASSWORD),
        json=payload,
    )
    assert response.status_code == 200


def test_unauthorized_post_scenarios(client, override_get_db):
    with pytest.raises(KeycloakAuthorizationConfigError):
        endpoint = "/json/scenarios"

        payload = {"id": 85, "name": "S1"}

        client.post(
            endpoint,
            auth=HTTPBasicAuth(username=UNAUTHORIZED_USER, password=TEST_PASSWORD),
            json=payload,
        )
