"""
Geo-spatial utilities for German real estate analysis.
Provides Haversine distance calculation, coordinate offsets, and spatial scoring.
"""

import math
from typing import Tuple, Optional

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance in kilometers between two points
    on the Earth using the Haversine formula.
    """
    r = 6371.0  # Earth's radius in km

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    return r * c

def calculate_micro_location_score(
    distance_to_center_km: float,
    distance_to_transit_km: float,
    distance_to_university_km: Optional[float] = None,
    district_prestige: float = 1.0,
    city_radius_km: float = 5.0
) -> float:
    """
    Computes a micro-location quality score from 0 to 100.
    
    Parameters:
    - distance_to_center_km: Distance to city center/Altstadt.
    - distance_to_transit_km: Distance to main train station / S-Bahn / U-Bahn.
    - distance_to_university_km: Optional distance to nearest university/college.
    - district_prestige: Factor (0.7 to 1.3) representing neighborhood desirability.
    - city_radius_km: Typical radius of the urban zone for normalization.
    """
    # Proximity to center (closer is better, exponential decay)
    center_score = max(0.0, 100.0 * math.exp(-1.2 * (distance_to_center_km / max(1.0, city_radius_km))))
    
    # Proximity to transit (ideally within 1.5 km)
    transit_score = max(0.0, 100.0 * math.exp(-0.8 * distance_to_transit_km))
    
    # Proximity to university (especially relevant for student hubs like Passau, Deggendorf)
    if distance_to_university_km is not None:
        uni_score = max(0.0, 100.0 * math.exp(-0.6 * distance_to_university_km))
        base_score = 0.50 * center_score + 0.30 * transit_score + 0.20 * uni_score
    else:
        base_score = 0.65 * center_score + 0.35 * transit_score
        
    final_score = base_score * district_prestige
    return min(100.0, max(0.0, final_score))
