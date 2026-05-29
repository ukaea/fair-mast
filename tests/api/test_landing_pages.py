"""Integration tests for the per-shot dataset landing-page routes.

Uses the existing TestClient + override_get_db fixtures from conftest.py,
which spins up a test postgres and ingests the mock data. Hits shot IDs
that the JSON tests confirm exist in the mock set (e.g. 11699).
"""

import json
import re

import pytest

# override_get_db patches app.dependency_overrides as a side effect; it's
# applied to every test here rather than passed as an (unused) argument.
pytestmark = pytest.mark.usefixtures("override_get_db")

KNOWN_SHOT_ID = 11699  # exists in mock_data per tests/api/test_json.py
MISSING_SHOT_ID = 99999999


def _extract_jsonld(html: str) -> dict:
    m = re.search(
        r'<script type="application/ld\+json">\s*(.*?)\s*</script>',
        html,
        re.DOTALL,
    )
    assert m, "no JSON-LD <script> block found in HTML"
    return json.loads(m.group(1))


# --- Level 1 HTML ---------------------------------------------------------


def test_level1_landing_returns_html(client):
    response = client.get(f"/dataset/level1/shot/{KNOWN_SHOT_ID}")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")


def test_level1_landing_has_embedded_schema_org_jsonld(client):
    response = client.get(f"/dataset/level1/shot/{KNOWN_SHOT_ID}")
    doc = _extract_jsonld(response.text)
    assert doc["@context"] == "https://schema.org"
    assert doc["@type"] == "Dataset"
    assert "Level 1" in doc["name"]
    assert doc["license"] == "https://creativecommons.org/licenses/by/4.0/"


def test_level1_landing_has_canonical_and_alternate_links(client):
    response = client.get(f"/dataset/level1/shot/{KNOWN_SHOT_ID}")
    assert 'rel="canonical"' in response.text
    assert 'rel="alternate"' in response.text
    assert f"/dataset/level1/shot/{KNOWN_SHOT_ID}.jsonld" in response.text


def test_level1_landing_404_for_missing_shot(client):
    response = client.get(f"/dataset/level1/shot/{MISSING_SHOT_ID}")
    assert response.status_code == 404


# --- Level 1 DCAT JSON-LD -------------------------------------------------


def test_level1_dcat_endpoint_returns_jsonld(client):
    response = client.get(f"/dataset/level1/shot/{KNOWN_SHOT_ID}.jsonld")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/ld+json")
    doc = response.json()
    assert doc["@type"] == "dcat:Dataset"
    assert "Level 1" in doc["dct:title"]
    assert doc["dct:license"]["@id"] == "https://creativecommons.org/licenses/by/4.0/"


def test_level1_dcat_404_for_missing_shot(client):
    response = client.get(f"/dataset/level1/shot/{MISSING_SHOT_ID}.jsonld")
    assert response.status_code == 404


# --- Level 2 (routes exist regardless of mock data availability) ----------


def test_level2_landing_route_exists(client):
    """The route handler is registered; a missing shot returns 404 (not
    a routing 404). If level2 mock data exists, returns 200.
    """
    response = client.get(f"/dataset/level2/shot/{MISSING_SHOT_ID}")
    assert response.status_code == 404
    detail = response.json()["detail"]
    assert "Level 2" in detail


def test_level2_dcat_route_exists(client):
    response = client.get(f"/dataset/level2/shot/{MISSING_SHOT_ID}.jsonld")
    assert response.status_code == 404


