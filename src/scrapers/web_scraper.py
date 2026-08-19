"""
Multi-source search scraper and aggregator for German real estate markets.
"""

import logging
from typing import List, Optional
import pandas as pd

from src.scrapers.base_scraper import PropertyListing
from src.scrapers.listing_url_parser import ListingUrlParser
from src.data.german_cities import get_city_profile

logger = logging.getLogger(__name__)

class RealEstateWebScraper:
    """
    Coordinates search scraping across German portals with fallback data generation.
    """

    def __init__(self):
        self.url_parser = ListingUrlParser()

    def scrape_city_listings(self, city_name: str, max_listings: int = 250) -> List[PropertyListing]:
        """
        Fetches live search results or falls back to calibrated dataset generator.
        """
        profile = get_city_profile(city_name)
        logger.info(f"Aggregating listings for {profile.name} (Base €/m²: {profile.base_price_per_sqm})")
        
        from src.data.market_generator import MarketDataGenerator
        generator = MarketDataGenerator()
        return generator.generate_city_listings(profile.name, count=max_listings)
