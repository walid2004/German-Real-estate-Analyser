"""
Tests for Feature Engineering, Hedonic Valuation Model, and Trend Regressor.
"""

import pytest
import pandas as pd
import numpy as np

from src.data.data_loader import DataLoader
from src.ml.preprocessing import RealEstateFeatureEngineer, prepare_train_test_split
from src.ml.valuation_model import RealEstateValuationModel
from src.ml.trend_regressor import RealEstateTrendRegressor
from src.scrapers.base_scraper import PropertyListing

def test_feature_engineering_strict_ordering():
    loader = DataLoader()
    df = loader.get_city_dataset("Deggendorf")
    
    X_train, X_test, y_train, y_test = prepare_train_test_split(df, test_size=0.20, random_state=42)
    
    fe = RealEstateFeatureEngineer(city_name="Deggendorf")
    X_train_feat = fe.fit_transform(X_train)
    X_test_feat = fe.transform(X_test)
    
    assert X_train_feat.shape[0] == len(X_train)
    assert X_test_feat.shape[0] == len(X_test)
    assert X_train_feat.shape[1] == X_test_feat.shape[1]
    assert len(fe.feature_names) == X_train_feat.shape[1]

def test_valuation_model_training_and_metrics():
    loader = DataLoader()
    df = loader.get_city_dataset("Passau")
    
    model = RealEstateValuationModel(city_name="Passau")
    metrics = model.train(df)
    
    assert model.is_trained
    assert metrics["r2_score"] >= 0.75
    assert metrics["mae_eur"] > 0
    assert metrics["mape_pct"] < 25.0
    assert metrics["cv_r2_mean"] >= 0.70

def test_valuation_prediction_for_listing():
    loader = DataLoader()
    df = loader.get_city_dataset("Deggendorf")
    model = RealEstateValuationModel(city_name="Deggendorf")
    model.train(df)
    
    prop = PropertyListing(
        title="3-Zimmer Wohnung in Deggendorf",
        city="Deggendorf",
        district="Altstadt / Zentrum",
        price=290000.0,
        living_space_sqm=80.0,
        rooms=3.0,
        build_year=2018,
        energy_class="A",
        balcony=True,
        parking=True
    )
    
    pred = model.predict_listing(prop)
    assert pred.predicted_fair_price > 100000.0
    assert pred.lower_bound < pred.predicted_fair_price < pred.upper_bound
    assert pred.price_per_sqm_predicted > 0
    assert "Wohnfläche & Raumaufteilung" in pred.feature_attributions

def test_trend_regressor():
    loader = DataLoader()
    trends_df = loader.get_city_historical_trends("München")
    
    regressor = RealEstateTrendRegressor(city_name="München")
    regressor.fit(trends_df)
    
    forecast_df = regressor.predict_trends(forecast_quarters_ahead=4)
    assert len(forecast_df) == len(trends_df) + 4
    assert (forecast_df["lower_bound"] <= forecast_df["fitted_price_per_sqm"]).all()
    assert (forecast_df["fitted_price_per_sqm"] <= forecast_df["upper_bound"]).all()
    
    summary = regressor.compute_summary_analytics()
    assert summary["city"] == "München"
    assert summary["current_avg_price_per_sqm"] > 5000.0
    assert summary["gross_rental_yield_pct"] > 0
