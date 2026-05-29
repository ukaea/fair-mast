"""Static metadata used by the schema.org and DCAT JSON-LD builders.

Values that apply uniformly across all MAST/MAST-U shots live here as
constants. Per-shot variation (timestamp, scenario, signals, etc.) comes
from the database, not this module.
"""

LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"
LICENSE_NAME = "Creative Commons Attribution 4.0 International (CC-BY-4.0)"

PUBLISHER = {
    "@id": "https://ror.org/05nbnja43",
    "@type": "Organization",
    "name": "UK Atomic Energy Authority",
    "url": "https://ccfe.ukaea.uk/",
}

FUNDER = {
    "@type": "Organization",
    "name": "UK Atomic Energy Authority",
    "url": "https://ccfe.ukaea.uk/",
}

CONTACT_POINT = {
    "@type": "ContactPoint",
    "contactType": "Data curator",
    "email": "fair-mast@ukaea.uk",
}

TOP_LEVEL_KEYWORDS = [
    "fusion",
    "tokamak",
    "plasma physics",
    "MAST",
    "MAST-U",
    "magnetic confinement fusion",
    "spherical tokamak",
]

CATALOG_NAME = "FAIR MAST Data Archive"
CATALOG_DESCRIPTION = (
    "Open experimental data from the MAST and MAST-U spherical tokamaks "
    "operated by the UK Atomic Energy Authority. Includes plasma physics "
    "signals, source diagnostic data, and per-shot metadata for fusion "
    "research."
)

MEASUREMENT_TECHNIQUE = "Magnetic confinement fusion plasma diagnostics"


def catalog_url(site_url: str) -> str:
    return f"{site_url}/catalog"


def shot_page_url(site_url: str, shot_id: int, level: int = 1) -> str:
    return f"{site_url}/dataset/level{level}/shot/{shot_id}"


def shot_jsonld_url(site_url: str, shot_id: int, level: int = 1) -> str:
    return f"{site_url}/dataset/level{level}/shot/{shot_id}.jsonld"


def level_label(level: int) -> str:
    """Human-readable label for a processing level (used in titles, keywords)."""
    return f"Level {level}"


def s3_to_http(s3_url: str | None, endpoint_url: str | None) -> str | None:
    """Convert an ``s3://bucket/key`` URL to ``{endpoint_url}/bucket/key``.

    Returns the original URL unchanged if it isn't an s3:// URL, or if no
    endpoint is available. Browsers and Googlebot can't follow s3:// URLs,
    so distribution / accessURL values need the HTTP form.
    """
    if not s3_url:
        return s3_url
    if not s3_url.startswith("s3://"):
        return s3_url
    if not endpoint_url:
        return s3_url
    return f"{endpoint_url.rstrip('/')}/{s3_url[len('s3://'):]}"
