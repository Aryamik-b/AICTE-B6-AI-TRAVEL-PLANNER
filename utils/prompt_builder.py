def _format_list(items, fallback="- Not available"):
    if not items:
        return fallback
    return "\n".join([f"- {x}" for x in items])


def _format_dict_sections(data: dict, fallback="Not available"):
    """
    Converts dict like:
    {"Beaches": ["a","b"], "Hills": ["x"]}
    Into formatted sections with limits to save tokens.
    """
    if not data:
        return fallback

    lines = []
    found_any = False

    for k, v in data.items():
        if v:
            found_any = True
            # LIMIT to 5 items per category to save tokens
            limited_v = v[:5]
            lines.append(f"{k}:")
            lines.extend([f"- {x}" for x in limited_v])
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
    travel_time_hint: str = "Not available",
) -> str:
    """
    OPTIMIZED: Shorter prompt to leave more tokens for response generation.
    """

    currency = (currency or "INR").strip().upper()
    interests_text = ", ".join(interests) if interests else "General"
    
    # LIMIT attractions to top 8 to save tokens
    attractions_text = _format_list(attractions[:8], fallback="- Not available")
    
    # LIMIT categories (already limited to 5 per category in _format_dict_sections)
    city_categories_text = _format_dict_sections(city_categories, fallback="Not available")
    nearby_trips_text = _format_dict_sections(nearby_trips, fallback="Not available")

    # STREAMLINED PROMPT - removed redundant rules
    prompt = f"""You are a travel planner. Create a {days}-day itinerary for {destination_city}.

TRIP DETAILS:
- Departure: {departure_full}
- Budget: {budget} | Transport: {transport_pref}
- Interests: {interests_text}
- Currency: {currency}
- Travel time: {travel_time_hint}

AVAILABLE PLACES:
{city_categories_text}

{nearby_trips_text}

RULES:
1. Use ONLY places listed above (no invented names)
2. 2-4 places per day (realistic pace)
3. Prefer tourist attractions over residential areas
4. Include timings and costs in {currency}
5. Include all sections below

OUTPUT FORMAT:

## Day-wise Itinerary
Day 1: [Morning/Afternoon/Evening activities]
Day 2: ...
[Continue for all {days} days]

## Transport Plan
- Inter-city: [mode and cost]
- Local: [transport options]

## Estimated Budget Breakdown ({currency})
- Transport: {currency} X-Y
- Stay: {currency} X-Y
- Food: {currency} X-Y
- Activities: {currency} X-Y
- Total: {currency} X-Y

## Food Recommendations
- 5 local dishes
- 3 restaurants/areas
- Budget + premium options

## Travel Tips
- Best time to visit
- Safety tips
- Packing essentials
"""
    return prompt.strip()