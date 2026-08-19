"""
Tests for 0-100 Deal Scoring Engine.
"""

import pytest
from src.scrapers.base_scraper import PropertyListing
from src.ml.valuation_model import ValuationPrediction
from src.valuation.deal_scorer import DealScoringEngine

def test_deal_scorer_bounds_and_structure():
    engine = DealScoringEngine()
    
    prop = PropertyListing(
        title="Gepflegte Eigentumswohnung",
        city="Deggendorf",
        district="Schaching",
        price=260000.0,
        living_space_sqm=75.0,
        rooms=3.0,
        build_year=2019,
        energy_class="A",
        balcony=True,
        parking=True
    )
    
    pred = ValuationPrediction(
        predicted_fair_price=290000.0,
        lower_bound=270000.0,
        upper_bound=310000.0,
        price_per_sqm_predicted=3866.67,
        price_delta_eur=-30000.0,
        price_delta_pct=-10.34
    )
    
    score_card = engine.evaluate_deal(prop, pred)
    assert 0.0 <= score_card.overall_score <= 100.0
    assert 0.0 <= score_card.price_score <= 100.0
    assert 0.0 <= score_card.location_score <= 100.0
    assert 0.0 <= score_card.quality_energy_score <= 100.0
    assert 0.0 <= score_card.layout_space_score <= 100.0
    assert score_card.recommended_offer_price > 0
    assert len(score_card.pros) > 0

def test_undervalued_vs_overpriced_comparison():
    engine = DealScoringEngine()
    fair_value = 300000.0
    
    prop_cheap = PropertyListing(
        title="Günstige Wohnung",
        city="Passau",
        district="Innstadt",
        price=240000.0,  # 20% below fair value
        living_space_sqm=80.0,
        rooms=3.0,
        build_year=2015,
        energy_class="B"
    )
    
    prop_expensive = PropertyListing(
        title="Teure Wohnung",
        city="Passau",
        district="Innstadt",
        price=380000.0,  # 26.6% above fair value
        living_space_sqm=80.0,
        rooms=3.0,
        build_year=2015,
        energy_class="B"
    )
    
    pred = ValuationPrediction(
        predicted_fair_price=fair_value,
        lower_bound=280000.0,
        upper_bound=320000.0,
        price_per_sqm_predicted=3750.0,
        price_delta_eur=0.0,
        price_delta_pct=0.0
    )
    
    score_cheap = engine.evaluate_deal(prop_cheap, pred)
    score_expensive = engine.evaluate_deal(prop_expensive, pred)
    
    assert score_cheap.overall_score > score_expensive.overall_score
    assert score_cheap.price_score > score_expensive.price_score
    assert score_cheap.overall_score >= 75.0
    assert score_expensive.overall_score < 60.0
