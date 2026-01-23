import requests
import streamlit as st

def is_valid_tourist_place(name: str) -> bool:
    if not name:
        return False
    n = name.lower()

    blacklist = [
        "club", "tennis", "gym", "school", "college", "office", "corporation",
        "pvt", "private", "hospital", "clinic", "atm", "police", "bank",
        "apartment", "residency", "hostel", "complex"
    ]

    return not any(b in n for b in blacklist)


@st.cache_data(ttl=3600)
def search_cities(query: str, limit: int = 8):
    if not query or len(query) < 2:
        return []

    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": query,
        "format": "json",
        "addressdetails": 1,
        "limit": limit
    }
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

    return list(dict.fromkeys(suggestions))


def clean_city_name(full_location: str) -> str:
    if not full_location:
        return ""
    city = full_location.split(",")[0].strip()

    bad = ["corporation", "municipality", "district", "division", "region"]
    for word in bad:
        city = city.replace(word.title(), "").replace(word.lower(), "").strip()

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
def get_attractions_osm(city: str, limit: int = 12, radius_m: int = 20000):
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
      node(around:{radius_m},{lat},{lon})["historic"="monument"];
      node(around:{radius_m},{lat},{lon})["amenity"="place_of_worship"];
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
        name = element.get("tags", {}).get("name")
        if name:
            places.append(name)

    unique_places = list(dict.fromkeys(places))
    return unique_places[:limit]



@st.cache_data(ttl=86400)
def get_city_categories(city: str, radius_m: int = 40000, limit_each: int = 8):
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

      // Hill stations / Viewpoints / Peaks
      node(around:{radius_m},{lat},{lon})["tourism"="viewpoint"];
      node(around:{radius_m},{lat},{lon})["natural"="peak"];
      node(around:{radius_m},{lat},{lon})["natural"="hill"];

      // Adventure / Fun
      node(around:{radius_m},{lat},{lon})["leisure"="water_park"];
      node(around:{radius_m},{lat},{lon})["tourism"="theme_park"];
      node(around:{radius_m},{lat},{lon})["tourism"="zoo"];
      node(around:{radius_m},{lat},{lon})["sport"];
      node(around:{radius_m},{lat},{lon})["leisure"="park"];

      // Waterfalls / Nature
      node(around:{radius_m},{lat},{lon})["waterway"="waterfall"];
      node(around:{radius_m},{lat},{lon})["natural"="waterfall"];

      // Culture / History
      node(around:{radius_m},{lat},{lon})["historic"="monument"];
      node(around:{radius_m},{lat},{lon})["tourism"="museum"];
      node(around:{radius_m},{lat},{lon})["amenity"="place_of_worship"];
    );
    out tags;
    """

    try:
        response = requests.get(overpass_url, params={"data": query}, timeout=80)
        response.raise_for_status()
        data = response.json()
    except Exception:
        return {}

    beaches, hills, adventure, waterfalls, culture = [], [], [], [], []

    for element in data.get("elements", []):
        tags = element.get("tags", {})
        name = tags.get("name")
        if not name:
            continue

        if tags.get("natural") == "beach":
            beaches.append(name)

        elif tags.get("tourism") == "viewpoint" or tags.get("natural") in ["peak", "hill"]:
            hills.append(name)

        elif tags.get("leisure") == "water_park" or tags.get("tourism") in ["theme_park", "zoo"] or tags.get("sport") or tags.get("leisure") == "park":
            adventure.append(name)

        elif tags.get("waterway") == "waterfall" or tags.get("natural") == "waterfall":
            waterfalls.append(name)

        elif tags.get("historic") == "monument" or tags.get("tourism") == "museum" or tags.get("amenity") == "place_of_worship":
            culture.append(name)

    def uniq(items):
        return list(dict.fromkeys(items))[:limit_each]

    return {
        "Beaches 🏖️": uniq(beaches),
        "Hill Stations / Viewpoints ⛰️": uniq(hills),
        "Waterfalls 🌊": uniq(waterfalls),
        "Adventure / Fun 🎢": uniq(adventure),
        "Culture / History 🏛️": uniq(culture),
    }



@st.cache_data(ttl=86400)
def get_nearby_day_trips(city: str, radius_m: int = 200000, limit_each: int = 8):
    """
    Finds nearby destinations (day trips) using broader radius.
    Example: Vizag -> Araku Valley, Borra Caves etc.
    """
    coords = geocode_city(city)
    if not coords:
        return {}

    lat, lon = coords
    overpass_url = "https://overpass-api.de/api/interpreter"

    query = f"""
    [out:json];
    (
      // Hill / mountain / viewpoints
      node(around:{radius_m},{lat},{lon})["natural"="peak"];
      node(around:{radius_m},{lat},{lon})["tourism"="viewpoint"];
      node(around:{radius_m},{lat},{lon})["place"="village"];
      node(around:{radius_m},{lat},{lon})["place"="town"];

      // Waterfalls & nature
      node(around:{radius_m},{lat},{lon})["waterway"="waterfall"];
      node(around:{radius_m},{lat},{lon})["natural"="waterfall"];

      // Caves / special natural
      node(around:{radius_m},{lat},{lon})["natural"="cave_entrance"];

      // Beaches (coastal trips)
      node(around:{radius_m},{lat},{lon})["natural"="beach"];
      way(around:{radius_m},{lat},{lon})["natural"="beach"];

      // Wildlife / parks
      node(around:{radius_m},{lat},{lon})["boundary"="national_park"];
      node(around:{radius_m},{lat},{lon})["leisure"="nature_reserve"];
    );
    out tags;
    """

    try:
        response = requests.get(overpass_url, params={"data": query}, timeout=90)
        response.raise_for_status()
        data = response.json()
    except Exception:
        return {}

    hill_trips, nature_trips, beach_trips, special_trips = [], [], [], []

    for element in data.get("elements", []):
        tags = element.get("tags", {})
        name = tags.get("name")
        if not name:
            continue

        if tags.get("natural") in ["peak"] or tags.get("tourism") == "viewpoint":
            hill_trips.append(name)

        elif tags.get("waterway") == "waterfall" or tags.get("natural") in ["waterfall"]:
            nature_trips.append(name)

        elif tags.get("natural") == "beach":
            beach_trips.append(name)

        elif tags.get("natural") == "cave_entrance":
            special_trips.append(name)

    def uniq(items):
        return list(dict.fromkeys(items))[:limit_each]

    return {
        "Nearby Hill/Nature Trips (Day Trips) ⛰️": uniq(hill_trips),
        "Nearby Waterfalls/Nature 🌿": uniq(nature_trips),
        "Nearby Beaches 🏖️": uniq(beach_trips),
        "Special Places (Caves etc.) 🕳️": uniq(special_trips),
    }
