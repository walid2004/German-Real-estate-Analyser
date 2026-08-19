import argparse
import sys
from tabulate import tabulate

from src.scrapers.base_scraper import PropertyListing
from src.scrapers.listing_url_parser import ListingUrlParser, SAMPLE_LISTINGS
from src.data.data_loader import DataLoader
from src.ml.valuation_model import RealEstateValuationModel
from src.valuation.deal_scorer import DealScoringEngine
from src.utils.formatters import format_currency, format_price_per_sqm, format_sqm

def main():
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="German Real Estate Valuation and Deal Scoring Tool")
    parser.add_argument("--city", type=str, default="Deggendorf", help="German city name (e.g. Deggendorf, Passau, Muenchen)")
    parser.add_argument("--url", type=str, default=None, help="Listing URL or sample key")
    parser.add_argument("--sample", type=str, default=None, help="Sample listing key (e.g. deggendorf_top_deal, passau_innstadt)")
    
    parser.add_argument("--price", type=float, default=None, help="Asking price in EUR")
    parser.add_argument("--sqm", type=float, default=None, help="Living space in m2")
    parser.add_argument("--rooms", type=float, default=3.0, help="Number of rooms")
    parser.add_argument("--year", type=int, default=None, help="Year of construction")
    parser.add_argument("--energy", type=str, default="C", help="Energy efficiency class (A+, A, B, C, D, E, F, G, H)")
    parser.add_argument("--district", type=str, default="Zentrum", help="District name")
    parser.add_argument("--balcony", action="store_true", help="Has balcony or terrace")
    parser.add_argument("--garden", action="store_true", help="Has garden")
    parser.add_argument("--elevator", action="store_true", help="Has elevator")
    parser.add_argument("--kitchen", action="store_true", help="Has fitted kitchen")
    parser.add_argument("--parking", action="store_true", help="Has parking spot or garage")
    
    args = parser.parse_args()

    city = args.city.strip()
    url_parser = ListingUrlParser()

    if args.sample:
        sample_key = args.sample.lower()
        if sample_key in SAMPLE_LISTINGS:
            listing = SAMPLE_LISTINGS[sample_key]
        else:
            print(f"Sample '{args.sample}' not found. Available samples: {list(SAMPLE_LISTINGS.keys())}")
            sys.exit(1)
    elif args.url:
        listing = url_parser.parse_url(args.url, default_city=city)
    elif args.price and args.sqm:
        listing = PropertyListing(
            title=f"{args.rooms:.1f}-Room Property in {city}",
            city=city,
            district=args.district,
            price=args.price,
            living_space_sqm=args.sqm,
            rooms=args.rooms,
            build_year=args.year,
            energy_class=args.energy.upper(),
            balcony=args.balcony,
            garden=args.garden,
            elevator=args.elevator,
            fitted_kitchen=args.kitchen,
            parking=args.parking,
            source="CLI Input"
        )
    else:
        sample_key = f"{city.lower()}_top_deal"
        if sample_key in SAMPLE_LISTINGS:
            listing = SAMPLE_LISTINGS[sample_key]
        else:
            listing = list(SAMPLE_LISTINGS.values())[0]

    print("=" * 75)
    print(f"GERMAN REAL ESTATE VALUATION & DEAL EVALUATOR: {listing.city.upper()}")
    print("=" * 75)
    
    print(f"\n[1/3] Loading market listings and training Hedonic Valuation Model for {listing.city}...")
    loader = DataLoader()
    df = loader.get_city_dataset(listing.city)
    
    model = RealEstateValuationModel(city_name=listing.city)
    metrics = model.train(df)
    
    print(f"      Model trained on {metrics['train_samples']} listings.")
    print(f"      Validation R2 Score: {metrics['r2_score']:.4f} | MAE: {format_currency(metrics['mae_eur'])} | MAPE: {metrics['mape_pct']:.2f}%")

    print(f"\n[2/3] Evaluating Listing: '{listing.title}'...")
    prediction = model.predict_listing(listing)

    print("\n[3/3] Calculating Multi-Factor 0-100 Deal Score & Negotiation Strategy...")
    deal_engine = DealScoringEngine()
    score_card = deal_engine.evaluate_deal(listing, prediction)

    print("\n" + "=" * 75)
    print(" PROPERTY OVERVIEW")
    print("=" * 75)
    prop_table = [
        ["Title", listing.title],
        ["City & District", f"{listing.city} ({listing.district})"],
        ["Living Space", format_sqm(listing.living_space_sqm)],
        ["Rooms", f"{listing.rooms:.1f} Rooms"],
        ["Build Year", listing.build_year if listing.build_year else "Unknown"],
        ["Energy Class", listing.energy_class],
        ["Asking Price", format_currency(listing.price)],
        ["Price / m2", format_price_per_sqm(listing.price_per_sqm)],
        ["Features", f"Balcony: {'Yes' if listing.balcony else 'No'}, Elevator: {'Yes' if listing.elevator else 'No'}, Garage: {'Yes' if listing.parking else 'No'}, Kitchen: {'Yes' if listing.fitted_kitchen else 'No'}"],
    ]
    print(tabulate(prop_table, tablefmt="fancy_grid"))

    print("\n" + "=" * 75)
    print(f" 0-100 DEAL SCORE: {score_card.overall_score:.1f} / 100")
    print(f" Verdict: {score_card.deal_verdict}")
    print("=" * 75)
    
    score_table = [
        ["Overall Score (0-100)", f"{score_card.overall_score:.1f} / 100", score_card.deal_verdict],
        ["1. Price Attractiveness (40%)", f"{score_card.price_score:.1f} / 100", f"Delta: {score_card.price_delta_pct:+.1f}% vs Fair Value"],
        ["2. Micro-Location (25%)", f"{score_card.location_score:.1f} / 100", "Center, Transit, Campus"],
        ["3. Quality & Energy (20%)", f"{score_card.quality_energy_score:.1f} / 100", f"Class {listing.energy_class}, Built {listing.build_year or 'N/A'}"],
        ["4. Space & Layout (15%)", f"{score_card.layout_space_score:.1f} / 100", f"{listing.living_space_sqm/max(1.0, listing.rooms):.1f} m2/Room + Amenities"],
    ]
    print(tabulate(score_table, headers=["Category", "Score", "Details"], tablefmt="fancy_grid"))

    print("\n" + "=" * 75)
    print(" FINANCIAL VALUATION & MARKET ANALYSIS")
    print("=" * 75)
    val_table = [
        ["Asking Price", format_currency(listing.price), format_price_per_sqm(listing.price_per_sqm)],
        ["Estimated Fair Market Value", format_currency(prediction.predicted_fair_price), format_price_per_sqm(prediction.price_per_sqm_predicted)],
        ["90% Confidence Interval", f"{format_currency(prediction.lower_bound)} - {format_currency(prediction.upper_bound)}", "Statistical Band"],
        ["Recommended Offer Price", format_currency(score_card.recommended_offer_price), f"Negotiation Margin: {format_currency(score_card.negotiation_potential_eur)}"],
    ]
    print(tabulate(val_table, headers=["Metric", "Total Value", "Per m2 / Note"], tablefmt="fancy_grid"))

    print("\n" + "=" * 75)
    print(" STRENGTHS, WEAKNESSES & NEGOTIATION ADVICE")
    print("=" * 75)
    print("STRENGTHS (PROS):")
    for p in score_card.pros:
        print(f"  - {p}")
    if score_card.cons:
        print("\nWEAKNESSES (CONS):")
        for c in score_card.cons:
            print(f"  - {c}")
    print("\nNEGOTIATION RECOMMENDATION:")
    for t in score_card.negotiation_tips:
        print(f"  - {t}")
    print("=" * 75 + "\n")

if __name__ == "__main__":
    main()
