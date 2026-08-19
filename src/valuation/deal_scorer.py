import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

from src.scrapers.base_scraper import PropertyListing
from src.ml.valuation_model import ValuationPrediction
from src.config import ENERGY_CLASS_SCORES, CONDITION_SCORES, DEFAULT_WEIGHTS
from src.data.german_cities import get_city_profile
from src.utils.geo_utils import haversine_distance_km, calculate_micro_location_score

@dataclass
class ScoreBreakdown:
    overall_score: float
    deal_verdict: str
    deal_verdict_de: str
    price_score: float
    location_score: float
    quality_energy_score: float
    layout_space_score: float
    
    asking_price: float
    fair_market_price: float
    price_delta_pct: float
    recommended_offer_price: float
    negotiation_potential_eur: float
    
    pros: List[str]
    cons: List[str]
    negotiation_tips: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": round(self.overall_score, 1),
            "deal_verdict": self.deal_verdict,
            "deal_verdict_de": self.deal_verdict_de,
            "price_score": round(self.price_score, 1),
            "location_score": round(self.location_score, 1),
            "quality_energy_score": round(self.quality_energy_score, 1),
            "layout_space_score": round(self.layout_space_score, 1),
            "asking_price": round(self.asking_price, 2),
            "fair_market_price": round(self.fair_market_price, 2),
            "price_delta_pct": round(self.price_delta_pct, 2),
            "recommended_offer_price": round(self.recommended_offer_price, 2),
            "negotiation_potential_eur": round(self.negotiation_potential_eur, 2),
            "pros": self.pros,
            "cons": self.cons,
            "negotiation_tips": self.negotiation_tips,
        }

class DealScoringEngine:
    """
    Computes a 0-100 evaluation score and negotiation breakdown for a property.
    """

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or DEFAULT_WEIGHTS

    def evaluate_deal(self, listing: PropertyListing, prediction: ValuationPrediction) -> ScoreBreakdown:
        profile = get_city_profile(listing.city)
        pros = []
        cons = []
        tips = []

        fair_price = prediction.predicted_fair_price
        asking_price = listing.price
        discount_pct = ((fair_price - asking_price) / fair_price) * 100.0 if fair_price > 0 else 0.0

        price_score = float(np.clip(75.0 + (discount_pct * 1.4), 0.0, 100.0))

        if discount_pct >= 8.0:
            pros.append(f"Below market value: Asking price is {discount_pct:.1f}% below estimated fair value.")
        elif discount_pct <= -8.0:
            cons.append(f"Above market value: Asking price is {abs(discount_pct):.1f}% above estimated fair value.")
            tips.append(f"Price negotiation: Target a reduction of at least {abs(discount_pct):.1f}%.")
        else:
            pros.append("Fair market pricing consistent with recent regional comparables.")

        lat = listing.latitude or profile.center_lat
        lon = listing.longitude or profile.center_lon
        
        dist_center = haversine_distance_km(lat, lon, profile.center_lat, profile.center_lon)
        dist_transit = haversine_distance_km(lat, lon, profile.train_station_lat, profile.train_station_lon)
        dist_uni = haversine_distance_km(lat, lon, profile.university_lat, profile.university_lon) if profile.university_lat else None

        district_prestige = 1.0
        for d in profile.districts:
            if d.name.lower() in listing.district.lower():
                district_prestige = d.prestige_multiplier
                break

        location_score = calculate_micro_location_score(
            dist_center, dist_transit, dist_uni, district_prestige, city_radius_km=profile.radius_km
        )

        if dist_center <= 1.5:
            pros.append(f"Central location: {dist_center:.1f} km to city center.")
        elif dist_center > 4.0:
            cons.append(f"Outskirts location: {dist_center:.1f} km to city center.")
            tips.append("Verify public transit connection frequency.")

        if dist_uni and dist_uni <= 1.8:
            pros.append(f"High rental demand location: {dist_uni:.1f} km to campus.")

        energy_score = ENERGY_CLASS_SCORES.get(str(listing.energy_class).upper(), 50)
        condition_score = CONDITION_SCORES.get(listing.condition, 70)
        
        if listing.build_year:
            if listing.build_year >= 2020:
                age_score = 95.0
                pros.append(f"Modern new build (Year {listing.build_year}) with updated building systems.")
            elif listing.build_year >= 2010:
                age_score = 85.0
                pros.append(f"Recent construction (Year {listing.build_year}).")
            elif listing.build_year >= 1995:
                age_score = 75.0
            elif listing.build_year >= 1970:
                age_score = 60.0
            elif listing.build_year < 1945:
                age_score = 82.0 if listing.condition in ["Saniert", "Vollständig renoviert"] else 45.0
                if listing.condition in ["Saniert", "Vollständig renoviert"]:
                    pros.append("Renovated historic building.")
                else:
                    cons.append("Historic building requiring renovation.")
                    tips.append("Inspect maintenance reserve fund and upcoming facade/roof repairs.")
            else:
                age_score = 65.0
        else:
            age_score = 65.0

        if str(listing.energy_class).upper() in ["A+", "A", "B"]:
            pros.append(f"High energy efficiency (Class {listing.energy_class}) resulting in lower operating costs.")
        elif str(listing.energy_class).upper() in ["F", "G", "H"]:
            cons.append(f"Low energy efficiency (Class {listing.energy_class}) with potential heating upgrade requirements.")
            tips.append("Use heating system modernization costs as leverage during negotiations.")

        quality_energy_score = float(0.40 * energy_score + 0.35 * age_score + 0.25 * condition_score)

        rooms = max(1.0, float(listing.rooms))
        sqm = max(15.0, float(listing.living_space_sqm))
        sqm_per_room = sqm / rooms

        if 22.0 <= sqm_per_room <= 38.0:
            layout_base = 85.0
        elif 18.0 <= sqm_per_room < 22.0 or 38.0 < sqm_per_room <= 50.0:
            layout_base = 72.0
        else:
            layout_base = 55.0

        amenities_pts = 0.0
        if listing.balcony:
            amenities_pts += 15.0
            pros.append("Balcony or terrace included.")
        if listing.elevator:
            amenities_pts += 15.0
            pros.append("Elevator access available.")
        if listing.parking:
            amenities_pts += 15.0
            pros.append("Dedicated parking space or garage included.")
        if listing.fitted_kitchen:
            amenities_pts += 10.0
            pros.append("Fitted kitchen included.")
        if listing.garden:
            amenities_pts += 15.0
            pros.append("Private garden area included.")

        layout_space_score = float(np.clip(layout_base * 0.40 + amenities_pts * 0.85, 0.0, 100.0))

        w_price = self.weights["price_value"]
        w_loc = self.weights["micro_location"]
        w_qual = self.weights["quality_energy"]
        w_lay = self.weights["layout_efficiency"]

        overall_score = (
            w_price * price_score +
            w_loc * location_score +
            w_qual * quality_energy_score +
            w_lay * layout_space_score
        )
        overall_score = float(np.clip(overall_score, 0.0, 100.0))

        if overall_score >= 86.0:
            verdict_en = "Top Deal / Strong Buy"
            verdict_de = "Hervorragendes Angebot (Top Deal)"
        elif overall_score >= 72.0:
            verdict_en = "Good Value / Buy"
            verdict_de = "Gutes Angebot (Attraktiver Kauf)"
        elif overall_score >= 55.0:
            verdict_en = "Fair Price / Negotiate"
            verdict_de = "Marktgerecht (Verhandlungsbasis)"
        elif overall_score >= 40.0:
            verdict_en = "Overpriced / Needs Discount"
            verdict_de = "Leicht Ueberteuert (Nachverhandeln)"
        else:
            verdict_en = "High Risk / Significantly Overpriced"
            verdict_de = "Stark Ueberteuert / Hohes Risiko"

        if asking_price > fair_price:
            recommended_offer = min(asking_price, fair_price * 0.96)
        else:
            recommended_offer = min(asking_price, fair_price * 0.98)
            
        negotiation_potential = max(0.0, asking_price - recommended_offer)

        if not tips:
            tips.append("Request HOA meeting minutes and maintenance reserve reports.")

        return ScoreBreakdown(
            overall_score=overall_score,
            deal_verdict=verdict_en,
            deal_verdict_de=verdict_de,
            price_score=price_score,
            location_score=location_score,
            quality_energy_score=quality_energy_score,
            layout_space_score=layout_space_score,
            asking_price=asking_price,
            fair_market_price=fair_price,
            price_delta_pct=discount_pct,
            recommended_offer_price=recommended_offer,
            negotiation_potential_eur=negotiation_potential,
            pros=pros,
            cons=cons,
            negotiation_tips=tips
        )
