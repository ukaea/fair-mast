# ========= Tests ==========

def test_get_cpf(client, override_get_db):
    response = client.get("/json/cpf_summary")
    assert response.status_code == 200
    data = response.json()
    assert len(data['items']) == 50
    assert "description" in data['items'][0]

def test_get_shots(client, override_get_db):
    response = client.get("json/shots")
    data = response.json()
    assert response.status_code == 200
    assert len(data['items']) == 50
    assert data['previous_page'] is None


def test_get_shots_filter_shot_id(client, override_get_db):
    response = client.get("json/shots?filters=shot_id$geq:30000")
    data = response.json()
    assert response.status_code == 200
    assert len(data['items']) == 50


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
    assert len(data) == 1

def test_get_signals_for_shot(client, override_get_db):
    response = client.get("json/shots/30471/signals")
    data = response.json()
    assert response.status_code == 200
    assert len(data['items']) == 50
    assert data['previous_page'] is None


def test_get_signals(client, override_get_db):
    response = client.get("json/signals")
    data = response.json()
    assert response.status_code == 200
    assert "name" in data['items'][0]
    assert "quality" in data['items'][0]
    assert len(data['items']) == 50


def test_get_cpf_summary(client, override_get_db):
    response = client.get("json/cpf_summary")
    data = response.json()
    assert response.status_code == 200
    assert len(data['items']) == 50


def test_get_scenarios(client, override_get_db):
    response = client.get("json/scenarios")
    data = response.json()
    assert response.status_code == 200
    assert len(data['items']) == 34


def test_get_sources(client, override_get_db):
    response = client.get("json/sources")
    data = response.json()
    assert response.status_code == 200
    assert len(data['items']) == 50

def test_get_cursor(client, override_get_db):
    response = client.get("json/signals")
    first_page_data = response.json()
    next_cursor = first_page_data['next_page']
    next_response = client.get(f"json/signals?cursor={next_cursor}")
    next_page_data = next_response.json()
    assert next_page_data['current_page'] == next_cursor

def test_cursor_response(client, override_get_db):
    response = client.get("json/signals")
    data = response.json()
    assert data['previous_page'] is None

def test_http_exception(client, override_get_db):
    response = client.get('/json/shots/filters=shot_id$geq:30000')
    data = response.json()
    assert data['Message'] == ["Unprocessable entity. Please check your query and/or filter."]