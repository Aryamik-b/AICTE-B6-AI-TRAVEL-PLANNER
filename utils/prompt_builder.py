def _format_list(items, fallback="- Not available"):
    if not items:
        return fallback
    return "\n".join([f"- {x}" for x in items])


def _format_dict_sections(data: dict, fallback="Not available"):
    """
    Converts dict like:
    {"Beaches": ["a","b"], "Hills": ["x"]}

    Into:
    Beaches:
    - a
    - b

    Hills:
    - x
    """
    if not data:
        return fallback

    lines = []
    found_any = False

    for k, v in data.items():
        if v:
            found_any = True
            lines.append(f"{k}:")
            lines.extend([f"- {x}" for x in v])
            lines.append("") 

    if not found_any:
        return fallback

    return "\n".join(lines).strip()


def build_prompt(
    destination_full: str,
    destination_city: str,
    departure_full: str,
    days: int,
    budget: str,
    currency: str,
    travel_type: str,
    transport_pref: str,
    interests: list,
    attractions: list,
    city_categories: dict,
    nearby_trips: dict,
) -> str:
    """
    Build one strong prompt (no template files needed).
    Includes:
    - City categories (beaches/hills/adventure etc.)
    - Nearby day trips (within 150-200 km)
    - Currency control (USD/EUR/INR etc.)
    """

    currency = (currency or "INR").strip().upper()

    interests_text = ", ".join(interests) if interests else "General"
    attractions_text = _format_list(attractions, fallback="- Not available")

    city_categories_text = _format_dict_sections(city_categories, fallback="Not available")
    nearby_trips_text = _format_dict_sections(nearby_trips, fallback="Not available")

    prompt = f"""
You are a professional travel planner.

Create a {days}-day itinerary that is exciting, realistic, and not overloaded.

Trip details:
- Destination: {destination_full if destination_full else "Not specified"}
- City: {destination_city if destination_city else "Not specified"}
- Departure city: {departure_full if departure_full else "Not specified"}
- Budget level: {budget}
- Travel type: {travel_type}
- Transport preference: {transport_pref}
- Interests: {interests_text}
- Currency to use for all costs: {currency}

General attractions around {destination_city}:
{attractions_text}

CITY HIGHLIGHTS (within city / nearby):
{city_categories_text}

NEARBY DAY TRIPS (within ~150-200 km from {destination_city}):
{nearby_trips_text}

IMPORTANT OUTPUT RULES:
- You MUST include ALL headings below in the exact same order.
- Do NOT skip any section.
- If something is missing, write "Not available".
- Include at least one nearby day trip if available.
- Include beaches / hill stations / waterfalls / adventure / water parks if available.
- Costs must be approximate and clearly mentioned as estimates.
- Use the currency: {currency}

Return the response with these Markdown headings:

## Day-wise Itinerary
Day 1:
Day 2:
...

## Transport Plan
- Inter-city travel (from departure city)
- Local travel inside destination (auto/cab/metro/bus/rental)
- Daily movement strategy

## Estimated Budget Breakdown ({currency})
- Transport:
- Stay:
- Food:
- Activities:
- Total Estimated Range:

## Food Recommendations
- At least 5 local dishes
- At least 3 recommended markets/areas/restaurants
- Mention budget-friendly + premium options

## Travel Tips
- Best time to visit
- Safety and crowd tips
- Packing checklist
"""
    return prompt.strip()
