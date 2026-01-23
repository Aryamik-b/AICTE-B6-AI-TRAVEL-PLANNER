import requests
import streamlit as st
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
    except Exception as e:
        st.error(f"City search failed: {e}")
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
    """
    IMPROVED: Better error handling and debugging
    """
    if not city:
        st.warning("⚠️ Empty city name provided to geocode_city()")
        return None

    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": city, "format": "json", "limit": 1}
    headers = {"User-Agent": "AITravelPlanner/1.0 (streamlit app)"}

    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        
        if not data:
            st.error(f"🔍 Geocoding failed: No results for '{city}'")
            st.info("💡 Try: Full city name with country (e.g., 'Paris, France')")
            return None
            
        lat, lon = float(data[0]["lat"]), float(data[0]["lon"])
        st.success(f"✅ Geocoded '{city}' → {lat:.4f}, {lon:.4f}")
        return lat, lon
        
    except requests.exceptions.Timeout:
        st.error(f"⏱️ Geocoding timeout for '{city}'. Try again.")
        return None
    except Exception as e:
        st.error(f"❌ Geocoding error for '{city}': {str(e)}")
        return None


@st.cache_data(ttl=86400)
def get_attractions_osm(city: str, limit: int = 15, radius_m: int = 30000):
    """
    IMPROVED: Added debugging and fallback handling
    """
    st.info(f"🔍 Searching attractions in '{city}' (radius: {radius_m/1000}km)...")
    
    coords = geocode_city(city)
    if not coords:
        return []

    lat, lon = coords
    overpass_url = "https://overpass-api.de/api/interpreter"

    query = f"""
    [out:json][timeout:60];
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
        
        total_found = len(data.get("elements", []))
        st.info(f"📊 OSM returned {total_found} raw elements")
        
    except requests.exceptions.Timeout:
        st.error("⏱️ OSM API timeout. Try reducing radius or try again later.")
        return []
    except Exception as e:
        st.error(f"❌ OSM query failed: {str(e)}")
        return []

    places = []
    filtered_out = 0
    
    for element in data.get("elements", []):
        tags = element.get("tags", {})
        name = tags.get("name")
        
        if not name:
            continue
            
        if is_valid_tourist_place(name):
            places.append(name)
        else:
            filtered_out += 1

    unique_places = uniq(places)[:limit]
    
    st.success(f"✅ Found {len(unique_places)} valid attractions (filtered {filtered_out})")
    
    if len(unique_places) == 0:
        st.warning(f"⚠️ No attractions found. Try:\n- Larger radius\n- Nearby bigger city\n- Check spelling")
    
    return unique_places


@st.cache_data(ttl=86400)
def get_city_categories(city: str, radius_m: int = 40000, limit_each: int = 10):
    """
    IMPROVED: Better debugging
    """
    st.info(f"🏖️ Searching categories in '{city}' (radius: {radius_m/1000}km)...")
    
    coords = geocode_city(city)
    if not coords:
        return {}

    lat, lon = coords
    overpass_url = "https://overpass-api.de/api/interpreter"

    query = f"""
    [out:json][timeout:80];
    (
      node(around:{radius_m},{lat},{lon})["natural"="beach"];
      way(around:{radius_m},{lat},{lon})["natural"="beach"];
      node(around:{radius_m},{lat},{lon})["natural"="peak"];
      node(around:{radius_m},{lat},{lon})["tourism"="viewpoint"];
      node(around:{radius_m},{lat},{lon})["waterway"="waterfall"];
      node(around:{radius_m},{lat},{lon})["natural"="waterfall"];
      node(around:{radius_m},{lat},{lon})["leisure"="water_park"];
      node(around:{radius_m},{lat},{lon})["tourism"="theme_park"];
      node(around:{radius_m},{lat},{lon})["tourism"="zoo"];
      node(around:{radius_m},{lat},{lon})["historic"];
      node(around:{radius_m},{lat},{lon})["tourism"="museum"];
    );
    out tags;
    """

    try:
        response = requests.get(overpass_url, params={"data": query}, timeout=80)
        response.raise_for_status()
        data = response.json()
        st.info(f"📊 Categories query returned {len(data.get('elements', []))} elements")
    except Exception as e:
        st.error(f"❌ Categories query failed: {str(e)}")
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
        elif tags.get("leisure") == "water_park" or tags.get("tourism") in ["theme_park", "zoo", "attraction"]:
            adventure.append(name)
        elif tags.get("historic") is not None or tags.get("tourism") in ["museum", "gallery"]:
            culture.append(name)

    result = {
        "Beaches 🏖️": uniq(beaches)[:limit_each],
        "Hill Stations / Viewpoints ⛰️": uniq(hills)[:limit_each],
        "Waterfalls 🌊": uniq(waterfalls)[:limit_each],
        "Adventure / Fun 🎢": uniq(adventure)[:limit_each],
        "Culture / History 🏛️": uniq(culture)[:limit_each],
    }
    
    total_places = sum(len(v) for v in result.values())
    st.success(f"✅ Categorized {total_places} places")
    
    return result


@st.cache_data(ttl=86400)
def get_nearby_day_trips(city: str, radius_m: int = 200000, limit_each: int = 10):
    """
    IMPROVED: Better debugging
    """
    st.info(f"🚗 Searching day trips near '{city}' (radius: {radius_m/1000}km)...")
    
    coords = geocode_city(city)
    if not coords:
        return {}

    lat, lon = coords
    overpass_url = "https://overpass-api.de/api/interpreter"

    query = f"""
    [out:json][timeout:90];
    (
      node(around:{radius_m},{lat},{lon})["tourism"="attraction"];
      node(around:{radius_m},{lat},{lon})["historic"];
      node(around:{radius_m},{lat},{lon})["tourism"="viewpoint"];
      node(around:{radius_m},{lat},{lon})["natural"="peak"];
      node(around:{radius_m},{lat},{lon})["waterway"="waterfall"];
      node(around:{radius_m},{lat},{lon})["natural"="beach"];
    );
    out tags;
    """

    try:
        response = requests.get(overpass_url, params={"data": query}, timeout=90)
        response.raise_for_status()
        data = response.json()
        st.info(f"📊 Day trips query returned {len(data.get('elements', []))} elements")
    except Exception as e:
        st.error(f"❌ Day trips query failed: {str(e)}")
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
        elif tags.get("tourism") == "attraction" or tags.get("historic") is not None:
            special.append(name)

    result = {
        "Nearby Hill/Nature Trips ⛰️": uniq(hills)[:limit_each],
        "Nearby Waterfalls 🌿": uniq(nature)[:limit_each],
        "Nearby Beaches 🏖️": uniq(beaches)[:limit_each],
        "Special Places ✨": uniq(special)[:limit_each],
    }
    
    total_places = sum(len(v) for v in result.values())
    st.success(f"✅ Found {total_places} day trip destinations")
    
    return result