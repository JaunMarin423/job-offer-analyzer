"""Country/region matching for location-based filtering.

Free job feeds report locations as free text ("Bogotá, Colombia", "LATAM",
"Anywhere in the World", "United States"). To surface offers a candidate in a
given country can realistically take, we keep postings that are either located
in that country/region or globally remote, and drop ones locked to another
on-site region (e.g. "Berlin", "United States").
"""

from __future__ import annotations

import unicodedata
from typing import Dict, List

# Tokens that signal a globally-open remote role (takeable from anywhere).
_GLOBAL_REMOTE_TOKENS = (
    "worldwide", "anywhere", "global", "everywhere", "fully remote",
    "remote - global", "100% remote", "world",
)

# Per-country aliases plus the regions that include that country.
_COUNTRY_ALIASES: Dict[str, List[str]] = {
    "colombia": [
        "colombia", "colombian", "bogota", "medellin", "cali", "barranquilla",
        "cartagena", "latam", "latin america", "latinoamerica",
        "america latina", "south america", "sudamerica", "americas",
    ],
    "mexico": [
        "mexico", "mexican", "cdmx", "guadalajara", "monterrey", "latam",
        "latin america", "latinoamerica", "america latina", "americas",
    ],
    "argentina": [
        "argentina", "argentine", "buenos aires", "cordoba", "latam",
        "latin america", "latinoamerica", "america latina", "south america",
        "sudamerica", "americas",
    ],
    "spain": [
        "spain", "espana", "spanish", "madrid", "barcelona", "valencia",
        "europe", "emea",
    ],
}

# Country aliases for normalizing the user-supplied value to a canonical key.
_COUNTRY_NAMES = {
    "colombia": "colombia", "co": "colombia",
    "mexico": "mexico", "mx": "mexico", "méxico": "mexico",
    "argentina": "argentina", "ar": "argentina",
    "spain": "spain", "espana": "spain", "españa": "spain", "es": "spain",
}


def _strip_accents(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _norm(text: str) -> str:
    return _strip_accents(text or "").lower()


def normalize_country(value: str) -> str:
    """Map a user-supplied country name/code to a canonical key (e.g. 'colombia')."""
    key = _norm(value).strip()
    return _COUNTRY_NAMES.get(key, key)


def location_matches_country(location: str, country: str) -> bool:
    """True if `location` is in the country/region or is globally remote."""
    loc = _norm(location)
    if not loc:
        return False
    if any(token in loc for token in _GLOBAL_REMOTE_TOKENS):
        return True
    key = normalize_country(country)
    aliases = _COUNTRY_ALIASES.get(key, [key])
    return any(alias in loc for alias in aliases)
