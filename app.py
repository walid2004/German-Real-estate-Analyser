import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any

from src.data.german_cities import list_available_cities, get_city_profile, GERMAN_CITIES
from src.data.data_loader import DataLoader
from src.scrapers.base_scraper import PropertyListing
from src.scrapers.listing_url_parser import ListingUrlParser, SAMPLE_LISTINGS
from src.ml.valuation_model import RealEstateValuationModel
from src.ml.trend_regressor import RealEstateTrendRegressor
from src.valuation.deal_scorer import DealScoringEngine
from src.utils.formatters import format_currency, format_price_per_sqm, format_sqm, get_energy_color

st.set_page_config(
    page_title="German Real Estate Market Analyzer & Valuation",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.1rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.2rem;
    }
    .kpi-card {
        background-color: #F8FAFC;
        border-radius: 10px;
        padding: 16px;
        border-left: 5px solid #2563EB;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    .kpi-title {
        font-size: 0.82rem;
        color: #64748B;
        text-transform: uppercase;
        font-weight: 600;
    }
    .kpi-value {
        font-size: 1.7rem;
        font-weight: 700;
        color: #0F172A;
    }
    .kpi-sub {
        font-size: 0.8rem;
        color: #10B981;
    }
    .parsed-box {
        background-color: #F0FDF4;
        border: 1px solid #BBF7D0;
        border-radius: 8px;
        padding: 14px;
        margin-bottom: 15px;
    }
    /* Fix for dropdown hover overshadowing */
    div[data-baseweb="select"] ul {
        max-height: 380px !important;
    }
    div[data-baseweb="select"] li {
        padding: 8px 12px !important;
        font-size: 0.92rem !important;
    }
</style>
""", unsafe_allow_html=True)

if "data_loader" not in st.session_state:
    st.session_state.data_loader = DataLoader()
if "url_parser" not in st.session_state:
    st.session_state.url_parser = ListingUrlParser()
if "models" not in st.session_state:
    st.session_state.models = {}
if "trend_regressors" not in st.session_state:
    st.session_state.trend_regressors = {}

st.sidebar.title("Immobilien-Analyse")
st.sidebar.markdown("**German Real Estate Market & Valuation Engine**")

city_list = list_available_cities()
selected_city = st.sidebar.selectbox(
    "Select City / Region",
    city_list,
    index=city_list.index("Deggendorf") if "Deggendorf" in city_list else 0
)

allow_custom = st.sidebar.checkbox("Enter custom city name", value=False)
if allow_custom:
    custom_city = st.sidebar.text_input("City name:", value="")
    if custom_city.strip():
        selected_city = custom_city.strip()

city_profile = get_city_profile(selected_city)
st.sidebar.markdown("---")
st.sidebar.markdown(f"**State:** {city_profile.state}")
st.sidebar.markdown(f"**Benchmark Price:** {format_price_per_sqm(city_profile.base_price_per_sqm)}")
st.sidebar.markdown(f"**Gross Rental Yield:** {city_profile.rental_yield_pct:.1f} %")

with st.spinner(f"Loading market data and training valuation model for {selected_city}..."):
    city_df = st.session_state.data_loader.get_city_dataset(selected_city)
    trends_df = st.session_state.data_loader.get_city_historical_trends(selected_city)

    if selected_city not in st.session_state.models:
        model = RealEstateValuationModel(city_name=selected_city)
        model.train(city_df)
        st.session_state.models[selected_city] = model
    else:
        model = st.session_state.models[selected_city]

    if selected_city not in st.session_state.trend_regressors:
        regressor = RealEstateTrendRegressor(city_name=selected_city)
        regressor.fit(trends_df)
        st.session_state.trend_regressors[selected_city] = regressor
    else:
        regressor = st.session_state.trend_regressors[selected_city]

trend_summary = regressor.compute_summary_analytics()

st.markdown(f"<div class='main-header'>Real Estate Market Analysis & Valuation: {selected_city}</div>", unsafe_allow_html=True)
st.markdown(f"<div class='sub-header'>Hedonic Price Valuation, Historical Trend Regression, and 0-100 Deal Scoring for {selected_city} and Germany</div>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs([
    "Market Analysis & Geo Map",
    "Price Trends & Regression (2018-2026)",
    "Property Valuation & Deal Score",
    "City Comparison & Top Deals"
])

# Tab 1: Market Analysis & Geo Map
with tab1:
    col1, col2, col3, col4, col5 = st.columns(5)
    
    avg_price_sqm = city_df["price_per_sqm"].mean()
    median_price_sqm = city_df["price_per_sqm"].median()
    median_total_price = city_df["price"].median()
    total_listings = len(city_df)
    
    with col1:
        st.markdown(f"""
        <div class='kpi-card'>
            <div class='kpi-title'>Average Price / m2</div>
            <div class='kpi-value'>{format_price_per_sqm(avg_price_sqm)}</div>
            <div class='kpi-sub'>Median: {format_price_per_sqm(median_price_sqm)}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
        <div class='kpi-card'>
            <div class='kpi-title'>Median Price</div>
            <div class='kpi-value'>{format_currency(median_total_price)}</div>
            <div class='kpi-sub'>Range: {format_currency(city_df['price'].min())} - {format_currency(city_df['price'].max())}</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class='kpi-card'>
            <div class='kpi-title'>Gross Rental Yield</div>
            <div class='kpi-value'>{trend_summary.get('gross_rental_yield_pct', 4.2):.1f} %</div>
            <div class='kpi-sub'>Avg Rent: {trend_summary.get('estimated_rent_per_sqm_eur', 13.5):.2f} EUR/m2</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class='kpi-card'>
            <div class='kpi-title'>Price-to-Rent Ratio</div>
            <div class='kpi-value'>{trend_summary.get('kaufpreisfaktor', 24.0):.1f}x</div>
            <div class='kpi-sub'>Years of Net Rent</div>
        </div>
        """, unsafe_allow_html=True)

    with col5:
        st.markdown(f"""
        <div class='kpi-card'>
            <div class='kpi-title'>Active Listings</div>
            <div class='kpi-value'>{total_listings}</div>
            <div class='kpi-sub'>Model R2: {model.metrics.get('r2_score', 0.92):.3f}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    map_col, chart_col = st.columns([3, 2])

    with map_col:
        st.subheader(f"Geographic Price Distribution in {selected_city}")
        
        fig_map = px.scatter_mapbox(
            city_df,
            lat="latitude",
            lon="longitude",
            color="price_per_sqm",
            size="living_space_sqm",
            color_continuous_scale="Viridis",
            range_color=[city_df["price_per_sqm"].quantile(0.05), city_df["price_per_sqm"].quantile(0.95)],
            hover_name="title",
            hover_data={
                "district": True,
                "price": ":,.0f EUR",
                "price_per_sqm": ":,.0f EUR/m2",
                "living_space_sqm": ":.1f m2",
                "rooms": True,
                "build_year": True,
                "latitude": False,
                "longitude": False,
            },
            zoom=12,
            center={"lat": city_profile.center_lat, "lon": city_profile.center_lon},
            mapbox_style="carto-positron",
            height=520,
            title=f"Property Listings and Price Levels (EUR/m2) in {selected_city}"
        )
        fig_map.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0})
        st.plotly_chart(fig_map, use_container_width=True)

    with chart_col:
        st.subheader("Price Levels by District (EUR/m2)")
        district_stats = city_df.groupby("district")["price_per_sqm"].agg(["mean", "median", "count"]).reset_index()
        district_stats = district_stats.sort_values(by="mean", ascending=True)

        fig_dist = px.bar(
            district_stats,
            x="mean",
            y="district",
            orientation="h",
            color="mean",
            color_continuous_scale="Blues",
            labels={"mean": "Average Price (EUR/m2)", "district": "District"},
            height=520,
            text_auto=".0f"
        )
        fig_dist.update_layout(showlegend=False, margin={"r": 10, "t": 40, "l": 10, "b": 10})
        st.plotly_chart(fig_dist, use_container_width=True)

    dist_col1, dist_col2 = st.columns(2)
    with dist_col1:
        st.subheader("Price Distribution by Area & Rooms")
        fig_scatter = px.scatter(
            city_df,
            x="living_space_sqm",
            y="price",
            color="property_type",
            size="rooms",
            hover_name="title",
            labels={"living_space_sqm": "Living Space (m2)", "price": "Purchase Price (EUR)", "property_type": "Type"},
            title="Purchase Price vs. Living Space",
            height=380
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    with dist_col2:
        st.subheader("Distribution by Energy Efficiency Class")
        energy_counts = city_df["energy_class"].value_counts().reset_index()
        energy_counts.columns = ["energy_class", "count"]
        fig_pie = px.pie(
            energy_counts,
            names="energy_class",
            values="count",
            color="energy_class",
            color_discrete_map={k: get_energy_color(k) for k in city_df["energy_class"].unique()},
            title="Energy Efficiency Distribution (GEG Scale)",
            height=380
        )
        st.plotly_chart(fig_pie, use_container_width=True)

# Tab 2: Historical Price Trends & Regression
with tab2:
    st.subheader(f"Historical Price Trends & Regression Forecast (2018 - 2026+)")
    st.markdown("""
    The regression model analyzes the long-term price trajectory across key market cycles:
    - **Low-Interest Growth (2018 - Early 2022)**: Substantial valuation expansion driven by low borrowing costs.
    - **Interest Rate Correction (2022 - 2024)**: Market consolidation following ECB policy rate increases.
    - **Supply Shortage & Stabilization (2024 - 2026)**: Market stabilization supported by structural housing demand.
    """)

    trend_df = regressor.predict_trends(forecast_quarters_ahead=6)

    fig_trend = go.Figure()

    actual_mask = trend_df["actual_price_per_sqm"].notnull()
    fig_trend.add_trace(go.Scatter(
        x=trend_df.loc[actual_mask, "quarter"],
        y=trend_df.loc[actual_mask, "actual_price_per_sqm"],
        mode="markers",
        name="Historical Data Point",
        marker=dict(size=8, color="#1E3A8A")
    ))

    fig_trend.add_trace(go.Scatter(
        x=trend_df["quarter"],
        y=trend_df["fitted_price_per_sqm"],
        mode="lines",
        name="Regression Trendline (Fit & Forecast)",
        line=dict(color="#2563EB", width=3)
    ))

    fig_trend.add_trace(go.Scatter(
        x=list(trend_df["quarter"]) + list(trend_df["quarter"])[::-1],
        y=list(trend_df["upper_bound"]) + list(trend_df["lower_bound"])[::-1],
        fill="toself",
        fillcolor="rgba(37, 99, 235, 0.15)",
        line=dict(color="rgba(255,255,255,0)"),
        name="95% Confidence Interval"
    ))

    fig_trend.update_layout(
        title=f"Price Development & Forecast (EUR/m2) for {selected_city}",
        xaxis_title="Quarter",
        yaxis_title="Price per m2 (EUR/m2)",
        hovermode="x unified",
        height=480,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    t_col1, t_col2, t_col3, t_col4 = st.columns(4)
    with t_col1:
        st.metric("Current Average Price / m2", f"{trend_summary.get('current_avg_price_per_sqm', 0):,.0f} EUR/m2")
    with t_col2:
        st.metric("1-Year Trend (YoY)", f"{trend_summary.get('yoy_change_pct', 0):+.2f} %", delta=f"{trend_summary.get('yoy_change_pct', 0):+.1f}%")
    with t_col3:
        st.metric("Historical Peak (2022)", f"{trend_summary.get('peak_price_2022', 0):,.0f} EUR/m2")
    with t_col4:
        st.metric("Market Trough (2024)", f"{trend_summary.get('trough_price_2024', 0):,.0f} EUR/m2")

# Tab 3: Property Valuation & Deal Score
with tab3:
    st.subheader("Property Valuation & 0-100 Deal Scoring Engine")
    st.markdown("Provide a listing URL from ImmoScout24, Immowelt, or Kleinanzeigen, pick a sample listing, or enter parameters manually:")

    # Clean concise sample names to avoid hover clipping / overshadowing
    sample_display_names = {
        "deggendorf_top_deal": "Deggendorf: 3-Room Flat (275k EUR)",
        "deggendorf_altstadt": "Deggendorf: 2-Room City Flat (215k EUR)",
        "passau_innstadt": "Passau: 3-Room Historic Flat (335k EUR)",
        "passau_haidenhof": "Passau: 4-Room New Build (410k EUR)",
        "regensburg_westenviertel": "Regensburg: 3-Room Flat (445k EUR)",
        "regensburg_family_house": "Regensburg: 5-Room House (680k EUR)",
        "muenchen_schwabing": "Munich: Penthouse Schwabing (1.18M EUR)",
        "muenchen_luxury_villa": "Munich: Luxury Villa Bogenhausen (2.45M EUR)",
        "berlin_zehlendorf_villa": "Berlin: Villa Zehlendorf (1.85M EUR)",
        "frankfurt_westend_loft": "Frankfurt: Westend Loft (980k EUR)",
    }

    input_mode = st.radio(
        "Input Mode:",
        ["Listing URL or Curated Sample", "Manual Property Entry"],
        horizontal=True
    )

    initial_listing = None

    if input_mode == "Listing URL or Curated Sample":
        col_url, col_sample = st.columns([3, 2])
        with col_url:
            input_url = st.text_input(
                "Listing URL:",
                placeholder="https://www.immobilienscout24.de/expose/..."
            )
        with col_sample:
            sample_keys = ["-- Select Sample --"] + list(sample_display_names.keys())
            sample_choice = st.selectbox(
                "Or choose a benchmark sample:",
                sample_keys,
                format_func=lambda k: sample_display_names.get(k, k)
            )

        if input_url.strip():
            with st.spinner("Extracting listing metadata from URL..."):
                initial_listing = st.session_state.url_parser.parse_url(input_url, default_city=selected_city)
        elif sample_choice != "-- Select Sample --":
            initial_listing = SAMPLE_LISTINGS[sample_choice]
            if initial_listing.city != selected_city:
                selected_city = initial_listing.city
                if selected_city not in st.session_state.models:
                    c_df = st.session_state.data_loader.get_city_dataset(selected_city)
                    m = RealEstateValuationModel(city_name=selected_city)
                    m.train(c_df)
                    st.session_state.models[selected_city] = m
                model = st.session_state.models[selected_city]

    # Editable form pre-filled with parsed values or defaults
    st.markdown("#### Property Specifications & Verification")
    st.caption("Review extracted parameters below and modify if necessary before running evaluation:")

    default_title = initial_listing.title if initial_listing else "Property Listing"
    default_price = float(initial_listing.price) if initial_listing else 320000.0
    default_sqm = float(initial_listing.living_space_sqm) if initial_listing else 78.0
    default_rooms = float(initial_listing.rooms) if initial_listing else 3.0
    default_year = int(initial_listing.build_year) if (initial_listing and initial_listing.build_year) else 2018
    default_energy = initial_listing.energy_class if initial_listing else "B"
    default_type = initial_listing.property_type if initial_listing else "Wohnung"
    default_cond = initial_listing.condition if initial_listing else "Gepflegt"
    default_balcony = bool(initial_listing.balcony) if initial_listing else True
    default_garden = bool(initial_listing.garden) if initial_listing else False
    default_elevator = bool(initial_listing.elevator) if initial_listing else True
    default_kitchen = bool(initial_listing.fitted_kitchen) if initial_listing else True
    default_parking = bool(initial_listing.parking) if initial_listing else True

    with st.form("property_evaluation_form"):
        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            form_title = st.text_input("Title / Description", value=default_title)
            form_price = st.number_input("Asking Price (EUR)", min_value=10000.0, max_value=50000000.0, value=default_price, step=10000.0)
            form_sqm = st.number_input("Living Space (m2)", min_value=15.0, max_value=2500.0, value=default_sqm, step=1.0)
            form_rooms = st.number_input("Number of Rooms", min_value=1.0, max_value=25.0, value=default_rooms, step=0.5)

        with f_col2:
            form_year = st.number_input("Construction Year", min_value=1850, max_value=2026, value=default_year)
            
            energy_options = ["A+", "A", "B", "C", "D", "E", "F", "G", "H", "UNKNOWN"]
            e_idx = energy_options.index(default_energy) if default_energy in energy_options else 2
            form_energy = st.selectbox("Energy Efficiency Class", energy_options, index=e_idx)
            
            district_list = [d.name for d in city_profile.districts] if city_profile.districts else ["Zentrum"]
            d_idx = 0
            if initial_listing and initial_listing.district:
                for idx, d in enumerate(district_list):
                    if d.lower() in initial_listing.district.lower():
                        d_idx = idx
                        break
            form_district = st.selectbox("District / Neighborhood", district_list, index=d_idx)
            
            type_options = ["Wohnung", "Haus", "Penthouse", "Maisonette", "Villa"]
            t_idx = type_options.index(default_type) if default_type in type_options else 0
            form_type = st.selectbox("Property Type", type_options, index=t_idx)

        with f_col3:
            cond_options = ["Erstbezug", "Neuwertig", "Saniert", "Gepflegt", "Modernisierungsbedürftig", "Renovierungsbedürftig"]
            c_idx = cond_options.index(default_cond) if default_cond in cond_options else 3
            form_condition = st.selectbox("Condition", cond_options, index=c_idx)
            
            st.markdown("**Amenities & Features:**")
            form_balcony = st.checkbox("Balcony / Terrace", value=default_balcony)
            form_elevator = st.checkbox("Elevator", value=default_elevator)
            form_parking = st.checkbox("Parking / Garage", value=default_parking)
            form_kitchen = st.checkbox("Fitted Kitchen", value=default_kitchen)
            form_garden = st.checkbox("Private Garden", value=default_garden)

        submit_btn = st.form_submit_button("Run Evaluation & Score")

    # Evaluate property on submission or if sample/URL is loaded
    listing_to_evaluate = None
    if submit_btn:
        listing_to_evaluate = PropertyListing(
            title=form_title,
            city=selected_city,
            district=form_district,
            price=form_price,
            living_space_sqm=form_sqm,
            rooms=form_rooms,
            build_year=form_year,
            energy_class=form_energy,
            property_type=form_type,
            condition=form_condition,
            balcony=form_balcony,
            garden=form_garden,
            elevator=form_elevator,
            fitted_kitchen=form_kitchen,
            parking=form_parking,
            source="User Verified Form"
        )
    elif initial_listing:
        listing_to_evaluate = initial_listing

    if listing_to_evaluate:
        st.markdown("---")
        st.markdown(f"### Valuation Report: *{listing_to_evaluate.title}*")
        
        prediction = model.predict_listing(listing_to_evaluate)
        deal_engine = DealScoringEngine()
        score_card = deal_engine.evaluate_deal(listing_to_evaluate, prediction)

        res_col1, res_col2, res_col3 = st.columns([2, 2, 3])

        with res_col1:
            st.markdown("#### Deal Score (0-100)")
            
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=score_card.overall_score,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': score_card.deal_verdict, 'font': {'size': 16}},
                gauge={
                    'axis': {'range': [0, 100], 'tickwidth': 1},
                    'bar': {'color': "#1E3A8A"},
                    'steps': [
                        {'range': [0, 40], 'color': "#FCA5A5"},
                        {'range': [40, 60], 'color': "#FDE68A"},
                        {'range': [60, 80], 'color': "#BBF7D0"},
                        {'range': [80, 100], 'color': "#86EFAC"},
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': score_card.overall_score
                    }
                }
            ))
            fig_gauge.update_layout(height=260, margin={"r": 10, "t": 30, "l": 10, "b": 10})
            st.plotly_chart(fig_gauge, use_container_width=True)

        with res_col2:
            st.markdown("#### Market Value Comparison")
            asking = listing_to_evaluate.price
            fair = prediction.predicted_fair_price
            delta_pct = score_card.price_delta_pct

            st.metric("Asking Price", format_currency(asking), f"{format_price_per_sqm(listing_to_evaluate.price_per_sqm)}")
            st.metric("Estimated Fair Market Value", format_currency(fair), f"{format_price_per_sqm(prediction.price_per_sqm_predicted)}")
            
            delta_label = f"{abs(delta_pct):.1f}% Below Market Value" if delta_pct > 0 else f"{abs(delta_pct):.1f}% Above Market Value"
            st.metric("Price Variance (Delta)", delta_label, delta=f"{delta_pct:+.1f}%")
            st.caption(f"90% Confidence Band: {format_currency(prediction.lower_bound)} - {format_currency(prediction.upper_bound)}")

        with res_col3:
            st.markdown("#### 4-Pillar Evaluation")
            
            categories = ["Price Value (40%)", "Location (25%)", "Quality & Energy (20%)", "Layout & Amenities (15%)"]
            values = [score_card.price_score, score_card.location_score, score_card.quality_energy_score, score_card.layout_space_score]

            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=values + [values[0]],
                theta=categories + [categories[0]],
                fill='toself',
                fillcolor='rgba(37, 99, 235, 0.25)',
                line=dict(color='#2563EB', width=2),
                name='Property Score'
            ))
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                showlegend=False,
                height=260,
                margin={"r": 20, "t": 20, "l": 20, "b": 20}
            )
            st.plotly_chart(fig_radar, use_container_width=True)

        st.markdown("---")
        bot_col1, bot_col2 = st.columns(2)

        with bot_col1:
            st.subheader("Feature Attributions: Key Value Drivers")
            st.caption("Estimated monetary contribution of individual property features (in EUR):")
            
            attr_df = pd.DataFrame([
                {"Feature": k, "Value Contribution (EUR)": v} for k, v in prediction.feature_attributions.items()
            ])
            
            fig_attr = px.bar(
                attr_df,
                x="Value Contribution (EUR)",
                y="Feature",
                orientation="h",
                color="Value Contribution (EUR)",
                color_continuous_scale="Tealgrn",
                text_auto=".0f",
                height=280
            )
            fig_attr.update_layout(showlegend=False, margin={"r": 10, "t": 20, "l": 10, "b": 10})
            st.plotly_chart(fig_attr, use_container_width=True)

        with bot_col2:
            st.subheader("Negotiation Guidance & Strategy")
            st.markdown(f"**Recommended Offer Target:** `{format_currency(score_card.recommended_offer_price)}`")
            st.markdown(f"**Calculated Negotiation Margin:** `{format_currency(score_card.negotiation_potential_eur)}`")
            
            st.markdown("**Strengths (Pros):**")
            for pro in score_card.pros:
                st.markdown(f"- {pro}")
                
            if score_card.cons:
                st.markdown("**Risks & Weaknesses (Cons):**")
                for con in score_card.cons:
                    st.markdown(f"- {con}")

            st.markdown("**Negotiation Leverage Points:**")
            for tip in score_card.negotiation_tips:
                st.markdown(f"- {tip}")

# Tab 4: City Comparison & Top Deals
with tab4:
    st.subheader("City Comparison & Regional Overview")
    st.markdown("Comparative market benchmarks across key German cities:")

    comparison_data = []
    for c_name in ["Deggendorf", "Passau", "Regensburg", "München", "Nürnberg", "Augsburg", "Ingolstadt", "Würzburg", "Erlangen", "Straubing", "Landshut", "Berlin", "Hamburg", "Frankfurt am Main", "Köln", "Stuttgart"]:
        p = get_city_profile(c_name)
        comparison_data.append({
            "City": p.name,
            "State": p.state,
            "Avg Price (EUR/m2)": p.base_price_per_sqm,
            "Gross Rental Yield": f"{p.rental_yield_pct:.1f} %",
            "Price-to-Rent Ratio": f"{100/p.rental_yield_pct:.1f}x",
            "Peak Price (2022)": p.historical_peak_2022,
            "Trough Price (2024)": p.historical_trough_2024,
        })
        
    comp_df = pd.DataFrame(comparison_data)
    st.dataframe(
        comp_df.style.format({
            "Avg Price (EUR/m2)": "{:,.0f} EUR/m2",
            "Peak Price (2022)": "{:,.0f} EUR/m2",
            "Trough Price (2024)": "{:,.0f} EUR/m2",
        }),
        use_container_width=True
    )

    st.markdown("---")
    st.subheader(f"Top-Rated Listings in {selected_city}")
    
    with st.spinner("Analyzing active listings and scoring deals..."):
        deal_results = []
        for idx, row in city_df.head(30).iterrows():
            prop = PropertyListing(
                title=row["title"],
                city=row["city"],
                district=row["district"],
                price=row["price"],
                living_space_sqm=row["living_space_sqm"],
                rooms=row["rooms"],
                build_year=int(row["build_year"]) if pd.notnull(row["build_year"]) else None,
                energy_class=row["energy_class"],
                property_type=row["property_type"],
                condition=row["condition"],
                balcony=bool(row["balcony"]),
                garden=bool(row["garden"]),
                elevator=bool(row["elevator"]),
                fitted_kitchen=bool(row["fitted_kitchen"]),
                parking=bool(row["parking"]),
                latitude=row["latitude"],
                longitude=row["longitude"],
                url=row["url"]
            )
            pred = model.predict_listing(prop)
            engine = DealScoringEngine()
            sc = engine.evaluate_deal(prop, pred)
            
            deal_results.append({
                "Deal Score (0-100)": sc.overall_score,
                "Verdict": sc.deal_verdict,
                "Title": prop.title,
                "District": prop.district,
                "Asking Price": prop.price,
                "Fair Value": pred.predicted_fair_price,
                "Living Space": f"{prop.living_space_sqm:.1f} m2",
                "Rooms": prop.rooms,
                "Build Year": prop.build_year or "N/A",
                "Energy Class": prop.energy_class,
            })

        deal_df = pd.DataFrame(deal_results).sort_values(by="Deal Score (0-100)", ascending=False)
        st.dataframe(
            deal_df.style.format({
                "Deal Score (0-100)": "{:.1f}",
                "Asking Price": "{:,.0f} EUR",
                "Fair Value": "{:,.0f} EUR",
            }).background_gradient(subset=["Deal Score (0-100)"], cmap="YlGn"),
            use_container_width=True
        )
