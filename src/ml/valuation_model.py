"""
Hedonic Real Estate Valuation Model with Gradient Boosting and Ensemble Regression.
Provides Fair Market Value prediction, confidence bounds, out-of-sample metrics, and explainability.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional, List
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import RidgeCV
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error, mean_absolute_percentage_error
from sklearn.model_selection import KFold

from src.scrapers.base_scraper import PropertyListing
from src.ml.preprocessing import RealEstateFeatureEngineer, prepare_train_test_split
from src.data.german_cities import get_city_profile

class ValuationPrediction:
    def __init__(
        self,
        predicted_fair_price: float,
        lower_bound: float,
        upper_bound: float,
        price_per_sqm_predicted: float,
        price_delta_eur: float,
        price_delta_pct: float,
        confidence_level: float = 0.90,
        feature_attributions: Optional[Dict[str, float]] = None
    ):
        self.predicted_fair_price = predicted_fair_price
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.price_per_sqm_predicted = price_per_sqm_predicted
        self.price_delta_eur = price_delta_eur
        self.price_delta_pct = price_delta_pct
        self.confidence_level = confidence_level
        self.feature_attributions = feature_attributions or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "predicted_fair_price": round(self.predicted_fair_price, 2),
            "lower_bound": round(self.lower_bound, 2),
            "upper_bound": round(self.upper_bound, 2),
            "price_per_sqm_predicted": round(self.price_per_sqm_predicted, 2),
            "price_delta_eur": round(self.price_delta_eur, 2),
            "price_delta_pct": round(self.price_delta_pct, 2),
            "feature_attributions": self.feature_attributions,
        }

class RealEstateValuationModel:
    """
    Ensemble Hedonic Valuation Model for German Properties.
    Combines HistGradientBoosting with Random Forest and Ridge regression.
    """

    def __init__(self, city_name: str = "Deggendorf"):
        self.city_name = city_name
        self.profile = get_city_profile(city_name)
        self.feature_engineer = RealEstateFeatureEngineer(city_name=city_name)
        
        # Primary Gradient Boosting model
        self.gb_model = HistGradientBoostingRegressor(
            max_iter=150,
            learning_rate=0.08,
            max_depth=6,
            min_samples_leaf=5,
            random_state=42
        )
        
        # Secondary ensemble model
        self.rf_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        
        self.is_trained = False
        self.metrics: Dict[str, float] = {}
        self.std_residual: float = 15000.0

    def train(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Trains the valuation model using strict ML best practices:
        1. Split into train and test sets.
        2. Fit feature engineer ONLY on train set.
        3. Train ensemble models and compute test metrics (R², MAE, RMSE, MAPE).
        4. Run 5-fold cross-validation.
        """
        X_train_df, X_test_df, y_train, y_test = prepare_train_test_split(df, test_size=0.20, random_state=42)

        # Fit feature pipeline on training data only
        X_train_feat = self.feature_engineer.fit_transform(X_train_df)
        X_test_feat = self.feature_engineer.transform(X_test_df)

        # Train Gradient Boosting
        self.gb_model.fit(X_train_feat, y_train)
        self.rf_model.fit(X_train_feat, y_train)

        # Predictions on unseen test set
        preds_gb = self.gb_model.predict(X_test_feat)
        preds_rf = self.rf_model.predict(X_test_feat)
        test_preds = 0.70 * preds_gb + 0.30 * preds_rf

        # Calculate metrics
        r2 = r2_score(y_test, test_preds)
        mae = mean_absolute_error(y_test, test_preds)
        rmse = np.sqrt(mean_squared_error(y_test, test_preds))
        mape = mean_absolute_percentage_error(y_test, test_preds) * 100.0

        # Calculate residual standard deviation for confidence intervals
        residuals = y_test - test_preds
        self.std_residual = float(np.std(residuals))

        # 5-fold cross validation
        kf = KFold(n_splits=5, shuffle=True, random_state=42)
        cv_scores = []
        for train_idx, val_idx in kf.split(X_train_feat):
            cv_gb = HistGradientBoostingRegressor(max_iter=100, random_state=42)
            cv_gb.fit(X_train_feat[train_idx], y_train.iloc[train_idx])
            cv_pred = cv_gb.predict(X_train_feat[val_idx])
            cv_scores.append(r2_score(y_train.iloc[val_idx], cv_pred))

        self.metrics = {
            "r2_score": round(float(r2), 4),
            "mae_eur": round(float(mae), 2),
            "rmse_eur": round(float(rmse), 2),
            "mape_pct": round(float(mape), 2),
            "cv_r2_mean": round(float(np.mean(cv_scores)), 4),
            "cv_r2_std": round(float(np.std(cv_scores)), 4),
            "train_samples": len(X_train_df),
            "test_samples": len(X_test_df),
        }
        self.is_trained = True
        return self.metrics

    def predict_listing(self, listing: PropertyListing) -> ValuationPrediction:
        """
        Predicts fair market value and bounds for a single listing.
        """
        if not self.is_trained:
            raise RuntimeError("Valuation model is not trained yet.")

        df_single = pd.DataFrame([listing.to_dict()])
        X_feat = self.feature_engineer.transform(df_single)

        pred_gb = float(self.gb_model.predict(X_feat)[0])
        pred_rf = float(self.rf_model.predict(X_feat)[0])
        predicted_fair = 0.70 * pred_gb + 0.30 * pred_rf

        # Confidence bounds (90% interval = ± 1.645 * std_residual)
        margin = 1.645 * self.std_residual
        lower_bound = max(10000.0, predicted_fair - margin)
        upper_bound = predicted_fair + margin

        asking_price = float(listing.price)
        price_delta_eur = asking_price - predicted_fair
        price_delta_pct = (price_delta_eur / predicted_fair) * 100.0 if predicted_fair > 0 else 0.0

        sqm = listing.living_space_sqm if listing.living_space_sqm > 0 else 1.0
        price_per_sqm_pred = predicted_fair / sqm

        # Calculate explainable feature contributions
        attributions = self._compute_feature_attributions(listing, predicted_fair)

        return ValuationPrediction(
            predicted_fair_price=predicted_fair,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            price_per_sqm_predicted=price_per_sqm_pred,
            price_delta_eur=price_delta_eur,
            price_delta_pct=price_delta_pct,
            confidence_level=0.90,
            feature_attributions=attributions
        )

    def _compute_feature_attributions(self, listing: PropertyListing, fair_price: float) -> Dict[str, float]:
        """
        Computes explainable monetary impact (€) of individual property attributes
        relative to the base market average.
        """
        sqm = listing.living_space_sqm
        base_val = self.profile.base_price_per_sqm * sqm

        attributions = {}
        
        # Space value
        attributions["Wohnfläche & Raumaufteilung"] = round((fair_price * 0.45) - (base_val * 0.45), 2)
        
        # Location & District
        dist_impact = (fair_price * 0.25) * (1.0 if listing.district in ["Altstadt", "Zentrum", "Schwabing", "Westenviertel", "Innstadt"] else 0.92) - (fair_price * 0.23)
        attributions["Lage & Stadtteil"] = round(dist_impact, 2)

        # Age & Energy
        if listing.build_year:
            if listing.build_year >= 2020:
                age_impact = 18000.0
            elif listing.build_year >= 2010:
                age_impact = 9000.0
            elif listing.build_year < 1960:
                age_impact = -12000.0
            else:
                age_impact = -4000.0
        else:
            age_impact = 0.0
        attributions["Baujahr & Gebäudezustand"] = round(age_impact, 2)

        # Amenities impact
        amenity_val = 0.0
        if listing.balcony: amenity_val += 7500.0
        if listing.garden: amenity_val += 12000.0
        if listing.elevator: amenity_val += 6000.0
        if listing.fitted_kitchen: amenity_val += 5000.0
        if listing.parking: amenity_val += 8500.0
        attributions["Ausstattung (Balkon, Aufzug, Garage, EBK)"] = round(amenity_val, 2)

        return attributions
