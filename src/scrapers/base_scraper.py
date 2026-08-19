"""
Base models and dataclasses for real estate listings.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any

@dataclass
class PropertyListing:
    title: str
    city: str
    district: str
    price: float  # Total purchase price in EUR
    living_space_sqm: float
    rooms: float
    build_year: Optional[int] = None
    energy_class: Optional[str] = "UNKNOWN"
    property_type: str = "Wohnung"  # Wohnung, Haus, Penthouse, Maisonette, Villa, etc.
    condition: str = "Gepflegt"     # Erstbezug, Neuwertig, Saniert, Gepflegt, Modernisierungsbedürftig, etc.
    balcony: bool = False
    garden: bool = False
    elevator: bool = False
    fitted_kitchen: bool = False   # Einbauküche (EBK)
    parking: bool = False          # Garage / Tiefgarage / Stellplatz
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    postal_code: Optional[str] = None
    url: Optional[str] = None
    source: str = "Manual / Scraper"
    description: Optional[str] = ""

    @property
    def price_per_sqm(self) -> float:
        if self.living_space_sqm and self.living_space_sqm > 0:
            return round(self.price / self.living_space_sqm, 2)
        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "city": self.city,
            "district": self.district,
            "postal_code": self.postal_code,
            "price": self.price,
            "living_space_sqm": self.living_space_sqm,
            "price_per_sqm": self.price_per_sqm,
            "rooms": self.rooms,
            "build_year": self.build_year,
            "energy_class": self.energy_class,
            "property_type": self.property_type,
            "condition": self.condition,
            "balcony": int(self.balcony),
            "garden": int(self.garden),
            "elevator": int(self.elevator),
            "fitted_kitchen": int(self.fitted_kitchen),
            "parking": int(self.parking),
            "latitude": self.latitude,
            "longitude": self.longitude,
            "url": self.url,
            "source": self.source,
        }
