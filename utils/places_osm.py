import requests
import streamlit as st
import re


import re

def is_valid_tourist_place(name: str) -> bool:
    if not name:
        return False

    n = name.strip().lower()

    if len(n) < 4:
        return False

    if re.fullmatch(r"[0-9\-_/]+", n):
        return False

    if re.search(r"[<>={}\[\]\\|~]", n):
        return False

    bad_phrases = [
        "room", "rooms", "guest house", "guesthouse", "lodge", "lodging",
        "hostel", "pg", "homestay", "dorm", "dormitory",
        "villa", "resort", "hotel", "restaurant", "cafe", "bar", "lounge",
        "apartment", "residency"
    ]
    if any(p in n for p in bad_phrases):
        return False

    blacklist = [

        "nagar", "colony", "layout", "extension", "enclave", "vihar",
        "sector", "phase", "block", "ward",
        "street", "road", "lane", "avenue", "circle", "junction", "signal", "cross",

        "corporation", "municipality", "office", "collectorate",
        "secretariat", "department",

        "atm", "bank", "police", "post office", "courier",
        "hospital", "clinic", "pharmacy", "medical", "diagnostic",
        "school", "college", "university", "institute", "coaching",

        "store", "mart", "supermarket", "bakery", "salon",

        "club", "tennis", "gym", "fitness", "association",
        "arena", "badminton", "yoga", "swimming", "pool",
    ]

    if any(b in n for b in blacklist):
        return False

    generic_names = {"park", "beach", "museum", "lake", "viewpoint", "temple", "church"}
    if n in generic_names:
        return False

    return True



def uniq(items):
    return list(dict.fromkeys(items))


@st.cache_data(ttl=3600)
def search_cities(query: str, limit: int = 8):
    if not query or len(query) < 2:
        return []

    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": query, "format": "json", "addressdetails": 1, "limit": limit}
    headers = {"User-Agent": "AITravelPlanner/1.0 (streamlit app)"}

    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception:
        return []

    suggestions = []
    for item in data:
        display_name = item.get("display_name", "")
        if display_name:
            suggestions.append(display_name)

    return uniq(suggestions)


def clean_city_name(full_location: str) -> str:
    if not full_location:
        return ""

    city = full_location.split(",")[0].strip()

    noisy = ["Corporation", "Municipality", "District", "Division", "Region", "Metropolitan"]
    for w in noisy:
        city = city.replace(w, "").strip()

    city = re.sub(r"\s+", " ", city).strip()
    return city


@st.cache_data(ttl=86400)
def geocode_city(city: str):
    if not city:
        return None

    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": city, "format": "json", "limit": 1}
    headers = {"User-Agent": "AITravelPlanner/1.0 (streamlit app)"}

    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        if not data:
            return None
        return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception:
        return None


@st.cache_data(ttl=86400)
def get_attractions_osm(city: str, limit: int = 15, radius_m: int = 30000):
    coords = geocode_city(city)
    if not coords:
        return []

    lat, lon = coords
    overpass_url = "https://overpass-api.de/api/interpreter"

    query = f"""
    [out:json];
    (
      node(around:{radius_m},{lat},{lon})["tourism"="attraction"];
      node(around:{radius_m},{lat},{lon})["tourism"="museum"];
      node(around:{radius_m},{lat},{lon})["tourism"="gallery"];
      node(around:{radius_m},{lat},{lon})["tourism"="viewpoint"];
      node(around:{radius_m},{lat},{lon})["historic"];
      node(around:{radius_m},{lat},{lon})["man_made"="lighthouse"];
      node(around:{radius_m},{lat},{lon})["natural"="beach"];
      node(around:{radius_m},{lat},{lon})["leisure"="park"];
    );
    out tags;
    """

    try:
        response = requests.get(overpass_url, params={"data": query}, timeout=60)
        response.raise_for_status()
        data = response.json()
    except Exception:
        return []

    places = []
    for element in data.get("elements", []):
        tags = element.get("tags", {})
        name = tags.get("name")
        if name and is_valid_tourist_place(name):
            places.append(name)

    return uniq(places)[:limit]


@st.cache_data(ttl=86400)
def get_city_categories(city: str, radius_m: int = 40000, limit_each: int = 10):
    coords = geocode_city(city)
    if not coords:
        return {}

    lat, lon = coords
    overpass_url = "https://overpass-api.de/api/interpreter"

    query = f"""
    [out:json];
    (
      // Beaches
      node(around:{radius_m},{lat},{lon})["natural"="beach"];
      way(around:{radius_m},{lat},{lon})["natural"="beach"];

      // Hill / Peaks / Viewpoints
      node(around:{radius_m},{lat},{lon})["natural"="peak"];
      node(around:{radius_m},{lat},{lon})["tourism"="viewpoint"];
      node(around:{radius_m},{lat},{lon})["natural"="hill"];

      // Waterfalls
      node(around:{radius_m},{lat},{lon})["waterway"="waterfall"];
      node(around:{radius_m},{lat},{lon})["natural"="waterfall"];

      // Adventure / Fun
      node(around:{radius_m},{lat},{lon})["leisure"="water_park"];
      node(around:{radius_m},{lat},{lon})["tourism"="theme_park"];
      node(around:{radius_m},{lat},{lon})["tourism"="zoo"];
      node(around:{radius_m},{lat},{lon})["tourism"="attraction"];
      node(around:{radius_m},{lat},{lon})["leisure"="park"];

      // Culture / History
      node(around:{radius_m},{lat},{lon})["historic"];
      node(around:{radius_m},{lat},{lon})["tourism"="museum"];
      node(around:{radius_m},{lat},{lon})["tourism"="gallery"];
      node(around:{radius_m},{lat},{lon})["man_made"="lighthouse"];
    );
    out tags;
    """

    try:
        response = requests.get(overpass_url, params={"data": query}, timeout=80)
        response.raise_for_status()
        data = response.json()
    except Exception:
        return {}

    beaches, hills, waterfalls, adventure, culture = [], [], [], [], []

    for element in data.get("elements", []):
        tags = element.get("tags", {})
        name = tags.get("name")
        if not name:
            continue

        if tags.get("natural") == "beach":
            beaches.append(name)
            continue

        if not is_valid_tourist_place(name):
            continue

        if tags.get("tourism") == "viewpoint" or tags.get("natural") in ["peak", "hill"]:
            hills.append(name)
        elif tags.get("waterway") == "waterfall" or tags.get("natural") == "waterfall":
            waterfalls.append(name)
        elif tags.get("leisure") == "water_park" or tags.get("tourism") in ["theme_park", "zoo", "attraction"] or tags.get("leisure") == "park":
            adventure.append(name)
        elif tags.get("historic") is not None or tags.get("tourism") in ["museum", "gallery"] or tags.get("man_made") == "lighthouse":
            culture.append(name)

    return {
        "Beaches 🏖️": uniq(beaches)[:limit_each],
        "Hill Stations / Viewpoints ⛰️": uniq(hills)[:limit_each],
        "Waterfalls 🌊": uniq(waterfalls)[:limit_each],
        "Adventure / Fun 🎢": uniq(adventure)[:limit_each],
        "Culture / History 🏛️": uniq(culture)[:limit_each],
    }


@st.cache_data(ttl=86400)
def get_nearby_day_trips(city: str, radius_m: int = 200000, limit_each: int = 10):
    coords = geocode_city(city)
    if not coords:
        return {}

    lat, lon = coords
    overpass_url = "https://overpass-api.de/api/interpreter"

    query = f"""
    [out:json];
    (
      // Common day-trip type places
      node(around:{radius_m},{lat},{lon})["tourism"="attraction"];
      node(around:{radius_m},{lat},{lon})["historic"];
      node(around:{radius_m},{lat},{lon})["tourism"="viewpoint"];
      node(around:{radius_m},{lat},{lon})["natural"="peak"];
      node(around:{radius_m},{lat},{lon})["natural"="hill"];

      // Waterfalls / nature
      node(around:{radius_m},{lat},{lon})["waterway"="waterfall"];
      node(around:{radius_m},{lat},{lon})["natural"="waterfall"];

      // Caves
      node(around:{radius_m},{lat},{lon})["natural"="cave_entrance"];

      // Beaches
      node(around:{radius_m},{lat},{lon})["natural"="beach"];
      way(around:{radius_m},{lat},{lon})["natural"="beach"];
    );
    out tags;
    """

    try:
        response = requests.get(overpass_url, params={"data": query}, timeout=90)
        response.raise_for_status()
        data = response.json()
    except Exception:
        return {}

    hills, nature, beaches, special = [], [], [], []

    for element in data.get("elements", []):
        tags = element.get("tags", {})
        name = tags.get("name")
        if not name:
            continue

        if tags.get("natural") == "beach":
            beaches.append(name)
            continue

        if not is_valid_tourist_place(name):
            continue

        if tags.get("tourism") == "viewpoint" or tags.get("natural") in ["peak", "hill"]:
            hills.append(name)
        elif tags.get("waterway") == "waterfall" or tags.get("natural") == "waterfall":
            nature.append(name)
        elif tags.get("natural") == "cave_entrance":
            special.append(name)
        elif tags.get("tourism") == "attraction" or tags.get("historic") is not None:
            # these can be day trips too
            special.append(name)

    return {
        "Nearby Hill/Nature Trips (Day Trips) ⛰️": uniq(hills)[:limit_each],
        "Nearby Waterfalls/Nature 🌿": uniq(nature)[:limit_each],
        "Nearby Beaches 🏖️": uniq(beaches)[:limit_each],
        "Special Places / Attractions ✨": uniq(special)[:limit_each],
    }
