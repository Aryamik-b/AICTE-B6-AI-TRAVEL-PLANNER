import math

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)

    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dl/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c


def estimate_travel_time(distance_km: float, mode: str):
    mode = (mode or "Any").lower()

    if mode == "train":
        low, high = distance_km / 60, distance_km / 45
        return (low, high, "Train")

    if mode == "bus":
        low, high = distance_km / 50, distance_km / 35
        return (low, high, "Bus")

    if mode == "flight":
    
        flight_hours = distance_km / 750
        low = flight_hours + 2.0
        high = flight_hours + 3.0
        return (low, high, "Flight")

    if distance_km < 250:

        low, high = distance_km / 60, distance_km / 45
        return (low, high, "Train/Car")
    else:
        flight_hours = distance_km / 750
        low = flight_hours + 2.0
        high = flight_hours + 3.0
        return (low, high, "Flight/Train")


def format_hours_range(low_h: float, high_h: float):
    low_h = max(0.5, low_h)
    high_h = max(low_h, high_h)
    return f"{low_h:.1f}–{high_h:.1f} hours"
