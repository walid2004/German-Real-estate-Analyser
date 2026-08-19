import re
import json
import logging
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlparse, unquote
import requests
from bs4 import BeautifulSoup

from src.scrapers.base_scraper import PropertyListing
from src.data.german_cities import get_city_profile, GERMAN_CITIES

logger = logging.getLogger(__name__)

SAMPLE_LISTINGS = {
    "muenchen_luxury_villa": PropertyListing(
        title="Repraesentative Luxusvilla in Bogenhausen mit Parkgrundstueck",
        city="München",
        district="Bogenhausen",
        price=2450000.0,
        living_space_sqm=265.0,
        rooms=7.0,
        build_year=2016,
        energy_class="A",
        property_type="Villa",
        condition="Neuwertig",
        balcony=True,
        garden=True,
        elevator=True,
        fitted_kitchen=True,
        parking=True,
        postal_code="81675",
        latitude=48.1480,
        longitude=11.6150,
        url="https://www.immobilienscout24.de/expose/sample-muenchen-villa-2450k",
        source="Sample: ImmoScout24 (Luxury)",
        description="Exklusive Villa mit grossem Garten, Doppelgarage und hochwertiger Ausstattung in bester Bogenhausen-Lage."
    ),
    "muenchen_schwabing": PropertyListing(
        title="Exklusives Penthouse in Schwabing mit Dachterrasse und Alpenblick",
        city="München",
        district="Schwabing",
        price=1180000.0,
        living_space_sqm=112.0,
        rooms=3.5,
        build_year=2018,
        energy_class="B",
        property_type="Penthouse",
        condition="Neuwertig",
        balcony=True,
        garden=False,
        elevator=True,
        fitted_kitchen=True,
        parking=True,
        postal_code="80801",
        latitude=48.1610,
        longitude=11.5870,
        url="https://www.immobilienscout24.de/expose/sample-muenchen-penthouse-1180k",
        source="Sample: ImmoScout24 (Penthouse)",
        description="Luxurioeses Penthouse mit Panorama-Dachterrasse und Tiefgaragenstellplatz in Schwabing."
    ),
    "regensburg_family_house": PropertyListing(
        title="Grosszuegiges Einfamilienhaus mit Sonnenterrasse und Garten in Burgweinting",
        city="Regensburg",
        district="Burgweinting",
        price=680000.0,
        living_space_sqm=158.0,
        rooms=5.0,
        build_year=2017,
        energy_class="A",
        property_type="Haus",
        condition="Neuwertig",
        balcony=True,
        garden=True,
        elevator=False,
        fitted_kitchen=True,
        parking=True,
        postal_code="93055",
        latitude=48.9880,
        longitude=12.1380,
        url="https://www.immowelt.de/expose/sample-regensburg-house-680k",
        source="Sample: Immowelt (House)",
        description="Modernes KfW-Effizienzhaus fuer Familien mit PV-Anlage, Waermepumpe und Garage."
    ),
    "regensburg_westenviertel": PropertyListing(
        title="Helle 3-Zimmer-Wohnung im Westenviertel nahe Stadtpark",
        city="Regensburg",
        district="Westenviertel",
        price=445000.0,
        living_space_sqm=84.0,
        rooms=3.0,
        build_year=2014,
        energy_class="B",
        property_type="Wohnung",
        condition="Gepflegt",
        balcony=True,
        garden=False,
        elevator=True,
        fitted_kitchen=True,
        parking=True,
        postal_code="93049",
        latitude=49.0150,
        longitude=12.0780,
        url="https://www.immowelt.de/expose/sample-regensburg-flat-445k",
        source="Sample: Immowelt (Apartment)",
        description="Ruhige und gepflegte Eigentumswohnung im beliebten Westenviertel."
    ),
    "passau_haidenhof": PropertyListing(
        title="Moderne 4-Zimmer-Familienwohnung mit Garten und Tiefgarage",
        city="Passau",
        district="Haidenhof Süd",
        price=410000.0,
        living_space_sqm=105.0,
        rooms=4.0,
        build_year=2021,
        energy_class="A+",
        property_type="Wohnung",
        condition="Erstbezug",
        balcony=True,
        garden=True,
        elevator=True,
        fitted_kitchen=True,
        parking=True,
        postal_code="94036",
        latitude=48.5670,
        longitude=13.4420,
        url="https://www.immobilienscout24.de/expose/sample-passau-410k",
        source="Sample: ImmoScout24 (New Build)",
        description="Neubau mit Waermepumpe, Fussbodenheizung und privatem Gartenanteil in Passau."
    ),
    "passau_innstadt": PropertyListing(
        title="Sanierte Altbauwohnung mit Inn-Blick und hohen Decken",
        city="Passau",
        district="Innstadt",
        price=335000.0,
        living_space_sqm=82.0,
        rooms=3.0,
        build_year=1910,
        energy_class="D",
        property_type="Wohnung",
        condition="Saniert",
        balcony=True,
        garden=False,
        elevator=False,
        fitted_kitchen=True,
        parking=False,
        postal_code="94032",
        latitude=48.5680,
        longitude=13.4680,
        url="https://www.kleinanzeigen.de/s-anzeige/sample-passau-altbau-335k",
        source="Sample: Kleinanzeigen (Altbau)",
        description="Charmanter Altbau mit Parkettboeden und modernen Baedern direkt an der Innbruecke."
    ),
    "deggendorf_top_deal": PropertyListing(
        title="Helle 3-Zimmer-Wohnung nahe THD mit Suedbalkon und Tiefgarage",
        city="Deggendorf",
        district="Schaching",
        price=275000.0,
        living_space_sqm=78.5,
        rooms=3.0,
        build_year=2019,
        energy_class="A",
        property_type="Wohnung",
        condition="Neuwertig",
        balcony=True,
        garden=False,
        elevator=True,
        fitted_kitchen=True,
        parking=True,
        postal_code="94469",
        latitude=48.8310,
        longitude=12.9570,
        url="https://www.immobilienscout24.de/expose/sample-deggendorf-deal-275k",
        source="Sample: ImmoScout24 (Top Deal)",
        description="Moderne Eigentumswohnung in ruhiger Lage, fußlaeufig zur TH Deggendorf und zum Donaupark."
    ),
    "deggendorf_altstadt": PropertyListing(
        title="Zentrale 2-Zimmer-Stadtwohnung am Stadtplatz Deggendorf",
        city="Deggendorf",
        district="Altstadt / Zentrum",
        price=215000.0,
        living_space_sqm=56.0,
        rooms=2.0,
        build_year=1995,
        energy_class="C",
        property_type="Wohnung",
        condition="Gepflegt",
        balcony=True,
        garden=False,
        elevator=False,
        fitted_kitchen=True,
        parking=False,
        postal_code="94469",
        latitude=48.8355,
        longitude=12.9645,
        url="https://www.immowelt.de/expose/sample-deggendorf-altstadt-215k",
        source="Sample: Immowelt (City Flat)",
        description="Eigentumswohnung direkt im historischen Stadtkern mit Einbaukueche."
    ),
    "berlin_zehlendorf_villa": PropertyListing(
        title="Klassische Stadtvilla in Berlin-Zehlendorf mit weitlaeufigem Garten",
        city="Berlin",
        district="Zehlendorf / Dahlem",
        price=1850000.0,
        living_space_sqm=235.0,
        rooms=6.5,
        build_year=2015,
        energy_class="B",
        property_type="Villa",
        condition="Neuwertig",
        balcony=True,
        garden=True,
        elevator=False,
        fitted_kitchen=True,
        parking=True,
        postal_code="14195",
        latitude=52.4350,
        longitude=13.2650,
        url="https://www.immobilienscout24.de/expose/sample-berlin-villa-1850k",
        source="Sample: ImmoScout24 (Villa)",
        description="Architektenvilla in ruhiger Villenkolonie mit Kamin und Doppelgarage."
    ),
    "frankfurt_westend_loft": PropertyListing(
        title="Design-Loft im Frankfurter Westend mit Tiefgaragenstellplatz",
        city="Frankfurt am Main",
        district="Westend",
        price=980000.0,
        living_space_sqm=110.0,
        rooms=3.5,
        build_year=2017,
        energy_class="A",
        property_type="Wohnung",
        condition="Neuwertig",
        balcony=True,
        garden=False,
        elevator=True,
        fitted_kitchen=True,
        parking=True,
        postal_code="60325",
        latitude=50.1220,
        longitude=8.6680,
        url="https://www.immobilienscout24.de/expose/sample-frankfurt-loft-980k",
        source="Sample: ImmoScout24 (Loft)",
        description="Hochwertiges Designer-Loft mit bodentiefen Fenstern und Blick auf die Skyline."
    ),
}

class ListingUrlParser:
    """
    Parser for German real estate listing URLs, HTML pages, and JSON payloads.
    Supports ImmoScout24, Immowelt, Kleinanzeigen, and Schema.org JSON-LD.
    """

    def __init__(self, request_timeout: int = 10):
        self.timeout = request_timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
            "Sec-Ch-Ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
        }

    def parse_url(self, url_or_text: str, default_city: str = "Deggendorf") -> PropertyListing:
        cleaned = url_or_text.strip()
        
        # Check sample shortcuts
        if cleaned.lower() in SAMPLE_LISTINGS:
            return SAMPLE_LISTINGS[cleaned.lower()]
        
        for key, sample in SAMPLE_LISTINGS.items():
            if sample.url and cleaned == sample.url:
                return sample
            if key in cleaned.lower():
                return sample

        # Check if it is a URL
        if cleaned.startswith("http://") or cleaned.startswith("https://"):
            try:
                session = requests.Session()
                response = session.get(cleaned, headers=self.headers, timeout=self.timeout)
                
                if response.status_code == 200 and len(response.text) > 500:
                    listing = self.parse_html(response.text, url=cleaned, default_city=default_city)
                    if listing.price > 10000 and listing.living_space_sqm > 10:
                        return listing
                else:
                    logger.warning(f"Live request returned status {response.status_code}")
            except Exception as e:
                logger.warning(f"Live fetch error ({e}), falling back to URL heuristics parser.")

        return self._parse_from_url_heuristics(cleaned, default_city=default_city)

    def parse_html(self, html_content: str, url: Optional[str] = None, default_city: str = "Deggendorf") -> PropertyListing:
        soup = BeautifulSoup(html_content, "html.parser")
        
        # 1. ImmoScout24 JS keyValues
        is24_match = re.search(r"var\s+keyValues\s*=\s*(\{.*?\});", html_content, re.DOTALL)
        if is24_match:
            try:
                kv = json.loads(is24_match.group(1))
                return self._extract_from_is24_keyvalues(kv, soup, url, default_city)
            except Exception:
                pass

        # 2. Next.js __NEXT_DATA__
        next_data = soup.find("script", id="__NEXT_DATA__")
        if next_data and next_data.string:
            try:
                nd = json.loads(next_data.string)
                listing = self._extract_from_next_data(nd, url, default_city)
                if listing and listing.price > 10000:
                    return listing
            except Exception:
                pass

        # 3. JSON-LD structured data
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                if isinstance(data, list):
                    data = data[0]
                if isinstance(data, dict):
                    if data.get("@type") in ["RealEstateListing", "Product", "SingleFamilyResidence", "Apartment", "House", "Place"]:
                        listing = self._extract_from_json_ld(data, soup, url, default_city)
                        if listing and listing.price > 10000:
                            return listing
            except Exception:
                continue

        # 4. Immowelt preloaded state
        iw_match = re.search(r"window\.__PRELOADED_STATE__\s*=\s*(\{.*?\});", html_content, re.DOTALL)
        if iw_match:
            try:
                iw_state = json.loads(iw_match.group(1))
                listing = self._extract_from_immowelt_state(iw_state, url, default_city)
                if listing and listing.price > 10000:
                    return listing
            except Exception:
                pass

        # 5. Extract from Meta tags & Full HTML text
        return self._extract_from_html_text_and_meta(soup, html_content, url, default_city)

    def _extract_from_is24_keyvalues(self, kv: Dict[str, Any], soup: BeautifulSoup, url: Optional[str], default_city: str) -> PropertyListing:
        price_raw = kv.get("obj_purchasePrice") or kv.get("obj_price") or kv.get("obj_baseRent") or "0"
        price = float(str(price_raw).replace(".", "").replace(",", "."))
        
        sqm_raw = kv.get("obj_livingSpace") or "75"
        sqm = float(str(sqm_raw).replace(",", "."))
        
        rooms_raw = kv.get("obj_rooms") or "3"
        rooms = float(str(rooms_raw).replace(",", "."))
        
        year_raw = kv.get("obj_yearConstructed")
        year = int(year_raw) if year_raw and str(year_raw).isdigit() else None
        
        energy = str(kv.get("obj_energyEfficiencyClass", "UNKNOWN")).upper()
        if energy not in ["A+", "A", "B", "C", "D", "E", "F", "G", "H"]:
            energy = "UNKNOWN"

        city = kv.get("obj_regio2") or kv.get("obj_regio3") or default_city
        district = kv.get("obj_regio3") or "Zentrum"
        
        balcony = bool(kv.get("obj_hasBalcony") == "y" or kv.get("obj_balcony") == "y")
        garden = bool(kv.get("obj_hasCourt") == "y" or kv.get("obj_garden") == "y")
        elevator = bool(kv.get("obj_hasElevator") == "y" or kv.get("obj_lift") == "y")
        kitchen = bool(kv.get("obj_hasBuiltInKitchen") == "y" or kv.get("obj_kitchen") == "y")
        parking = bool(kv.get("obj_parkingSpace") or kv.get("obj_garage") == "y")

        prop_type_raw = str(kv.get("obj_immotype", "Wohnung")).lower()
        if "haus" in prop_type_raw or "house" in prop_type_raw:
            prop_type = "Haus"
        elif "villa" in prop_type_raw:
            prop_type = "Villa"
        elif "penthouse" in prop_type_raw:
            prop_type = "Penthouse"
        else:
            prop_type = "Wohnung"

        title = soup.title.string if soup.title else f"{rooms:.1f}-Zimmer {prop_type} in {city}"
        profile = get_city_profile(city)

        return PropertyListing(
            title=title.strip()[:140],
            city=profile.name,
            district=district,
            price=price if price > 10000 else profile.base_price_per_sqm * sqm,
            living_space_sqm=sqm,
            rooms=rooms,
            build_year=year,
            energy_class=energy,
            property_type=prop_type,
            condition="Gepflegt",
            balcony=balcony,
            garden=garden,
            elevator=elevator,
            fitted_kitchen=kitchen,
            parking=parking,
            latitude=profile.center_lat,
            longitude=profile.center_lon,
            postal_code=profile.postal_codes[0] if profile.postal_codes else "00000",
            url=url,
            source="ImmoScout24 Parser"
        )

    def _extract_from_next_data(self, nd: Dict[str, Any], url: Optional[str], default_city: str) -> Optional[PropertyListing]:
        props = nd.get("props", {}).get("pageProps", {})
        expose = props.get("expose", {}) or props.get("estate", {}) or props.get("listing", {})
        if not expose:
            return None

        price = float(expose.get("price", {}).get("value", 0.0) or expose.get("purchasePrice", 0.0))
        sqm = float(expose.get("livingSpace", 0.0) or expose.get("area", 75.0))
        rooms = float(expose.get("numberOfRooms", 3.0) or expose.get("rooms", 3.0))
        year = expose.get("constructionYear")
        city = expose.get("address", {}).get("city", default_city) if isinstance(expose.get("address"), dict) else default_city
        district = expose.get("address", {}).get("district", "Zentrum") if isinstance(expose.get("address"), dict) else "Zentrum"
        title = expose.get("title", f"Immobilie in {city}")

        profile = get_city_profile(city)
        return PropertyListing(
            title=title[:140],
            city=profile.name,
            district=district,
            price=price if price > 10000 else profile.base_price_per_sqm * sqm,
            living_space_sqm=sqm,
            rooms=rooms,
            build_year=int(year) if year else None,
            energy_class="B",
            latitude=profile.center_lat,
            longitude=profile.center_lon,
            url=url,
            source="Next.js Payload Extractor"
        )

    def _extract_from_json_ld(self, data: Dict[str, Any], soup: BeautifulSoup, url: Optional[str], default_city: str) -> Optional[PropertyListing]:
        title = data.get("name") or (soup.title.string if soup.title else "Immobilienangebot")
        price = 0.0
        offers = data.get("offers", {})
        if isinstance(offers, dict):
            price = float(offers.get("price", 0.0))
        elif isinstance(offers, list) and len(offers) > 0:
            price = float(offers[0].get("price", 0.0))
            
        sqm = float(data.get("floorSize", {}).get("value", 75.0)) if isinstance(data.get("floorSize"), dict) else 75.0
        rooms = float(data.get("numberOfRooms", 3.0))
        year = data.get("yearBuilt")
        
        city = default_city
        district = "Zentrum"
        address = data.get("address", {})
        if isinstance(address, dict):
            city = address.get("addressLocality", default_city)
            district = address.get("addressRegion", "Zentrum")
            
        profile = get_city_profile(city)
        
        return PropertyListing(
            title=title[:140],
            city=profile.name,
            district=district,
            price=price if price > 10000 else profile.base_price_per_sqm * sqm,
            living_space_sqm=sqm,
            rooms=rooms,
            build_year=int(year) if year else None,
            energy_class="B",
            latitude=profile.center_lat,
            longitude=profile.center_lon,
            url=url,
            source="JSON-LD Extractor"
        )

    def _extract_from_immowelt_state(self, state: Dict[str, Any], url: Optional[str], default_city: str) -> Optional[PropertyListing]:
        estate = state.get("estate", {})
        if not estate:
            return None
        price = float(estate.get("price", 0.0))
        sqm = float(estate.get("livingSpace", 75.0))
        rooms = float(estate.get("rooms", 3.0))
        city = estate.get("city", default_city)
        profile = get_city_profile(city)
        return PropertyListing(
            title=estate.get("title", f"Immobilie in {city}")[:140],
            city=profile.name,
            district=estate.get("district", "Zentrum"),
            price=price,
            living_space_sqm=sqm,
            rooms=rooms,
            latitude=profile.center_lat,
            longitude=profile.center_lon,
            url=url,
            source="Immowelt State Extractor"
        )

    def _extract_from_html_text_and_meta(self, soup: BeautifulSoup, html: str, url: Optional[str], default_city: str) -> PropertyListing:
        # Check meta tags
        meta_desc = ""
        og_desc = soup.find("meta", property="og:description")
        if og_desc and og_desc.get("content"):
            meta_desc = og_desc["content"]
        elif soup.find("meta", attrs={"name": "description"}):
            meta_desc = soup.find("meta", attrs={"name": "description"})["content"]

        meta_title = ""
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            meta_title = og_title["content"]
        elif soup.title:
            meta_title = soup.title.string

        full_text = f"{meta_title} {meta_desc} " + soup.get_text(separator=" ", strip=True)

        price = self._extract_price(full_text)
        sqm = self._extract_sqm(full_text) or 75.0
        rooms = self._extract_rooms(full_text) or 3.0
        year = self._extract_build_year(full_text)
        energy = self._extract_energy_class(full_text) or "C"
        
        city, district = self._detect_city_and_district(full_text, default_city)
        profile = get_city_profile(city)

        if not price or price < 10000:
            price = profile.base_price_per_sqm * sqm

        balcony = bool(re.search(r"balkon|terrasse|loggia", full_text, re.I))
        garden = bool(re.search(r"garten|gartenanteil", full_text, re.I))
        elevator = bool(re.search(r"aufzug|fahrstuhl|lift", full_text, re.I))
        fitted_kitchen = bool(re.search(r"einbauk[üu]che|ebk", full_text, re.I))
        parking = bool(re.search(r"garage|stellplatz|tiefgarage|carport", full_text, re.I))

        return PropertyListing(
            title=(meta_title or f"Immobilie in {city}")[:140],
            city=profile.name,
            district=district,
            price=price,
            living_space_sqm=sqm,
            rooms=rooms,
            build_year=year,
            energy_class=energy,
            balcony=balcony,
            garden=garden,
            elevator=elevator,
            fitted_kitchen=fitted_kitchen,
            parking=parking,
            latitude=profile.center_lat,
            longitude=profile.center_lon,
            postal_code=profile.postal_codes[0] if profile.postal_codes else None,
            url=url,
            source="HTML & Meta Extractor"
        )

    def _parse_from_url_heuristics(self, text_or_url: str, default_city: str) -> PropertyListing:
        """
        Extracts city, district, price, and space clues from the URL string itself.
        """
        decoded_url = unquote(text_or_url)
        city = default_city
        for c in GERMAN_CITIES.keys():
            if c.lower() in decoded_url.lower():
                city = c
                break
                
        profile = get_city_profile(city)
        district = profile.districts[0].name if profile.districts else "Zentrum"
        for d in profile.districts:
            if d.name.lower() in decoded_url.lower():
                district = d.name
                break

        # Check for price patterns in the URL slug
        price = self._extract_price(decoded_url)
        sqm = self._extract_sqm(decoded_url) or 80.0
        rooms = self._extract_rooms(decoded_url) or 3.0

        if not price:
            price = round(profile.base_price_per_sqm * sqm, -2)

        return PropertyListing(
            title=f"Immobilienangebot in {city} ({district})",
            city=city,
            district=district,
            price=float(price),
            living_space_sqm=sqm,
            rooms=rooms,
            build_year=2018,
            energy_class="B",
            property_type="Wohnung",
            condition="Gepflegt",
            balcony=True,
            garden=False,
            elevator=True,
            fitted_kitchen=True,
            parking=True,
            latitude=profile.center_lat,
            longitude=profile.center_lon,
            postal_code=profile.postal_codes[0] if profile.postal_codes else "00000",
            url=text_or_url if text_or_url.startswith("http") else None,
            source="URL String Parser (Verify parameters below)",
            description=f"Objekt in {city} ({district})."
        )

    def _extract_price(self, text: str) -> Optional[float]:
        # Handle formats: 2.450.000 €, 2,45 Mio. €, 2.000.000 EUR, 350.000 €, 350000 €
        
        # 1. Millions notation: 2,45 Mio € / 2.45 Mio Euro / 2 Mio. €
        m_mio = re.search(r"(\d+(?:[,\.]\d+)?)\s*(?:mio\.?|millionen?)\s*(?:€|eur|euro)?", text, re.I)
        if m_mio:
            try:
                val = float(m_mio.group(1).replace(",", ".")) * 1_000_000
                if 50000 <= val <= 50000000:
                    return val
            except ValueError:
                pass

        # 2. Standard German currency format: 2.450.000 € / Kaufpreis: 2.000.000 € / 350.000,- EUR
        # Avoid matching small amounts like Hausgeld (280 €) by checking for Kaufpreis or large figures
        matches = re.finditer(r"(?:kaufpreis|preis|wert)?\s*[:]?\s*(\d{1,3}(?:\.\d{3})+|\d{5,8})(?:,\d{2})?\s*(?:€|eur|euro|,-)", text, re.I)
        prices = []
        for m in matches:
            clean_str = m.group(1).replace(".", "")
            try:
                val = float(clean_str)
                if 25000 <= val <= 50000000:
                    prices.append(val)
            except ValueError:
                continue

        if prices:
            # Prefer larger purchase price over incidental fees
            return max(prices)

        return None

    def _extract_sqm(self, text: str) -> Optional[float]:
        # Matches: 180 m², 180,5 qm, Wohnfläche: 92 m², 220.5 m2
        m = re.search(r"(?:wohnfl[äa]che|fl[äa]che|gr[öo][ßs]e)?\s*[:]?\s*(\d{2,4}(?:[,\.]\d{1,2})?)\s*(?:m²|qm|m2)", text, re.I)
        if m:
            clean_str = m.group(1).replace(",", ".")
            try:
                val = float(clean_str)
                if 15.0 <= val <= 2500.0:
                    return val
            except ValueError:
                pass
        return None

    def _extract_rooms(self, text: str) -> Optional[float]:
        # Matches: 3,5 Zimmer, 4 Zimmer, 2.5 Zi., 5.0 Räume
        m = re.search(r"(\d{1,2}(?:[,\.]\d{1})?)\s*(?:zimmer|zi\.?|r[äa]ume)", text, re.I)
        if m:
            clean_str = m.group(1).replace(",", ".")
            try:
                val = float(clean_str)
                if 1.0 <= val <= 25.0:
                    return val
            except ValueError:
                pass
        return None

    def _extract_build_year(self, text: str) -> Optional[int]:
        m = re.search(r"(?:baujahr|erbaut|bj\.?)\s*[:]?\s*(18\d{2}|19\d{2}|20[0-2]\d)", text, re.I)
        if m:
            try:
                return int(m.group(1))
            except ValueError:
                pass
        return None

    def _extract_energy_class(self, text: str) -> Optional[str]:
        m = re.search(r"(?:energieeffizienzklasse|effizienzklasse|energieklasse)\s*[:]?\s*([A-H]\+?|[A-H])", text, re.I)
        if m:
            return m.group(1).upper()
        return None

    def _detect_city_and_district(self, text: str, default_city: str) -> Tuple[str, str]:
        detected_city = default_city
        for c in GERMAN_CITIES.keys():
            if re.search(r"\b" + re.escape(c) + r"\b", text, re.I):
                detected_city = c
                break
                
        profile = get_city_profile(detected_city)
        detected_district = profile.districts[0].name if profile.districts else "Zentrum"
        for d in profile.districts:
            if re.search(r"\b" + re.escape(d.name) + r"\b", text, re.I):
                detected_district = d.name
                break
                
        return detected_city, detected_district
