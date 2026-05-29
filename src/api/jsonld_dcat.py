"""DCAT 3 JSON-LD builders for MAST datasets.

Served as alternate representations at ``/dataset/shot/{id}.jsonld`` for
DCAT-AP harvesters (B2FIND, OpenAIRE, re3data, EOSC). Companion to
``jsonld_schemaorg`` (which targets Google Dataset Search via HTML
embedding); both describe the same underlying data, in different
vocabularies.

The JSON-LD context mirrors the prefix mappings in ``create.base_context``
(see ``_DCAT_CONTEXT`` below — kept in sync manually to avoid pulling
create.py's heavy deps into the request path). The graph is built
explicitly; we don't route through ``CustomJSONResponse.convert_to_jsonld_terms``,
which is opaque field-name munging meant for the JSON API.
"""

import datetime
from typing import Iterable

from . import dataset_metadata as meta
from .models import BaseSourceModel, Level2ShotModel, ShotModel

# Either processing-level model is acceptable as input — both inherit from
# ShotLike but the enum fields we read (facility, divertor_config, etc.)
# live on the subclasses, not on the base.
ShotLike = ShotModel | Level2ShotModel

# Mirrors src/api/create.py:base_context (which can't be imported from the
# request path because create.py pulls in dask/pyarrow/psycopg2). Keep in
# sync if create.py's prefix table is extended.
_DCAT_CONTEXT = {
    "dcat": "http://www.w3.org/ns/dcat#",
    "dct": "http://purl.org/dc/terms/",
    "foaf": "http://xmlns.com/foaf/0.1/",
    "schema": "https://schema.org",
    "dqv": "http://www.w3.org/ns/dqv#",
    "sdmx-measure": "http://purl.org/linked-data/sdmx/2009/measure#",
    "prov": "http://www.w3.org/ns/prov#",
    "owl": "http://www.w3.org/2002/07/owl#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
}


def _context() -> dict:
    return dict(_DCAT_CONTEXT)


def _publisher_node() -> dict:
    return {
        "@id": meta.PUBLISHER["@id"],
        "@type": "foaf:Organization",
        "foaf:name": meta.PUBLISHER["name"],
        "foaf:homepage": {"@id": meta.PUBLISHER["url"]},
    }


def _license_node() -> dict:
    return {"@id": meta.LICENSE_URL}


def _temporal_node(shot: ShotLike) -> dict:
    start = shot.timestamp
    end = start + datetime.timedelta(seconds=1)
    return {
        "@type": "dct:PeriodOfTime",
        "dcat:startDate": {"@value": start.isoformat(), "@type": "xsd:dateTime"},
        "dcat:endDate": {"@value": end.isoformat(), "@type": "xsd:dateTime"},
    }


def _distributions(shot: ShotLike, site_url: str) -> list[dict]:
    dists: list[dict] = []
    zarr_url = meta.s3_to_http(shot.url, shot.endpoint_url)
    if zarr_url:
        dists.append(
            {
                "@type": "dcat:Distribution",
                "dct:title": "Zarr store",
                "dcat:accessURL": {"@id": zarr_url},
                "dct:format": "application/vnd.zarr",
                "dcat:mediaType": "application/vnd.zarr",
            }
        )
    dists.append(
        {
            "@type": "dcat:Distribution",
            "dct:title": "Parquet metadata export",
            "dcat:accessURL": {
                "@id": f"{site_url}/parquet/shots?filters=shot_id$eq:{shot.shot_id}"
            },
            "dct:format": "application/parquet",
            "dcat:mediaType": "application/parquet",
        }
    )
    dists.append(
        {
            "@type": "dcat:Distribution",
            "dct:title": "JSON metadata",
            "dcat:accessURL": {"@id": f"{site_url}/json/shots/{shot.shot_id}"},
            "dct:format": "application/json",
            "dcat:mediaType": "application/json",
        }
    )
    return dists


def _keywords(shot: ShotLike, level: int) -> list[str]:
    derived: list[str] = [meta.level_label(level), shot.facility.value]
    if shot.campaign:
        derived.append(f"campaign {shot.campaign}")
    if shot.divertor_config:
        derived.append(str(shot.divertor_config.value))
    if shot.plasma_shape:
        derived.append(str(shot.plasma_shape.value))
    if shot.current_range:
        derived.append(str(shot.current_range.value))
    seen: set[str] = set()
    out: list[str] = []
    for kw in derived + list(meta.TOP_LEVEL_KEYWORDS):
        if kw not in seen:
            seen.add(kw)
            out.append(kw)
    return out


def _description(shot: ShotLike, level: int) -> str:
    parts: list[str] = [
        f"{meta.level_label(level)} experimental data from {shot.facility.value} "
        f"shot {shot.shot_id}"
        + (f", campaign {shot.campaign}" if shot.campaign else "")
        + "."
    ]
    if shot.preshot_description:
        parts.append(f"Pre-shot plan: {shot.preshot_description.strip()}")
    if shot.postshot_description:
        parts.append(f"Post-shot observations: {shot.postshot_description.strip()}")
    return " ".join(parts)


def build_shot_dataset_dcat(
    shot: ShotLike,
    sources: Iterable[BaseSourceModel],
    site_url: str,
    level: int = 1,
    related_level_url: str | None = None,
) -> dict:
    """Build a DCAT 3 ``dcat:Dataset`` JSON-LD document for a single shot.

    ``level`` is the processing level (1 or 2). When ``related_level_url`` is
    supplied, the document encodes the derivation relationship via
    ``dct:source`` (level 2 → level 1) or ``dct:hasVersion`` (level 1 →
    level 2).
    """
    sources = list(sources)
    page_url = meta.shot_page_url(site_url, shot.shot_id, level)
    catalog_url = meta.catalog_url(site_url)

    title = f"{shot.facility.value.upper()} shot {shot.shot_id} ({meta.level_label(level)})"

    doc: dict = {
        "@context": _context(),
        "@id": page_url,
        "@type": "dcat:Dataset",
        "dct:title": title,
        "dct:description": _description(shot, level),
        "dct:identifier": str(shot.uuid) if shot.uuid else str(shot.shot_id),
        "dct:license": _license_node(),
        "dct:publisher": _publisher_node(),
        "dct:creator": _publisher_node(),
        "dcat:keyword": _keywords(shot, level),
        "dcat:distribution": _distributions(shot, site_url),
        "dct:isPartOf": {"@id": catalog_url},
        "owl:sameAs": {"@id": page_url},
    }

    if related_level_url:
        if level == 2:
            doc["dct:source"] = {"@id": related_level_url}
        else:
            doc["dct:hasVersion"] = {"@id": related_level_url}

    doc["dct:issued"] = {
        "@value": shot.timestamp.date().isoformat(),
        "@type": "xsd:date",
    }
    doc["dct:modified"] = {
        "@value": shot.timestamp.date().isoformat(),
        "@type": "xsd:date",
    }
    doc["dct:temporal"] = _temporal_node(shot)

    if sources:
        parts: list[dict] = []
        for src in sources:
            src_url = meta.s3_to_http(src.url, src.endpoint_url)
            part = {
                "@type": "dcat:Dataset",
                "dct:title": src.name,
                "dct:description": src.description
                or f"{src.name} diagnostic data for shot {shot.shot_id}.",
                "dct:identifier": str(src.uuid) if src.uuid else src.name,
                "dcat:distribution": (
                    [
                        {
                            "@type": "dcat:Distribution",
                            "dcat:accessURL": {"@id": src_url},
                            "dct:format": "application/vnd.zarr",
                            "dcat:mediaType": "application/vnd.zarr",
                        }
                    ]
                    if src_url
                    else []
                ),
            }
            parts.append(part)
        doc["dct:hasPart"] = parts

    return doc
