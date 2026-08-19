"""
Registry of German cities with geo-coordinates, districts, points of interest,
and calibrated baseline price benchmarks (€/m²).
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

@dataclass
class DistrictInfo:
    name: str
    lat_offset: float  # Offset from city center lat
    lon_offset: float  # Offset from city center lon
    prestige_multiplier: float  # 0.85 = budget, 1.0 = average, 1.25 = prime
    typical_property_types: List[str] = field(default_factory=lambda: ["Wohnung", "Haus"])

@dataclass
class CityProfile:
    name: str
    state: str
    postal_codes: List[str]
    center_lat: float
    center_lon: float
    radius_km: float
    base_price_per_sqm: float  # Current 2026 market baseline €/m²
    historical_price_2018: float
    historical_peak_2022: float
    historical_trough_2024: float
    rental_yield_pct: float    # Gross rental yield %
    train_station_lat: float
    train_station_lon: float
    university_lat: Optional[float] = None
    university_lon: Optional[float] = None
    districts: List[DistrictInfo] = field(default_factory=list)

# Comprehensive German City Catalog
GERMAN_CITIES: Dict[str, CityProfile] = {
    "Deggendorf": CityProfile(
        name="Deggendorf",
        state="Bayern",
        postal_codes=["94469"],
        center_lat=48.8353,
        center_lon=12.9642,
        radius_km=4.5,
        base_price_per_sqm=3650.0,
        historical_price_2018=2750.0,
        historical_peak_2022=4100.0,
        historical_trough_2024=3450.0,
        rental_yield_pct=4.4,
        train_station_lat=48.8315,
        train_station_lon=12.9567,
        university_lat=48.8300,  # Technische Hochschule Deggendorf (THD / DIT)
        university_lon=12.9540,
        districts=[
            DistrictInfo("Altstadt / Zentrum", 0.000, 0.000, 1.15),
            DistrictInfo("Schaching", -0.006, -0.008, 1.05),
            DistrictInfo("Fischerdorf", -0.015, -0.005, 0.95),
            DistrictInfo("Mietraching", 0.020, 0.012, 1.02),
            DistrictInfo("Deggenau", -0.012, 0.028, 0.92),
            DistrictInfo("Natternberg", -0.022, -0.025, 0.96),
            DistrictInfo("Seebach", -0.025, 0.018, 0.90),
            DistrictInfo("Rettenbach", 0.028, -0.015, 0.93),
        ]
    ),
    "Passau": CityProfile(
        name="Passau",
        state="Bayern",
        postal_codes=["94032", "94034", "94036"],
        center_lat=48.5735,
        center_lon=13.4637,
        radius_km=5.5,
        base_price_per_sqm=3950.0,
        historical_price_2018=2950.0,
        historical_peak_2022=4450.0,
        historical_trough_2024=3750.0,
        rental_yield_pct=4.6,
        train_station_lat=48.5731,
        train_station_lon=13.4508,
        university_lat=48.5670,  # Universität Passau (Innrain)
        university_lon=13.4530,
        districts=[
            DistrictInfo("Altstadt", 0.000, 0.005, 1.20),
            DistrictInfo("Innstadt", -0.008, 0.008, 1.08),
            DistrictInfo("Haidenhof Nord", 0.005, -0.018, 1.00),
            DistrictInfo("Haidenhof Süd", -0.005, -0.015, 1.04),
            DistrictInfo("Ilzstadt", 0.012, 0.010, 0.92),
            DistrictInfo("Hacklberg", 0.018, -0.010, 1.05),
            DistrictInfo("Grubweg", 0.015, 0.030, 0.90),
            DistrictInfo("Heining", -0.010, -0.040, 0.92),
            DistrictInfo("Hals", 0.035, 0.008, 0.88),
        ]
    ),
    "Regensburg": CityProfile(
        name="Regensburg",
        state="Bayern",
        postal_codes=["93047", "93049", "93051", "93053", "93055", "93057", "93059"],
        center_lat=49.0134,
        center_lon=12.1016,
        radius_km=6.5,
        base_price_per_sqm=5350.0,
        historical_price_2018=4100.0,
        historical_peak_2022=6100.0,
        historical_trough_2024=5100.0,
        rental_yield_pct=3.9,
        train_station_lat=49.0117,
        train_station_lon=12.0989,
        university_lat=48.9980,  # Universität Regensburg / OTH
        university_lon=12.0950,
        districts=[
            DistrictInfo("Innenstadt / Altstadt", 0.000, 0.000, 1.25),
            DistrictInfo("Stadtamhof", 0.010, -0.005, 1.22),
            DistrictInfo("Westenviertel", 0.002, -0.020, 1.10),
            DistrictInfo("Kumpfmühl", -0.012, -0.015, 1.05),
            DistrictInfo("Galgenberg", -0.015, 0.005, 1.08),
            DistrictInfo("Kasernenviertel", -0.010, 0.020, 0.95),
            DistrictInfo("Reinhausen", 0.018, 0.015, 0.96),
            DistrictInfo("Burgweinting", -0.030, 0.045, 0.92),
            DistrictInfo("Konradsiedlung", 0.025, 0.030, 0.91),
        ]
    ),
    "München": CityProfile(
        name="München",
        state="Bayern",
        postal_codes=["80331", "80333", "80335", "80538", "80539", "80799", "80801", "80802", "81675"],
        center_lat=48.1351,
        center_lon=11.5820,
        radius_km=12.0,
        base_price_per_sqm=9450.0,
        historical_price_2018=7600.0,
        historical_peak_2022=10800.0,
        historical_trough_2024=8950.0,
        rental_yield_pct=3.1,
        train_station_lat=48.1402,
        train_station_lon=11.5583,
        university_lat=48.1508,  # LMU / TUM Maxvorstadt
        university_lon=11.5802,
        districts=[
            DistrictInfo("Altstadt-Lehel", 0.000, 0.005, 1.35),
            DistrictInfo("Maxvorstadt", 0.015, -0.005, 1.25),
            DistrictInfo("Schwabing", 0.030, 0.005, 1.28),
            DistrictInfo("Bogenhausen", 0.020, 0.040, 1.25),
            DistrictInfo("Glockenbach / Isarvorstadt", -0.010, -0.005, 1.22),
            DistrictInfo("Neuhausen-Nymphenburg", 0.015, -0.045, 1.15),
            DistrictInfo("Sendling", -0.025, -0.030, 1.05),
            DistrictInfo("Haidhausen", -0.005, 0.030, 1.20),
            DistrictInfo("Pasing", 0.010, -0.120, 0.95),
            DistrictInfo("Giesing", -0.035, 0.015, 0.98),
            DistrictInfo("Trudering", -0.020, 0.090, 0.92),
            DistrictInfo("Moosach", 0.045, -0.055, 0.90),
        ]
    ),
    "Nürnberg": CityProfile(
        name="Nürnberg",
        state="Bayern",
        postal_codes=["90402", "90403", "90408", "90409", "90419", "90429", "90443"],
        center_lat=49.4521,
        center_lon=11.0767,
        radius_km=8.0,
        base_price_per_sqm=4450.0,
        historical_price_2018=3400.0,
        historical_peak_2022=5150.0,
        historical_trough_2024=4200.0,
        rental_yield_pct=4.2,
        train_station_lat=49.4456,
        train_station_lon=11.0827,
        university_lat=49.4560,
        university_lon=11.0820,
        districts=[
            DistrictInfo("Altstadt", 0.000, 0.000, 1.20),
            DistrictInfo("St. Johannis", 0.010, -0.015, 1.15),
            DistrictInfo("Erlenstegen", 0.020, 0.040, 1.22),
            DistrictInfo("Gostenhof (GoHo)", -0.005, -0.020, 1.02),
            DistrictInfo("Mögeldorf", 0.010, 0.050, 1.10),
            DistrictInfo("Südstadt", -0.025, 0.000, 0.88),
            DistrictInfo("Nordstadt", 0.020, 0.005, 1.06),
        ]
    ),
    "Straubing": CityProfile(
        name="Straubing",
        state="Bayern",
        postal_codes=["94315"],
        center_lat=48.8817,
        center_lon=12.5733,
        radius_km=4.5,
        base_price_per_sqm=3450.0,
        historical_price_2018=2600.0,
        historical_peak_2022=3900.0,
        historical_trough_2024=3250.0,
        rental_yield_pct=4.5,
        train_station_lat=48.8770,
        train_station_lon=12.5690,
        university_lat=48.8850,  # TUM Campus Straubing
        university_lon=12.5850,
        districts=[
            DistrictInfo("Stadtzentrum", 0.000, 0.000, 1.12),
            DistrictInfo("Ittling", 0.010, 0.040, 0.95),
            DistrictInfo("Alburg", -0.010, -0.035, 0.96),
            DistrictInfo("Kagers", 0.015, -0.010, 0.98),
            DistrictInfo("Süd", -0.020, 0.005, 0.92),
        ]
    ),
    "Landshut": CityProfile(
        name="Landshut",
        state="Bayern",
        postal_codes=["84028", "84030", "84032", "84034", "84036"],
        center_lat=48.5369,
        center_lon=12.1522,
        radius_km=5.0,
        base_price_per_sqm=4650.0,
        historical_price_2018=3550.0,
        historical_peak_2022=5350.0,
        historical_trough_2024=4400.0,
        rental_yield_pct=4.1,
        train_station_lat=48.5470,
        train_station_lon=12.1430,
        university_lat=48.5490,  # Hochschule Landshut
        university_lon=12.1850,
        districts=[
            DistrictInfo("Altstadt", 0.000, 0.000, 1.20),
            DistrictInfo("Nikola", 0.010, -0.008, 1.05),
            DistrictInfo("Achdorf", -0.015, -0.010, 1.04),
            DistrictInfo("Wolfgang", 0.018, 0.010, 0.95),
            DistrictInfo("Berg / Hofgarten", -0.010, 0.008, 1.15),
            DistrictInfo("Frauenberg", 0.015, 0.035, 0.90),
        ]
    ),
    "Berlin": CityProfile(
        name="Berlin",
        state="Berlin",
        postal_codes=["10115", "10117", "10119", "10435", "10437", "10969", "10999", "10719"],
        center_lat=52.5200,
        center_lon=13.4050,
        radius_km=15.0,
        base_price_per_sqm=5850.0,
        historical_price_2018=4400.0,
        historical_peak_2022=6700.0,
        historical_trough_2024=5500.0,
        rental_yield_pct=3.8,
        train_station_lat=52.5251,
        train_station_lon=13.3694,
        university_lat=52.5180,  # HU / TU Berlin
        university_lon=13.3930,
        districts=[
            DistrictInfo("Mitte", 0.000, 0.000, 1.30),
            DistrictInfo("Prenzlauer Berg", 0.020, 0.015, 1.22),
            DistrictInfo("Charlottenburg", 0.005, -0.080, 1.20),
            DistrictInfo("Kreuzberg", -0.025, 0.010, 1.15),
            DistrictInfo("Friedrichshain", -0.010, 0.050, 1.12),
            DistrictInfo("Schöneberg", -0.035, -0.050, 1.08),
            DistrictInfo("Neukölln", -0.050, 0.030, 0.98),
            DistrictInfo("Pankow", 0.055, 0.020, 1.02),
            DistrictInfo("Spandau", 0.020, -0.180, 0.85),
            DistrictInfo("Marzahn", 0.030, 0.150, 0.78),
        ]
    ),
    "Hamburg": CityProfile(
        name="Hamburg",
        state="Hamburg",
        postal_codes=["20095", "20148", "20249", "20354", "22303", "22767"],
        center_lat=53.5511,
        center_lon=9.9937,
        radius_km=12.0,
        base_price_per_sqm=6250.0,
        historical_price_2018=4800.0,
        historical_peak_2022=7200.0,
        historical_trough_2024=5950.0,
        rental_yield_pct=3.6,
        train_station_lat=53.5530,
        train_station_lon=10.0067,
        university_lat=53.5630,
        university_lon=9.9840,
        districts=[
            DistrictInfo("HafenCity / Altstadt", 0.000, 0.000, 1.35),
            DistrictInfo("Rotherbaum / Harvestehude", 0.020, -0.005, 1.30),
            DistrictInfo("Eppendorf", 0.040, -0.005, 1.25),
            DistrictInfo("Winterhude", 0.045, 0.015, 1.20),
            DistrictInfo("Altona / Ottensen", 0.005, -0.060, 1.15),
            DistrictInfo("Eimsbüttel", 0.025, -0.040, 1.12),
            DistrictInfo("St. Pauli", -0.005, -0.035, 1.05),
            DistrictInfo("Wandsbek", 0.020, 0.080, 0.92),
            DistrictInfo("Harburg", -0.090, -0.020, 0.82),
        ]
    ),
    "Frankfurt am Main": CityProfile(
        name="Frankfurt am Main",
        state="Hessen",
        postal_codes=["60311", "60313", "60322", "60325", "60594"],
        center_lat=50.1109,
        center_lon=8.6821,
        radius_km=10.0,
        base_price_per_sqm=6950.0,
        historical_price_2018=5400.0,
        historical_peak_2022=8100.0,
        historical_trough_2024=6600.0,
        rental_yield_pct=3.7,
        train_station_lat=50.1070,
        train_station_lon=8.6630,
        university_lat=50.1260,
        university_lon=8.6660,
        districts=[
            DistrictInfo("Westend", 0.015, -0.015, 1.35),
            DistrictInfo("Innenstadt / Bankenviertel", 0.000, 0.000, 1.28),
            DistrictInfo("Nordend", 0.020, 0.010, 1.22),
            DistrictInfo("Sachsenhausen", -0.015, 0.010, 1.18),
            DistrictInfo("Bornheim", 0.018, 0.035, 1.10),
            DistrictInfo("Bockenheim", 0.015, -0.035, 1.08),
            DistrictInfo("Ostend", 0.005, 0.040, 1.05),
            DistrictInfo("Gallus", 0.000, -0.040, 0.96),
        ]
    ),
    "Köln": CityProfile(
        name="Köln",
        state="Nordrhein-Westfalen",
        postal_codes=["50667", "50672", "50677", "50931", "50823"],
        center_lat=50.9375,
        center_lon=6.9603,
        radius_km=11.0,
        base_price_per_sqm=5150.0,
        historical_price_2018=3950.0,
        historical_peak_2022=5950.0,
        historical_trough_2024=4900.0,
        rental_yield_pct=4.0,
        train_station_lat=50.9432,
        train_station_lon=6.9586,
        university_lat=50.9280,
        university_lon=6.9290,
        districts=[
            DistrictInfo("Altstadt / Innenstadt", 0.000, 0.000, 1.22),
            DistrictInfo("Lindenthal", -0.015, -0.045, 1.25),
            DistrictInfo("Ehrenfeld", 0.015, -0.040, 1.12),
            DistrictInfo("Belgisches Viertel", 0.002, -0.020, 1.24),
            DistrictInfo("Nippes", 0.030, -0.010, 1.05),
            DistrictInfo("Sülz", -0.025, -0.035, 1.15),
            DistrictInfo("Deutz", -0.005, 0.025, 1.02),
            DistrictInfo("Mülheim", 0.035, 0.045, 0.90),
            DistrictInfo("Chorweiler", 0.080, -0.010, 0.78),
        ]
    ),
    "Stuttgart": CityProfile(
        name="Stuttgart",
        state="Baden-Württemberg",
        postal_codes=["70173", "70178", "70182", "70569", "70372"],
        center_lat=48.7758,
        center_lon=9.1829,
        radius_km=10.0,
        base_price_per_sqm=5650.0,
        historical_price_2018=4450.0,
        historical_peak_2022=6550.0,
        historical_trough_2024=5400.0,
        rental_yield_pct=3.8,
        train_station_lat=48.7840,
        train_station_lon=9.1810,
        university_lat=48.7450,
        university_lon=9.1060,
        districts=[
            DistrictInfo("Stuttgart-Mitte", 0.000, 0.000, 1.24),
            DistrictInfo("Stuttgart-Süd", -0.015, -0.005, 1.14),
            DistrictInfo("Degerloch", -0.030, -0.010, 1.22),
            DistrictInfo("Stuttgart-West", 0.005, -0.025, 1.18),
            DistrictInfo("Bad Cannstatt", 0.030, 0.035, 0.98),
            DistrictInfo("Vaihingen", -0.045, -0.060, 1.05),
        ]
    ),
    "Leipzig": CityProfile(
        name="Leipzig",
        state="Sachsen",
        postal_codes=["04109", "04103", "04229", "04275", "04155"],
        center_lat=51.3397,
        center_lon=12.3731,
        radius_km=9.0,
        base_price_per_sqm=3350.0,
        historical_price_2018=2350.0,
        historical_peak_2022=3850.0,
        historical_trough_2024=3150.0,
        rental_yield_pct=4.7,
        train_station_lat=51.3450,
        train_station_lon=12.3810,
        university_lat=51.3380,
        university_lon=12.3790,
        districts=[
            DistrictInfo("Zentrum", 0.000, 0.000, 1.20),
            DistrictInfo("Schleußig", -0.020, -0.035, 1.18),
            DistrictInfo("Südvorstadt", -0.025, -0.005, 1.15),
            DistrictInfo("Plagwitz", -0.010, -0.050, 1.10),
            DistrictInfo("Gohlis", 0.030, -0.015, 1.12),
            DistrictInfo("Reudnitz", -0.005, 0.030, 0.96),
            DistrictInfo("Grünau", -0.025, -0.095, 0.78),
        ]
    ),
}

# Aliases and normalization mapping
CITY_ALIASES = {
    "munich": "München",
    "muenchen": "München",
    "münchen": "München",
    "nuremberg": "Nürnberg",
    "nuernberg": "Nürnberg",
    "nürnberg": "Nürnberg",
    "cologne": "Köln",
    "koeln": "Köln",
    "köln": "Köln",
    "deggendorf": "Deggendorf",
    "passau": "Passau",
    "regensburg": "Regensburg",
    "straubing": "Straubing",
    "landshut": "Landshut",
    "berlin": "Berlin",
    "hamburg": "Hamburg",
    "frankfurt": "Frankfurt am Main",
    "frankfurt am main": "Frankfurt am Main",
    "stuttgart": "Stuttgart",
    "leipzig": "Leipzig",
}

def get_city_profile(city_name: str) -> CityProfile:
    """
    Retrieves or dynamically creates a profile for any German city.
    """
    normalized = city_name.strip().lower()
    canonical_name = CITY_ALIASES.get(normalized, city_name.strip().title())
    
    if canonical_name in GERMAN_CITIES:
        return GERMAN_CITIES[canonical_name]
    
    # Fallback dynamic profile for any other German town
    return CityProfile(
        name=canonical_name,
        state="Deutschland",
        postal_codes=["00000"],
        center_lat=48.8000,
        center_lon=12.0000,
        radius_km=5.0,
        base_price_per_sqm=3800.0,
        historical_price_2018=2800.0,
        historical_peak_2022=4300.0,
        historical_trough_2024=3600.0,
        rental_yield_pct=4.3,
        train_station_lat=48.8000,
        train_station_lon=12.0000,
        districts=[
            DistrictInfo("Zentrum", 0.000, 0.000, 1.15),
            DistrictInfo("Nord", 0.015, 0.000, 1.00),
            DistrictInfo("Süd", -0.015, 0.000, 0.98),
            DistrictInfo("Ost", 0.000, 0.015, 0.95),
            DistrictInfo("West", 0.000, -0.015, 1.02),
        ]
    )

def list_available_cities() -> List[str]:
    """Returns list of pre-configured featured German cities."""
    return list(GERMAN_CITIES.keys())
