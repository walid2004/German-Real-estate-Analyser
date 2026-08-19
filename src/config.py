from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data_cache"
MODELS_DIR = BASE_DIR / "models_cache"

DATA_DIR.mkdir(exist_ok=True, parents=True)
MODELS_DIR.mkdir(exist_ok=True, parents=True)

CURRENT_YEAR = 2026
HISTORICAL_START_YEAR = 2018

ENERGY_CLASSES = ["A+", "A", "B", "C", "D", "E", "F", "G", "H"]
ENERGY_CLASS_SCORES = {
    "A+": 100,
    "A": 90,
    "B": 80,
    "C": 70,
    "D": 55,
    "E": 40,
    "F": 30,
    "G": 15,
    "H": 0,
    "UNKNOWN": 50,
}

CONDITION_SCORES = {
    "Erstbezug": 100,
    "Neuwertig": 90,
    "Vollständig renoviert": 85,
    "Saniert": 80,
    "Gepflegt": 70,
    "Modernisierungsbedürftig": 40,
    "Renovierungsbedürftig": 25,
    "Abbruchreif": 5,
    "UNKNOWN": 65,
}

DEFAULT_WEIGHTS = {
    "price_value": 0.40,
    "micro_location": 0.25,
    "quality_energy": 0.20,
    "layout_efficiency": 0.15,
}
