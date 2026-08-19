"""
Feature engineering and preprocessing pipeline adhering to strict ML best practices.
Ensures strict featurization ordering (split before fit) and robust missing value imputation.
"""

import numpy as np
import pandas as pd
from typing import Tuple, List, Dict, Any, Optional
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.model_selection import train_test_split

from src.config import CURRENT_YEAR, ENERGY_CLASSES
from src.data.german_cities import get_city_profile
from src.utils.geo_utils import haversine_distance_km, calculate_micro_location_score

class RealEstateFeatureEngineer(BaseEstimator, TransformerMixin):
    """
    Transforms raw property listings into clean, standardized feature vectors.
    Computes spatial distances, space layout ratios, age features, and categorical encodings.
    """

    def __init__(self, city_name: str = "Deggendorf"):
        self.city_name = city_name
        self.profile = get_city_profile(city_name)
        self.scaler = StandardScaler()
        self.encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
        self.median_build_year: float = 1995.0
        self.median_sqm: float = 75.0
        self.is_fitted: bool = False

        self.numerical_cols = [
            "living_space_sqm",
            "rooms",
            "sqm_per_room",
            "building_age",
            "distance_to_center_km",
            "distance_to_transit_km",
            "distance_to_university_km",
            "micro_location_score",
            "energy_rank",
            "balcony",
            "garden",
            "elevator",
            "fitted_kitchen",
            "parking",
            "is_year_missing",
            "is_altbau",
            "is_new_build",
        ]
        self.categorical_cols = ["district", "property_type", "condition"]
        self.feature_names: List[str] = []

    def _extract_raw_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extracts raw domain-specific features from input dataframe or single listing.
        """
        res = df.copy()

        # Handle missing coordinates by falling back to city center
        if "latitude" not in res.columns or res["latitude"].isnull().all():
            res["latitude"] = self.profile.center_lat
        if "longitude" not in res.columns or res["longitude"].isnull().all():
            res["longitude"] = self.profile.center_lon

        res["latitude"] = res["latitude"].fillna(self.profile.center_lat)
        res["longitude"] = res["longitude"].fillna(self.profile.center_lon)

        # Spatial distances
        res["distance_to_center_km"] = res.apply(
            lambda r: haversine_distance_km(r["latitude"], r["longitude"], self.profile.center_lat, self.profile.center_lon),
            axis=1
        )
        res["distance_to_transit_km"] = res.apply(
            lambda r: haversine_distance_km(r["latitude"], r["longitude"], self.profile.train_station_lat, self.profile.train_station_lon),
            axis=1
        )
        if self.profile.university_lat and self.profile.university_lon:
            res["distance_to_university_km"] = res.apply(
                lambda r: haversine_distance_km(r["latitude"], r["longitude"], self.profile.university_lat, self.profile.university_lon),
                axis=1
            )
        else:
            res["distance_to_university_km"] = res["distance_to_center_km"]

        # Micro-location composite score
        res["micro_location_score"] = res.apply(
            lambda r: calculate_micro_location_score(
                r["distance_to_center_km"],
                r["distance_to_transit_km"],
                r["distance_to_university_km"],
                city_radius_km=self.profile.radius_km
            ),
            axis=1
        )

        # Space layout efficiency
        res["living_space_sqm"] = pd.to_numeric(res["living_space_sqm"], errors="coerce").fillna(self.median_sqm)
        res["rooms"] = pd.to_numeric(res["rooms"], errors="coerce").fillna(3.0)
        res["rooms"] = res["rooms"].apply(lambda x: max(1.0, float(x)))
        res["sqm_per_room"] = res["living_space_sqm"] / res["rooms"]

        # Build year and missing indicator
        res["is_year_missing"] = res["build_year"].isnull().astype(int)
        clean_years = pd.to_numeric(res["build_year"], errors="coerce").fillna(self.median_build_year)
        res["building_age"] = CURRENT_YEAR - clean_years
        res["is_altbau"] = (clean_years < 1945).astype(int)
        res["is_new_build"] = (clean_years >= 2020).astype(int)

        # Energy class ranking (A+ -> 1, A -> 2, ..., H -> 9, UNKNOWN -> 5)
        energy_rank_map = {
            "A+": 1, "A": 2, "B": 3, "C": 4, "D": 5,
            "E": 6, "F": 7, "G": 8, "H": 9, "UNKNOWN": 5
        }
        res["energy_rank"] = res["energy_class"].fillna("UNKNOWN").astype(str).map(lambda x: energy_rank_map.get(x.upper(), 5))

        # Binary amenities
        for col in ["balcony", "garden", "elevator", "fitted_kitchen", "parking"]:
            if col in res.columns:
                res[col] = res[col].fillna(0).astype(int)
            else:
                res[col] = 0

        # Standardize categorical strings
        res["district"] = res["district"].fillna("Zentrum").astype(str)
        res["property_type"] = res["property_type"].fillna("Wohnung").astype(str)
        res["condition"] = res["condition"].fillna("Gepflegt").astype(str)

        return res

    def fit(self, df: pd.DataFrame, y=None):
        """
        Fits transformers strictly on the provided training dataframe.
        """
        # Calculate median values on training set
        if "build_year" in df.columns:
            non_null_years = pd.to_numeric(df["build_year"], errors="coerce").dropna()
            if len(non_null_years) > 0:
                self.median_build_year = float(non_null_years.median())

        if "living_space_sqm" in df.columns:
            non_null_sqm = pd.to_numeric(df["living_space_sqm"], errors="coerce").dropna()
            if len(non_null_sqm) > 0:
                self.median_sqm = float(non_null_sqm.median())

        processed = self._extract_raw_features(df)

        # Fit Scaler on numerical features
        self.scaler.fit(processed[self.numerical_cols])

        # Fit OneHotEncoder on categorical features
        self.encoder.fit(processed[self.categorical_cols])
        
        encoded_cat_names = list(self.encoder.get_feature_names_out(self.categorical_cols))
        self.feature_names = self.numerical_cols + encoded_cat_names
        self.is_fitted = True
        return self

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        """
        Transforms dataframe into feature matrix using fitted parameters.
        """
        if not self.is_fitted:
            raise RuntimeError("RealEstateFeatureEngineer must be fitted before transforming data.")

        processed = self._extract_raw_features(df)
        num_scaled = self.scaler.transform(processed[self.numerical_cols])
        cat_encoded = self.encoder.transform(processed[self.categorical_cols])

        return np.hstack([num_scaled, cat_encoded])

    def fit_transform(self, df: pd.DataFrame, y=None) -> np.ndarray:
        return self.fit(df, y).transform(df)

def prepare_train_test_split(
    df: pd.DataFrame,
    test_size: float = 0.20,
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Splits dataset into train and test sets BEFORE applying any preprocessing transformations,
    strictly adhering to ML Best Practices to avoid data leakage.
    """
    # Drop invalid rows without target price or living space
    valid_mask = (df["price"] > 10000) & (df["living_space_sqm"] > 15)
    clean_df = df[valid_mask].copy()

    X = clean_df.drop(columns=["price"])
    y = clean_df["price"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )
    return X_train, X_test, y_train, y_test
