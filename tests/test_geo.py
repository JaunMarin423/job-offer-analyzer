"""Tests for country/region location matching."""

from jobranker.geo import location_matches_country, normalize_country


def test_normalize_country_aliases():
    assert normalize_country("Colombia") == "colombia"
    assert normalize_country("CO") == "colombia"
    assert normalize_country("España") == "spain"
    assert normalize_country("MX") == "mexico"


def test_colombia_keeps_in_country_and_regions():
    for loc in ["Bogotá, Colombia", "Colombia", "LATAM", "Latin America",
                "South America", "Americas, Europe, Asia, Oceania"]:
        assert location_matches_country(loc, "colombia"), loc


def test_colombia_keeps_globally_remote():
    for loc in ["Anywhere in the World", "Worldwide", "Remote - Global"]:
        assert location_matches_country(loc, "colombia"), loc


def test_colombia_drops_other_onsite_regions():
    for loc in ["United States", "Berlin", "Munich", "Brazil", "Slovenia",
                "Redmond, WA"]:
        assert not location_matches_country(loc, "colombia"), loc


def test_empty_location_does_not_match():
    assert not location_matches_country("", "colombia")
