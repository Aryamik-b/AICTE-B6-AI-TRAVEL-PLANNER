import streamlit as st

from utils.llm import generate_text
from utils.places_osm import (
    search_cities,
    clean_city_name,
    geocode_city,
    get_attractions_osm,
    get_city_categories,
    get_nearby_day_trips,
)
from utils.prompt_builder import build_prompt
from utils.export_pdf import generate_pdf_bytes

from utils.travel_time import (
    haversine_km,
    estimate_travel_time,
    format_hours_range,
)


# ----------------------------------------------------
# Page Config
# ----------------------------------------------------
st.set_page_config(
    page_title="AI Travel Planner",
    page_icon="🧳",
    layout="wide"
)

st.title("🧳 AI Travel Planner")
st.write(
    "AI travel planner with real location data (OpenStreetMap). "
    "Generates itinerary, transport plan, budget estimation, food & tips."
)

# Initialize session storage for generated plan
if "last_plan" not in st.session_state:
    st.session_state["last_plan"] = ""


# ----------------------------------------------------
# Sidebar Inputs
# ----------------------------------------------------
st.sidebar.header("Trip Details")

# Destination autocomplete
st.sidebar.subheader("📍 Destination")
dest_query = st.sidebar.text_input(
    "Type destination (min 2 letters)",
    placeholder="e.g. viz, bhu, del, goa, mu"
)
dest_suggestions = search_cities(dest_query)

if dest_suggestions:
    destination_full = st.sidebar.selectbox("Select destination", dest_suggestions)
else:
    destination_full = dest_query

destination_city = clean_city_name(destination_full)

# Departure autocomplete
st.sidebar.subheader("🏁 Departure (Optional)")
dep_query = st.sidebar.text_input(
    "Type departure city (optional)",
    placeholder="e.g. bbs, del, hyd"
)
dep_suggestions = search_cities(dep_query)

if dep_suggestions:
    departure_full = st.sidebar.selectbox("Select departure", dep_suggestions)
else:
    departure_full = dep_query

days = st.sidebar.slider("Number of Days", 1, 10, 5)

budget = st.sidebar.selectbox("Budget Level", ["Low", "Medium", "High"])

currency = st.sidebar.text_input(
    "Currency (INR/USD/EUR etc.)",
    value="INR"
)

travel_type = st.sidebar.radio("Travel Type", ["Solo", "Family", "Friends"])
transport_pref = st.sidebar.selectbox("Preferred Transport", ["Any", "Flight", "Train", "Bus"])

interests = st.sidebar.multiselect(
    "Interests",
    ["Nature", "Food", "Adventure", "Culture", "Relaxation"]
)

temperature = st.sidebar.slider("Creativity (Temperature)", 0.0, 1.0, 0.7, 0.1)


# ----------------------------------------------------
# Main UI
# ----------------------------------------------------
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("🧾 Selected Inputs")
    st.write(f"**Destination:** {destination_full if destination_full else '-'}")
    st.write(f"**Departure:** {departure_full if departure_full else '-'}")
    st.write(f"**Days:** {days}")
    st.write(f"**Budget:** {budget}")
    st.write(f"**Currency:** {currency.strip().upper() if currency else 'INR'}")
    st.write(f"**Travel type:** {travel_type}")
    st.write(f"**Transport preference:** {transport_pref}")
    st.write(f"**Interests:** {', '.join(interests) if interests else '-'}")

with col2:
    st.subheader("📍 City Highlights + Nearby Trips (Real Data)")

    if destination_city and len(destination_city) >= 2:
        with st.spinner("Fetching places..."):
            city_categories = get_city_categories(destination_city, radius_m=40000, limit_each=8)
            nearby_trips = get_nearby_day_trips(destination_city, radius_m=200000, limit_each=8)

        found_any = False

        for cat, places in city_categories.items():
            if places:
                found_any = True
                with st.expander(f"{cat} (within city)", expanded=False):
                    for p in places:
                        st.write("•", p)

        for cat, places in nearby_trips.items():
            if places:
                found_any = True
                with st.expander(f"{cat} (within ~200km)", expanded=False):
                    for p in places:
                        st.write("•", p)

        if not found_any:
            st.info("No data found. Try a bigger/nearby city name.")
    else:
        st.info("Type/select a destination to fetch places.")

st.markdown("---")


# ----------------------------------------------------
# Generate Travel Plan
# ----------------------------------------------------
if st.button("🚀 Generate Travel Plan"):
    if not destination_city or len(destination_city) < 2:
        st.warning("Please enter/select a destination.")
    else:
        try:
            # ✅ UNIVERSAL Travel time hint (any cities)
            travel_time_hint = "Not available"

            if departure_full and destination_city:
                dep_coords = geocode_city(departure_full)
                dest_coords = geocode_city(destination_city)

                if dep_coords and dest_coords:
                    dist_km = haversine_km(dep_coords[0], dep_coords[1], dest_coords[0], dest_coords[1])
                    low, high, mode = estimate_travel_time(dist_km, transport_pref)
                    travel_time_hint = f"{mode}: approx {format_hours_range(low, high)} (distance ~{dist_km:.0f} km)"

            with st.spinner("Preparing travel data..."):
                attractions = get_attractions_osm(destination_city, limit=12, radius_m=20000)
                if not attractions:
                    attractions = get_attractions_osm(destination_city, limit=12, radius_m=50000)

                city_categories = get_city_categories(destination_city, radius_m=40000, limit_each=8)
                nearby_trips = get_nearby_day_trips(destination_city, radius_m=200000, limit_each=8)

                # ✅ pass travel_time_hint into prompt
                prompt = build_prompt(
                    destination_full=destination_full,
                    destination_city=destination_city,
                    departure_full=departure_full,
                    days=days,
                    budget=budget,
                    currency=currency,
                    travel_type=travel_type,
                    transport_pref=transport_pref,
                    interests=interests,
                    attractions=attractions,
                    city_categories=city_categories,
                    nearby_trips=nearby_trips,
                    travel_time_hint=travel_time_hint,  # ✅ NEW
                )

            with st.spinner("Generating travel plan with LLM..."):
                output_text = generate_text(
                    prompt=prompt,
                    temperature=temperature,
                    max_new_tokens=1200
                )

            st.session_state["last_plan"] = output_text

        except Exception as e:
            st.error("Generation failed. Check HF token / model access / rate limits.")
            st.code(str(e))


# ----------------------------------------------------
# Display Plan + Download PDF
# ----------------------------------------------------
if st.session_state["last_plan"]:
    st.subheader("✅ AI Travel Plan")
    plan_text = st.session_state["last_plan"]

    st.markdown(plan_text)

    pdf_bytes = generate_pdf_bytes(
        title=f"AI Travel Plan - {destination_city}",
        content=plan_text
    )

    st.download_button(
        label="📄 Download Travel Plan as PDF",
        data=pdf_bytes,
        file_name=f"travel_plan_{destination_city.replace(' ', '_').lower()}.pdf",
        mime="application/pdf"
    )

st.markdown("---")
st.caption(
    "⚠️ Costs/timings are approximate. Places are fetched using OpenStreetMap (Nominatim + Overpass API)."
)
