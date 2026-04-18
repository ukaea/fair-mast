def test_get_l2_shots(client, override_get_db):
    response = client.get("json/level2/shots")
    data = response.json()
    assert response.status_code == 200
    assert len(data["items"]) == 13
    assert data["previous_page"] is None


def test_get_l2_shots_filter_shot_id(client, override_get_db):
    response = client.get("json/level2/shots?filters=shot_id$leq:20000")
    data = response.json()
    assert response.status_code == 200
    assert len(data["items"]) == 13


def test_get_l2_shot(client, override_get_db):
    response = client.get("json/level2/shots/11766")
    data = response.json()
    assert response.status_code == 200
    assert data["shot_id"] == 11766


def test_get_l2_shot_aggregate(client, override_get_db):
    response = client.get(
        "json/level2/shots/aggregate?data=shot_id$min:,shot_id$max:&groupby=campaign&sort=-min_shot_id"
    )
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 1
    assert data[0]["campaign"] == "M5"


def test_get_l2_signals_aggregate(client, override_get_db):
    response = client.get("json/level2/signals/aggregate?data=shot_id$count:&groupby=source")
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 7


def test_get_l2_signals_for_shot(client, override_get_db):
    response = client.get("json/level2/shots/11766/signals")
    data = response.json()
    assert response.status_code == 200
    assert len(data["items"]) == 50
    assert data["previous_page"] is None


def test_get_l2_signals(client, override_get_db):
    response = client.get("json/level2/signals")
    data = response.json()
    assert response.status_code == 200
    assert "name" in data["items"][0]
    assert "quality" in data["items"][0]
    assert len(data["items"]) == 50


def test_get_l2_sources(client, override_get_db):
    response = client.get("json/level2/sources")
    data = response.json()
    assert response.status_code == 200
    assert len(data["items"]) == 50

