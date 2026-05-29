"""Unit tests for src/api/jsonld_dcat.py — no DB needed.

Synthetic shot/source factories and the `shot` / `sources` fixtures live in
tests/api/conftest.py.
"""

import pytest

from src.api import dataset_metadata
from src.api.jsonld_dcat import build_shot_dataset_dcat
from src.api.models import Level2ShotModel

from .conftest import make_shot

SITE = "https://mastapp.site"


def test_basic_shape(shot, sources):
    doc = build_shot_dataset_dcat(shot, sources, SITE)
    assert doc["@type"] == "dcat:Dataset"
    assert doc["@id"] == "https://mastapp.site/dataset/level1/shot/30420"


def test_context_has_required_prefixes(shot, sources):
    doc = build_shot_dataset_dcat(shot, sources, SITE)
    ctx = doc["@context"]
    for prefix in ("dcat", "dct", "foaf", "schema", "xsd", "owl"):
        assert prefix in ctx, f"missing prefix: {prefix}"


def test_dcat_dataset_required_fields(shot, sources):
    doc = build_shot_dataset_dcat(shot, sources, SITE)
    for field in (
        "dct:title",
        "dct:description",
        "dct:identifier",
        "dct:license",
        "dct:publisher",
        "dcat:distribution",
        "dct:isPartOf",
    ):
        assert field in doc, f"missing required field: {field}"


def test_license_is_cc_by_4(shot, sources):
    doc = build_shot_dataset_dcat(shot, sources, SITE)
    assert doc["dct:license"]["@id"] == "https://creativecommons.org/licenses/by/4.0/"


def test_distributions_use_https_not_s3(shot, sources):
    doc = build_shot_dataset_dcat(shot, sources, SITE)
    for dist in doc["dcat:distribution"]:
        url = dist["dcat:accessURL"]["@id"]
        assert not url.startswith("s3://"), f"accessURL should be HTTPS, got {url}"


def test_temporal_is_period_of_time(shot, sources):
    doc = build_shot_dataset_dcat(shot, sources, SITE)
    temporal = doc["dct:temporal"]
    assert temporal["@type"] == "dct:PeriodOfTime"
    assert temporal["dcat:startDate"]["@type"] == "xsd:dateTime"
    assert temporal["dcat:endDate"]["@type"] == "xsd:dateTime"


def test_has_part_uses_source_name_not_boilerplate_title(shot, sources):
    doc = build_shot_dataset_dcat(shot, sources, SITE)
    titles = [p["dct:title"] for p in doc["dct:hasPart"]]
    assert "Source Dataset" not in titles
    assert titles == ["AMC", "AYC"]


def test_level_appears_in_title(shot, sources):
    doc_l1 = build_shot_dataset_dcat(shot, sources, SITE, level=1)
    doc_l2 = build_shot_dataset_dcat(make_shot(Level2ShotModel), sources, SITE, level=2)
    assert "(Level 1)" in doc_l1["dct:title"]
    assert "(Level 2)" in doc_l2["dct:title"]


def test_no_cross_link_when_related_url_omitted(shot, sources):
    doc = build_shot_dataset_dcat(shot, sources, SITE)
    assert "dct:source" not in doc
    assert "dct:hasVersion" not in doc


def test_level1_with_related_level_emits_has_version(shot, sources):
    related = dataset_metadata.shot_page_url(SITE, 30420, level=2)
    doc = build_shot_dataset_dcat(
        shot, sources, SITE, level=1, related_level_url=related
    )
    assert doc["dct:hasVersion"]["@id"] == related
    assert "dct:source" not in doc


def test_level2_with_related_level_emits_dct_source():
    shot = make_shot(Level2ShotModel)
    related = dataset_metadata.shot_page_url(SITE, 30420, level=1)
    doc = build_shot_dataset_dcat(
        shot, [], SITE, level=2, related_level_url=related
    )
    assert doc["dct:source"]["@id"] == related
    assert "dct:hasVersion" not in doc


def test_url_differs_per_level(shot):
    doc_l1 = build_shot_dataset_dcat(shot, [], SITE, level=1)
    doc_l2 = build_shot_dataset_dcat(make_shot(Level2ShotModel), [], SITE, level=2)
    assert doc_l1["@id"] == "https://mastapp.site/dataset/level1/shot/30420"
    assert doc_l2["@id"] == "https://mastapp.site/dataset/level2/shot/30420"


def test_jsonld_parses_with_rdflib(shot, sources):
    """Sanity check: the DCAT graph round-trips through an RDF parser.

    rdflib isn't a test dep — skip when it's not installed rather than
    forcing it. Useful to run locally if you've installed it.
    """
    rdflib = pytest.importorskip("rdflib")
    import json

    doc = build_shot_dataset_dcat(shot, sources, SITE)
    g = rdflib.Graph()
    g.parse(data=json.dumps(doc), format="json-ld")
    assert len(g) > 0
