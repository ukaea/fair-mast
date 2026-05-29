"""Unit tests for src/api/jsonld_schemaorg.py — no DB needed.

Synthetic shot/source factories and the `shot` / `sources` fixtures live in
tests/api/conftest.py.
"""

import datetime

from src.api import dataset_metadata
from src.api.jsonld_schemaorg import build_shot_dataset_jsonld
from src.api.models import Level2ShotModel

from .conftest import make_shot, make_source

SITE = "https://mastapp.site"


def test_basic_shape(shot, sources):
    doc = build_shot_dataset_jsonld(shot, sources, SITE)
    assert doc["@context"] == "https://schema.org"
    assert doc["@type"] == "Dataset"
    assert doc["@id"] == "https://mastapp.site/dataset/level1/shot/30420"
    assert doc["url"] == doc["@id"]


def test_required_google_fields_present(shot, sources):
    doc = build_shot_dataset_jsonld(shot, sources, SITE)
    for field in ("name", "description", "license", "identifier", "url", "publisher"):
        assert field in doc, f"missing required field: {field}"


def test_license_is_cc_by_4(shot, sources):
    doc = build_shot_dataset_jsonld(shot, sources, SITE)
    assert doc["license"] == "https://creativecommons.org/licenses/by/4.0/"


def test_identifier_contains_shot_id_and_uuid(shot, sources):
    doc = build_shot_dataset_jsonld(shot, sources, SITE)
    propertyIDs = {ident["propertyID"] for ident in doc["identifier"]}
    assert propertyIDs == {"shot_id", "uuid"}


def test_distributions_use_https_not_s3(shot, sources):
    doc = build_shot_dataset_jsonld(shot, sources, SITE)
    for dist in doc["distribution"]:
        assert not dist["contentUrl"].startswith("s3://"), (
            f"distribution contentUrl should be HTTPS, got {dist['contentUrl']}"
        )


def test_temporal_coverage_is_iso8601_interval(shot, sources):
    doc = build_shot_dataset_jsonld(shot, sources, SITE)
    assert "/" in doc["temporalCoverage"]
    start, end = doc["temporalCoverage"].split("/")
    datetime.datetime.fromisoformat(start)
    datetime.datetime.fromisoformat(end)


def test_included_in_data_catalog(shot, sources):
    doc = build_shot_dataset_jsonld(shot, sources, SITE)
    assert doc["includedInDataCatalog"]["@id"] == "https://mastapp.site/catalog"
    assert doc["isPartOf"] == "https://mastapp.site/catalog"


def test_keywords_deduped(shot, sources):
    doc = build_shot_dataset_jsonld(shot, sources, SITE)
    assert len(doc["keywords"]) == len(set(doc["keywords"]))


def test_variable_measured_uses_source_names_not_boilerplate_title(shot, sources):
    doc = build_shot_dataset_jsonld(shot, sources, SITE)
    names = [v["name"] for v in doc["variableMeasured"]]
    assert "Source Dataset" not in names
    assert names == ["AMC", "AYC"]


def test_has_part_uses_source_name(shot, sources):
    doc = build_shot_dataset_jsonld(shot, sources, SITE)
    part_names = [p["name"] for p in doc["hasPart"]]
    assert part_names == ["AMC", "AYC"]


def test_variable_measured_capped_at_10(shot):
    many = [make_source(f"SRC{i:02d}") for i in range(15)]
    doc = build_shot_dataset_jsonld(shot, many, SITE)
    assert len(doc["variableMeasured"]) == 10


def test_no_cross_link_when_related_url_omitted(shot, sources):
    doc = build_shot_dataset_jsonld(shot, sources, SITE)
    assert "isBasedOn" not in doc
    assert "subjectOf" not in doc


def test_level1_with_related_level_emits_subject_of(shot, sources):
    related = dataset_metadata.shot_page_url(SITE, 30420, level=2)
    doc = build_shot_dataset_jsonld(
        shot, sources, SITE, level=1, related_level_url=related
    )
    assert doc["subjectOf"]["@id"] == related
    assert "isBasedOn" not in doc


def test_level2_with_related_level_emits_is_based_on():
    shot = make_shot(Level2ShotModel)
    related = dataset_metadata.shot_page_url(SITE, 30420, level=1)
    doc = build_shot_dataset_jsonld(
        shot, [], SITE, level=2, related_level_url=related
    )
    assert doc["isBasedOn"]["@id"] == related
    assert "subjectOf" not in doc


def test_level_appears_in_name_and_description(shot, sources):
    doc_l1 = build_shot_dataset_jsonld(shot, sources, SITE, level=1)
    doc_l2 = build_shot_dataset_jsonld(
        make_shot(Level2ShotModel), sources, SITE, level=2
    )
    assert "(Level 1)" in doc_l1["name"]
    assert "(Level 2)" in doc_l2["name"]
    assert doc_l1["description"].startswith("Level 1")
    assert doc_l2["description"].startswith("Level 2")


def test_level_appears_in_keywords(shot, sources):
    doc_l1 = build_shot_dataset_jsonld(shot, sources, SITE, level=1)
    doc_l2 = build_shot_dataset_jsonld(
        make_shot(Level2ShotModel), sources, SITE, level=2
    )
    assert "Level 1" in doc_l1["keywords"]
    assert "Level 2" in doc_l2["keywords"]


def test_url_differs_per_level(shot):
    doc_l1 = build_shot_dataset_jsonld(shot, [], SITE, level=1)
    doc_l2 = build_shot_dataset_jsonld(
        make_shot(Level2ShotModel), [], SITE, level=2
    )
    assert doc_l1["url"] == "https://mastapp.site/dataset/level1/shot/30420"
    assert doc_l2["url"] == "https://mastapp.site/dataset/level2/shot/30420"
