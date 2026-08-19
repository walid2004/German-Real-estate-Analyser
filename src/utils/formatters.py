"""
Formatters for German real estate numbers, currencies, and energy ratings.
"""

from typing import Union

def format_currency(value: Union[int, float], symbol: str = "€") -> str:
    """Formats a number as German currency string, e.g. 345.000 €"""
    if value is None:
        return "N/A"
    return f"{value:,.0f} {symbol}".replace(",", ".")

def format_price_per_sqm(value: Union[int, float]) -> str:
    """Formats price per square meter, e.g. 4.250 €/m²"""
    if value is None:
        return "N/A"
    return f"{value:,.0f} €/m²".replace(",", ".")

def format_sqm(value: Union[int, float]) -> str:
    """Formats area in square meters, e.g. 85,5 m²"""
    if value is None:
        return "N/A"
    return f"{value:,.1f} m²".replace(".", ",")

def get_energy_color(energy_class: str) -> str:
    """Returns color hex code corresponding to German energy certificate class."""
    colors = {
        "A+": "#008000", # Dark Green
        "A":  "#2ECC71", # Green
        "B":  "#82E0AA", # Light Green
        "C":  "#F4D03F", # Yellow-Green
        "D":  "#F39C12", # Yellow-Orange
        "E":  "#E67E22", # Orange
        "F":  "#D35400", # Dark Orange
        "G":  "#E74C3C", # Red
        "H":  "#922B21", # Dark Red
        "UNKNOWN": "#95A5A6" # Gray
    }
    return colors.get(str(energy_class).upper(), "#95A5A6")
