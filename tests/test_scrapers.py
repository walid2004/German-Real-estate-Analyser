"""
Tests for listing data model and URL / HTML parser.
"""

import pytest
from src.scrapers.base_scraper import PropertyListing
from src.scrapers.listing_url_parser import ListingUrlParser, SAMPLE_LISTINGS

def test_property_listing_model():
    prop = PropertyListing(
        title="Schöne 3-Zimmer Wohnung in Deggendorf",
        city="Deggendorf",
        district="Schaching",
        price=300000.0,
        living_space_sqm=75.0,
        rooms=3.0,
        build_year=2018,
        energy_class="B"
    )
    assert prop.price_per_sqm == 4000.0
    data = prop.to_dict()
    assert data["city"] == "Deggendorf"
    assert data["rooms"] == 3.0
    assert data["price_per_sqm"] == 4000.0

def test_sample_listings_available():
    assert "deggendorf_top_deal" in SAMPLE_LISTINGS
    assert "passau_innstadt" in SAMPLE_LISTINGS
    assert "muenchen_schwabing" in SAMPLE_LISTINGS
    
    degg = SAMPLE_LISTINGS["deggendorf_top_deal"]
    assert degg.city == "Deggendorf"
    assert degg.price > 0
    assert degg.living_space_sqm > 0

def test_url_parser_samples():
    parser = ListingUrlParser()
    listing = parser.parse_url("deggendorf_top_deal")
    assert listing.city == "Deggendorf"
    assert listing.rooms == 4.0
    assert listing.price == 299000.0

def test_url_parser_heuristics():
    parser = ListingUrlParser()
    listing = parser.parse_url("https://www.immobilienscout24.de/expose/12345-passau", default_city="Passau")
    assert listing.city == "Passau"
    assert listing.price > 0
    assert listing.living_space_sqm > 0

def test_html_parser_extraction():
    parser = ListingUrlParser()
    html_snippet = """
    <html>
        <head><title>3 Zimmer Eigentumswohnung in Deggendorf</title></head>
        <body>
            <h1>Attraktive Wohnung nahe THD</h1>
            <p>Kaufpreis: 275.000 €</p>
            <p>Wohnfläche: 82,5 m²</p>
            <p>Zimmer: 3 Zimmer</p>
            <p>Baujahr: 2019</p>
            <p>Energieeffizienzklasse: A</p>
            <p>Balkon vorhanden, Aufzug und Tiefgarage.</p>
        </body>
    </html>
    """
    listing = parser.parse_html(html_snippet, default_city="Deggendorf")
    assert listing.price == 275000.0
    assert listing.living_space_sqm == 82.5
    assert listing.rooms == 3.0
    assert listing.build_year == 2019
    assert listing.energy_class == "A"
    assert listing.balcony is True
    assert listing.elevator is True
    assert listing.parking is True
