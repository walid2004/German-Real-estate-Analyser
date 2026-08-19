from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.data.data_loader import DataLoader
from src.data.german_cities import get_city_profile
from src.ml.valuation_model import RealEstateValuationModel
from src.ml.trend_regressor import RealEstateTrendRegressor
from src.valuation.deal_scorer import DealScoringEngine
from src.scrapers.base_scraper import PropertyListing

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
ASSETS_DIR.mkdir(exist_ok=True, parents=True)

# Global styling
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Helvetica"]
plt.rcParams["axes.edgecolor"] = "#CBD5E1"
plt.rcParams["axes.linewidth"] = 0.8

def generate_spatial_and_district_chart():
    loader = DataLoader()
    df = loader.get_city_dataset("Deggendorf")
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), dpi=200)
    
    # 1. Price vs Living Space
    scatter = ax1.scatter(
        df["living_space_sqm"],
        df["price"] / 1000.0,
        c=df["price_per_sqm"],
        cmap="viridis",
        s=df["rooms"] * 20,
        alpha=0.75,
        edgecolors="white",
        linewidth=0.5
    )
    cbar = plt.colorbar(scatter, ax=ax1)
    cbar.set_label("Price per m2 (EUR)", fontsize=10, color="#1E293B")
    cbar.ax.tick_params(labelsize=9)
    
    ax1.set_title("Deggendorf: Purchase Price vs. Living Space", fontsize=12, fontweight="bold", color="#1E3A8A", pad=12)
    ax1.set_xlabel("Living Space (m2)", fontsize=10, color="#334155")
    ax1.set_ylabel("Asking Price (k EUR)", fontsize=10, color="#334155")
    ax1.grid(True, linestyle="--", alpha=0.5)

    # 2. District Price Levels
    dist_stats = df.groupby("district")["price_per_sqm"].mean().sort_values()
    colors = plt.cm.Blues(np.linspace(0.4, 0.9, len(dist_stats)))
    bars = ax2.barh(dist_stats.index, dist_stats.values, color=colors, height=0.6)
    
    for bar in bars:
        w = bar.get_width()
        ax2.text(w - 300, bar.get_y() + bar.get_height()/2, f"{w:,.0f} EUR",
                 ha="right", va="center", color="white", fontweight="bold", fontsize=9)

    ax2.set_title("Deggendorf: Average Price Level by District (EUR/m2)", fontsize=12, fontweight="bold", color="#1E3A8A", pad=12)
    ax2.set_xlabel("Average Price per m2 (EUR)", fontsize=10, color="#334155")
    ax2.grid(True, linestyle="--", alpha=0.5, axis="x")

    plt.tight_layout()
    output_path = ASSETS_DIR / "market_spatial_analysis.png"
    plt.savefig(output_path, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_path}")

def generate_trend_regression_chart():
    loader = DataLoader()
    trends_df = loader.get_city_historical_trends("Deggendorf")
    regressor = RealEstateTrendRegressor("Deggendorf")
    regressor.fit(trends_df)
    forecast_df = regressor.predict_trends(forecast_quarters_ahead=6)

    fig, ax = plt.subplots(figsize=(12, 6), dpi=200)

    # Actuals
    actual_mask = forecast_df["actual_price_per_sqm"].notnull()
    ax.scatter(
        forecast_df.loc[actual_mask, "quarter"],
        forecast_df.loc[actual_mask, "actual_price_per_sqm"],
        color="#1E3A8A",
        s=50,
        zorder=5,
        label="Historical Market Data Points"
    )

    # Trendline
    ax.plot(
        forecast_df["quarter"],
        forecast_df["fitted_price_per_sqm"],
        color="#2563EB",
        linewidth=2.5,
        label="Hedonic Regression Fit & Forecast"
    )

    # Confidence Interval
    ax.fill_between(
        forecast_df["quarter"],
        forecast_df["lower_bound"],
        forecast_df["upper_bound"],
        color="#2563EB",
        alpha=0.15,
        label="95% Confidence Interval Band"
    )

    # Annotate Key Market Phases
    ax.axvline(x="2022-Q1", color="#DC2626", linestyle=":", alpha=0.7)
    ax.text("2022-Q1", 4200, " 2022 Peak\n (ECB Rate Shift)", color="#DC2626", fontsize=8.5, fontweight="bold")

    ax.axvline(x="2024-Q1", color="#16A34A", linestyle=":", alpha=0.7)
    ax.text("2024-Q1", 3350, " 2024 Trough\n (Stabilization)", color="#16A34A", fontsize=8.5, fontweight="bold")

    ax.set_title("Deggendorf Real Estate Price Trajectory & ML Forecast (2018 - 2027)", fontsize=13, fontweight="bold", color="#1E3A8A", pad=15)
    ax.set_xlabel("Quarter", fontsize=10, color="#334155")
    ax.set_ylabel("Price per m2 (EUR/m2)", fontsize=10, color="#334155")
    ax.tick_params(axis="x", rotation=45, labelsize=8.5)
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="upper left", frameon=True, facecolor="white", edgecolor="#CBD5E1")

    plt.tight_layout()
    output_path = ASSETS_DIR / "price_trend_regression.png"
    plt.savefig(output_path, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_path}")

def generate_deal_scoring_chart():
    # Listing and prediction
    prop = PropertyListing(
        title="3-Room Apartment near THD",
        city="Deggendorf",
        district="Schaching",
        price=275000.0,
        living_space_sqm=78.5,
        rooms=3.0,
        build_year=2019,
        energy_class="A",
        balcony=True,
        parking=True,
        elevator=True,
        fitted_kitchen=True
    )
    loader = DataLoader()
    df = loader.get_city_dataset("Deggendorf")
    model = RealEstateValuationModel("Deggendorf")
    model.train(df)
    pred = model.predict_listing(prop)
    deal_engine = DealScoringEngine()
    score_card = deal_engine.evaluate_deal(prop, pred)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), dpi=200)

    # 1. Gauge Bar / Breakdown
    categories = ["Price Value\n(40%)", "Micro-Location\n(25%)", "Building & Energy\n(20%)", "Space & Layout\n(15%)"]
    scores = [score_card.price_score, score_card.location_score, score_card.quality_energy_score, score_card.layout_space_score]
    colors = ["#10B981", "#3B82F6", "#8B5CF6", "#F59E0B"]

    bars = ax1.bar(categories, scores, color=colors, width=0.55, edgecolor="#E2E8F0")
    for bar in bars:
        h = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2, h + 2, f"{h:.1f}", ha="center", va="bottom", fontweight="bold", fontsize=10)

    ax1.set_ylim(0, 115)
    ax1.axhline(score_card.overall_score, color="#1E3A8A", linestyle="--", linewidth=1.5, label=f"Overall Score: {score_card.overall_score:.1f}/100")
    ax1.set_title(f"0-100 Deal Score: {score_card.overall_score:.1f}/100 ({score_card.deal_verdict})", fontsize=12, fontweight="bold", color="#1E3A8A", pad=12)
    ax1.set_ylabel("Pillar Score (0 - 100)", fontsize=10, color="#334155")
    ax1.grid(True, linestyle="--", alpha=0.5, axis="y")
    ax1.legend(loc="upper right", frameon=True)

    # 2. Polar Radar
    labels = np.array(["Price Value", "Location", "Quality & Energy", "Layout & Space"])
    values = np.array([score_card.price_score, score_card.location_score, score_card.quality_energy_score, score_card.layout_space_score])
    
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    values_closed = np.concatenate((values, [values[0]]))
    angles_closed = angles + [angles[0]]

    ax2 = plt.subplot(122, polar=True)
    ax2.plot(angles_closed, values_closed, color="#2563EB", linewidth=2)
    ax2.fill(angles_closed, values_closed, color="#2563EB", alpha=0.25)
    ax2.set_thetagrids(np.degrees(angles), labels, fontsize=10, fontweight="bold", color="#1E293B")
    ax2.set_ylim(0, 100)
    ax2.set_title("4-Pillar Evaluation Radar", fontsize=12, fontweight="bold", color="#1E3A8A", pad=18)

    plt.tight_layout()
    output_path = ASSETS_DIR / "deal_score_gauge_radar.png"
    plt.savefig(output_path, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_path}")

def generate_feature_attributions_chart():
    prop = PropertyListing(
        title="3-Room Apartment near THD",
        city="Deggendorf",
        district="Schaching",
        price=275000.0,
        living_space_sqm=78.5,
        rooms=3.0,
        build_year=2019,
        energy_class="A",
        balcony=True,
        parking=True,
        elevator=True,
        fitted_kitchen=True
    )
    loader = DataLoader()
    df = loader.get_city_dataset("Deggendorf")
    model = RealEstateValuationModel("Deggendorf")
    model.train(df)
    pred = model.predict_listing(prop)

    features = list(pred.feature_attributions.keys())
    values = [v / 1000.0 for v in pred.feature_attributions.values()]

    fig, ax = plt.subplots(figsize=(10, 5), dpi=200)
    colors = ["#10B981" if v >= 0 else "#EF4444" for v in values]
    bars = ax.barh(features, values, color=colors, height=0.55, edgecolor="#CBD5E1")

    for bar in bars:
        w = bar.get_width()
        offset = 0.5 if w >= 0 else -0.5
        ha = "left" if w >= 0 else "right"
        ax.text(w + offset, bar.get_y() + bar.get_height()/2, f"{w:+.1f}k EUR",
                ha=ha, va="center", fontweight="bold", fontsize=9, color="#1E293B")

    ax.axvline(0, color="#64748B", linewidth=0.8)
    ax.set_title("Feature Attributions: Estimated Monetary Value Contribution", fontsize=12, fontweight="bold", color="#1E3A8A", pad=12)
    ax.set_xlabel("Value Contribution (k EUR)", fontsize=10, color="#334155")
    ax.grid(True, linestyle="--", alpha=0.5, axis="x")

    plt.tight_layout()
    output_path = ASSETS_DIR / "feature_attributions_waterfall.png"
    plt.savefig(output_path, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_path}")

def generate_city_comparison_chart():
    cities = ["Deggendorf", "Passau", "Straubing", "Landshut", "Nürnberg", "Augsburg", "Regensburg", "München", "Frankfurt am Main", "Berlin", "Hamburg"]
    prices = [get_city_profile(c).base_price_per_sqm for c in cities]
    yields = [get_city_profile(c).rental_yield_pct for c in cities]

    fig, ax1 = plt.subplots(figsize=(12, 6), dpi=200)
    x = np.arange(len(cities))
    width = 0.4

    rects1 = ax1.bar(x - width/2, prices, width, label="Benchmark Price (EUR/m2)", color="#2563EB", edgecolor="white")
    ax1.set_ylabel("Price per m2 (EUR/m2)", color="#1E3A8A", fontsize=10, fontweight="bold")
    ax1.tick_params(axis="y", labelcolor="#1E3A8A")
    ax1.set_xticks(x)
    ax1.set_xticklabels(cities, rotation=35, ha="right", fontsize=9)
    ax1.grid(True, linestyle="--", alpha=0.4, axis="y")

    ax2 = ax1.twinx()
    rects2 = ax2.plot(x, yields, color="#DC2626", marker="o", linewidth=2.5, label="Gross Rental Yield (%)")
    ax2.set_ylabel("Gross Rental Yield (%)", color="#DC2626", fontsize=10, fontweight="bold")
    ax2.tick_params(axis="y", labelcolor="#DC2626")
    ax2.set_ylim(2.0, 5.5)

    plt.title("German Real Estate Benchmark: Price per m2 vs. Gross Rental Yield", fontsize=13, fontweight="bold", color="#1E3A8A", pad=15)
    plt.tight_layout()
    output_path = ASSETS_DIR / "city_comparison_yields.png"
    plt.savefig(output_path, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_path}")

if __name__ == "__main__":
    print("Generating chart assets...")
    generate_spatial_and_district_chart()
    generate_trend_regression_chart()
    generate_deal_scoring_chart()
    generate_feature_attributions_chart()
    generate_city_comparison_chart()
    print("All charts generated successfully in assets/.")
