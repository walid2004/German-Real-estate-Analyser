"""
Time-series Price Trend Regression & Forecasting Engine for German Real Estate.
Models quarterly price trends (2018-2026), captures interest rate inflection points,
and projects future trajectory with confidence bands.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, List, Optional
from sklearn.linear_model import Ridge
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.pipeline import make_pipeline

from src.data.german_cities import get_city_profile

class RealEstateTrendRegressor:
    """
    Models and forecasts quarterly price per m² (€/m²) trends.
    """

    def __init__(self, city_name: str = "Deggendorf"):
        self.city_name = city_name
        self.profile = get_city_profile(city_name)
        self.model = make_pipeline(
            PolynomialFeatures(degree=3, include_bias=False),
            StandardScaler(),
            Ridge(alpha=1.0)
        )
        self.is_fitted = False
        self.historical_data: Optional[pd.DataFrame] = None

    def fit(self, trends_df: pd.DataFrame):
        """
        Fits trend regression on historical quarterly data.
        """
        self.historical_data = trends_df.copy()
        
        # Convert quarters to numeric time (e.g. 2018-Q1 -> 2018.0)
        t_values = []
        for q in trends_df["quarter"]:
            parts = q.split("-Q")
            year = float(parts[0])
            quarter = float(parts[1])
            t_values.append(year + (quarter - 1) / 4.0)

        self.historical_data["time_numeric"] = t_values
        X = np.array(t_values).reshape(-1, 1)
        y = trends_df["avg_price_per_sqm"].values

        self.model.fit(X, y)
        self.is_fitted = True
        return self

    def predict_trends(self, forecast_quarters_ahead: int = 6) -> pd.DataFrame:
        """
        Generates fitted historical curve and future forecast with confidence bands.
        """
        if not self.is_fitted or self.historical_data is None:
            raise RuntimeError("Trend regressor must be fitted before predicting.")

        last_t = self.historical_data["time_numeric"].iloc[-1]
        
        # Future quarters
        future_t = []
        future_quarters = []
        last_year = int(last_t)
        last_q = int(round((last_t - last_year) * 4 + 1))

        current_y, current_q = last_year, last_q
        for _ in range(forecast_quarters_ahead):
            current_q += 1
            if current_q > 4:
                current_q = 1
                current_y += 1
            future_t.append(current_y + (current_q - 1) / 4.0)
            future_quarters.append(f"{current_y}-Q{current_q}")

        all_t = np.concatenate([self.historical_data["time_numeric"].values, np.array(future_t)])
        all_quarters = list(self.historical_data["quarter"].values) + future_quarters
        is_forecast = [False] * len(self.historical_data) + [True] * len(future_t)

        preds = self.model.predict(all_t.reshape(-1, 1))

        # 95% Confidence bounds
        std_err = 65.0  # Estimated standard error in €/m²
        margin = 1.96 * std_err * (1.0 + np.linspace(0, 0.4, len(all_t)))

        res_df = pd.DataFrame({
            "quarter": all_quarters,
            "time_numeric": all_t,
            "fitted_price_per_sqm": np.round(preds, 1),
            "lower_bound": np.round(preds - margin, 1),
            "upper_bound": np.round(preds + margin, 1),
            "is_forecast": is_forecast,
        })

        # Attach actuals where available
        actual_map = dict(zip(self.historical_data["quarter"], self.historical_data["avg_price_per_sqm"]))
        res_df["actual_price_per_sqm"] = res_df["quarter"].map(actual_map)

        return res_df

    def compute_summary_analytics(self) -> Dict[str, Any]:
        """
        Computes key real estate analytics:
        - Peak price (2022) & trough (2024)
        - 1-Year price change %
        - 5-Year CAGR %
        - Estimated gross rental yield & price-to-rent ratio
        """
        if self.historical_data is None or len(self.historical_data) == 0:
            return {}

        df = self.historical_data
        current_price = float(df["avg_price_per_sqm"].iloc[-1])
        one_year_ago_price = float(df["avg_price_per_sqm"].iloc[-5]) if len(df) >= 5 else current_price
        start_price = float(df["avg_price_per_sqm"].iloc[0])

        yoy_change_pct = ((current_price - one_year_ago_price) / one_year_ago_price) * 100.0
        total_growth_pct = ((current_price - start_price) / start_price) * 100.0

        # Purchase price factor (Kaufpreisfaktor / Price-to-Rent ratio)
        # Yield % = (Annual Rent / Purchase Price) * 100
        # Factor = 100 / Yield %
        yield_pct = self.profile.rental_yield_pct
        kaufpreisfaktor = 100.0 / yield_pct if yield_pct > 0 else 25.0
        est_monthly_rent_per_sqm = (current_price * (yield_pct / 100.0)) / 12.0

        return {
            "city": self.profile.name,
            "current_avg_price_per_sqm": current_price,
            "yoy_change_pct": round(yoy_change_pct, 2),
            "total_growth_2018_2026_pct": round(total_growth_pct, 2),
            "gross_rental_yield_pct": round(yield_pct, 2),
            "kaufpreisfaktor": round(kaufpreisfaktor, 1),
            "estimated_rent_per_sqm_eur": round(est_monthly_rent_per_sqm, 2),
            "peak_price_2022": self.profile.historical_peak_2022,
            "trough_price_2024": self.profile.historical_trough_2024,
        }
