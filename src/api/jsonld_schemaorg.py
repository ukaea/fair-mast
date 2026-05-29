"""schema.org Dataset JSON-LD builders for MAST landing pages.

Embedded in HTML pages via ``<script type="application/ld+json">`` so Google
Dataset Search indexes them. Builders are pure functions returning dicts;
templates serialise via ``tojson``.
"""

import datetime
from typing import Iterable

from . import dataset_metadata as meta
from .models import BaseSourceModel, Level2ShotModel, ShotModel

# Either processing-level model is acceptable as input — both inherit from
# ShotLike but the enum fields we read (facility, divertor_config, etc.)
# live on the subclasses, not on the base.
ShotLike = ShotModel | Level2ShotModel


def _shot_name(shot: ShotLike, level: int) -> str:
    return f"{shot.facility.value.upper()} shot {shot.shot_id} ({meta.level_label(level)})"


def _shot_description(shot: ShotLike, level: int) -> str:
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


def _shot_keywords(shot: ShotLike, level: int) -> list[str]:
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


def _temporal_coverage(shot: ShotLike) -> str:
    # MAST plasma pulses last ~1s; the timestamp marks the pulse start.
    start = shot.timestamp
    end = start + datetime.timedelta(seconds=1)
    return f"{start.isoformat()}/{end.isoformat()}"


def _identifiers(shot: ShotLike, site_url: str) -> list[dict]:
    ids: list[dict] = [
        {
            "@type": "PropertyValue",
            "propertyID": "shot_id",
            "value": str(shot.shot_id),
        }
    ]
    if shot.uuid:
        ids.append(
            {
                "@type": "PropertyValue",
                "propertyID": "uuid",
                "value": str(shot.uuid),
            }
        )
    return ids


def _distributions(shot: ShotLike, site_url: str) -> list[dict]:
    dists: list[dict] = []
    zarr_url = meta.s3_to_http(shot.url, shot.endpoint_url)
    if zarr_url:
        dists.append(
            {
                "@type": "DataDownload",
                "encodingFormat": "application/vnd.zarr",
                "contentUrl": zarr_url,
                "name": "Zarr store (full shot data)",
            }
        )
    dists.append(
        {
            "@type": "DataDownload",
            "encodingFormat": "application/parquet",
            "contentUrl": f"{site_url}/parquet/shots?filters=shot_id$eq:{shot.shot_id}",
            "name": "Parquet metadata export",
        }
    )
    dists.append(
        {
            "@type": "DataDownload",
            "encodingFormat": "application/json",
            "contentUrl": f"{site_url}/json/shots/{shot.shot_id}",
            "name": "JSON metadata",
        }
    )
    return dists


def _variable_measured(sources: Iterable[BaseSourceModel]) -> list[dict]:
    # Curated list of diagnostic systems (sources), capped — these are what
    # researchers actually search for, e.g. "Thomson scattering MAST".
    out: list[dict] = []
    seen: set[str] = set()
    for src in sources:
        if src.name in seen:
            continue
        seen.add(src.name)
        item = {
            "@type": "PropertyValue",
            "name": src.name,
            "propertyID": src.name,
        }
        if src.description:
            item["description"] = src.description
        out.append(item)
        if len(out) >= 10:
            break
    return out


def _has_part(sources: Iterable[BaseSourceModel], shot: ShotLike) -> list[dict]:
    parts: list[dict] = []
    for src in sources:
        part: dict = {
            "@type": "Dataset",
            "name": src.name,
            "description": src.description or f"{src.name} diagnostic data for shot {shot.shot_id}.",
        }
        src_url = meta.s3_to_http(src.url, src.endpoint_url)
        if src_url:
            part["distribution"] = {
                "@type": "DataDownload",
                "encodingFormat": "application/vnd.zarr",
                "contentUrl": src_url,
            }
        if src.uuid:
            part["identifier"] = {
                "@type": "PropertyValue",
                "propertyID": "uuid",
                "value": str(src.uuid),
            }
        parts.append(part)
    return parts


def build_shot_dataset_jsonld(
    shot: ShotLike,
    sources: Iterable[BaseSourceModel],
    site_url: str,
    level: int = 1,
    related_level_url: str | None = None,
) -> dict:
    """Build a schema.org/Dataset JSON-LD document for a single MAST shot.

    The output is intended to be embedded in an HTML landing page via
    ``<script type="application/ld+json">`` for Google Dataset Search.

    ``level`` is the processing level (1 or 2). When ``related_level_url`` is
    supplied, the document links to the counterpart at the other processing
    level via ``isBasedOn`` (level 2 → level 1) or ``subjectOf`` (level 1 →
    level 2).
    """
    sources = list(sources)
    page_url = meta.shot_page_url(site_url, shot.shot_id, level)
    catalog_url = meta.catalog_url(site_url)

    doc: dict = {
        "@context": "https://schema.org",
        "@type": "Dataset",
        "@id": page_url,
        "name": _shot_name(shot, level),
        "description": _shot_description(shot, level),
        "url": page_url,
        "sameAs": meta.shot_jsonld_url(site_url, shot.shot_id, level),
        "identifier": _identifiers(shot, site_url),
        "license": meta.LICENSE_URL,
        "isAccessibleForFree": True,
        "creator": meta.PUBLISHER,
        "publisher": meta.PUBLISHER,
        "funder": meta.FUNDER,
        "keywords": _shot_keywords(shot, level),
        "measurementTechnique": meta.MEASUREMENT_TECHNIQUE,
        "distribution": _distributions(shot, site_url),
        "includedInDataCatalog": {
            "@type": "DataCatalog",
            "@id": catalog_url,
            "name": meta.CATALOG_NAME,
            "url": catalog_url,
        },
        "isPartOf": catalog_url,
    }

    if related_level_url:
        if level == 2:
            doc["isBasedOn"] = {"@type": "Dataset", "@id": related_level_url}
        else:
            doc["subjectOf"] = {"@type": "Dataset", "@id": related_level_url}

    doc["datePublished"] = shot.timestamp.date().isoformat()
    doc["dateModified"] = shot.timestamp.date().isoformat()
    doc["temporalCoverage"] = _temporal_coverage(shot)

    variables = _variable_measured(sources)
    if variables:
        doc["variableMeasured"] = variables

    parts = _has_part(sources, shot)
    if parts:
        doc["hasPart"] = parts

    return doc
