"""
Data loader and cache manager for German real estate datasets.
"""

import pandas as pd
from pathlib import Path
from typing import List, Tuple

from src.scrapers.base_scraper import PropertyListing
from src.data.german_cities import get_city_profile, list_available_cities
from src.data.market_generator import MarketDataGenerator
from src.config import DATA_DIR

class DataLoader:
    """
    Manages loading, caching, and querying city real estate datasets.
    """

    def __init__(self):
        self.generator = MarketDataGenerator()

    def get_city_dataset(self, city_name: str, force_refresh: bool = False) -> pd.DataFrame:
        """
        Returns active listings dataframe for the specified city, using cache if available.
        """
        profile = get_city_profile(city_name)
        cache_file = DATA_DIR / f"listings_{profile.name.lower()}.csv"

        if cache_file.exists() and not force_refresh:
            df = pd.read_csv(cache_file)
            return df

        listings = self.generator.generate_city_listings(profile.name, count=300)
        df = pd.DataFrame([l.to_dict() for l in listings])
        df.to_csv(cache_file, index=False)
        return df

    def get_city_historical_trends(self, city_name: str, force_refresh: bool = False) -> pd.DataFrame:
        """
        Returns quarterly historical price trends dataframe for the specified city.
        """
        profile = get_city_profile(city_name)
        cache_file = DATA_DIR / f"trends_{profile.name.lower()}.csv"

        if cache_file.exists() and not force_refresh:
            df = pd.read_csv(cache_file)
            return df

        df = self.generator.generate_historical_trends(profile.name)
        df.to_csv(cache_file, index=False)
        return df
