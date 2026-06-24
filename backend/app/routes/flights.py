from fastapi import APIRouter, HTTPException, Query
import os
import requests

router = APIRouter()

DUFFEL_API_KEY = os.getenv("DUFFEL_API_KEY")
DUFFEL_BASE_URL = "https://api.duffel.com/air"

headers = {
    "Authorization": f"Bearer {DUFFEL_API_KEY}",
    "Duffel-Version": "v2",
    "Content-Type": "application/json"
}

@router.get("/places")
def search_places(query: str = Query(..., description="Search query for city or airport")):
    if not DUFFEL_API_KEY:
        return {"status": "success", "places": get_fallback_places(query)}
    try:
        req_res = requests.get(f"https://api.duffel.com/places/suggestions?query={query}", headers=headers)
        if req_res.status_code != 200:
            return {"status": "success", "places": get_fallback_places(query)}
        
        data = req_res.json().get("data", [])
        formatted_places = []
        for place in data:
            if place.get("iata_code"):
                place_type = place.get("type", "unknown")
                country = place.get("iata_country_code", "")
                formatted_places.append({
                    "id": place.get("id"),
                    "name": place.get("name"),
                    "iata_code": place.get("iata_code"),
                    "type": place_type,
                    "country": country
                })
        return {"status": "success", "places": formatted_places}
    except Exception:
        return {"status": "success", "places": get_fallback_places(query)}

def get_fallback_places(query: str):
    suggestions = [
        {"name": "London Heathrow Airport", "iata_code": "LHR", "type": "airport", "country": "GB"},
        {"name": "New York John F. Kennedy International", "iata_code": "JFK", "type": "airport", "country": "US"},
        {"name": "Paris Charles de Gaulle", "iata_code": "CDG", "type": "airport", "country": "FR"},
        {"name": "Tokyo Haneda", "iata_code": "HND", "type": "airport", "country": "JP"},
        {"name": "Bali Ngurah Rai", "iata_code": "DPS", "type": "airport", "country": "ID"},
        {"name": "Singapore Changi", "iata_code": "SIN", "type": "airport", "country": "SG"}
    ]
    query_clean = query.lower()
    results = [s for s in suggestions if query_clean in s["name"].lower() or query_clean in s["iata_code"].lower()]
    return results if results else suggestions[:3]

@router.get("/search")
def search_flights(
    origin: str = Query(..., description="IATA code for origin, e.g., LHR"),
    destination: str = Query(..., description="IATA code for destination, e.g., JFK"),
    departure_date: str = Query(..., description="YYYY-MM-DD"),
    passengers: int = Query(1, description="Number of adult passengers")
):
    if not DUFFEL_API_KEY:
        return {"status": "success", "flights": get_fallback_flights(origin, destination, departure_date, passengers)}

    # Step 1: Create an Offer Request
    payload = {
        "data": {
            "slices": [
                {
                    "origin": origin,
                    "destination": destination,
                    "departure_date": departure_date
                }
            ],
            "passengers": [{"type": "adult"} for _ in range(passengers)],
            "cabin_class": "economy",
            "return_offers": True
        }
    }

    try:
        req_res = requests.post(f"{DUFFEL_BASE_URL}/offer_requests", json=payload, headers=headers)
        if req_res.status_code != 201 and req_res.status_code != 200:
            return {"status": "success", "flights": get_fallback_flights(origin, destination, departure_date, passengers)}
        
        req_data = req_res.json()
        offers = req_data.get("data", {}).get("offers", [])
        
        formatted_flights = []
        offers.sort(key=lambda x: float(x.get('total_amount', 0)))
        
        for offer in offers[:4]:
            slice_data = offer.get("slices", [{}])[0]
            segments = slice_data.get("segments", [])
            
            if not segments:
                continue
                
            first_segment = segments[0]
            last_segment = segments[-1]
            
            airline = offer.get("owner", {}).get("name", "Unknown Airline")
            price = offer.get("total_amount")
            currency = offer.get("total_currency")
            duration = slice_data.get("duration", "")
            dep_time = first_segment.get("departing_at", "")
            arr_time = last_segment.get("arriving_at", "")
            
            stops = len(segments) - 1
            stop_text = "Direct" if stops == 0 else f"{stops} Stop(s)"
            
            formatted_segments = []
            for seg in segments:
                formatted_segments.append({
                    "origin": seg.get("origin", {}).get("iata_code", "N/A"),
                    "destination": seg.get("destination", {}).get("iata_code", "N/A"),
                    "departing_at": seg.get("departing_at", ""),
                    "arriving_at": seg.get("arriving_at", ""),
                    "airline": seg.get("operating_carrier", {}).get("name", airline),
                    "flight_number": seg.get("operating_carrier_flight_number", "")
                })

            formatted_flights.append({
                "id": offer.get("id"),
                "airline": airline,
                "price": price,
                "currency": currency,
                "duration": duration,
                "departure_time": dep_time,
                "arrival_time": arr_time,
                "stops": stop_text,
                "segments": formatted_segments
            })
            
        return {"status": "success", "flights": formatted_flights}
        
    except Exception:
        return {"status": "success", "flights": get_fallback_flights(origin, destination, departure_date, passengers)}

def get_fallback_flights(origin: str, destination: str, departure_date: str, passengers: int):
    airlines = ["Skyline Airways", "Global Connect", "EcoJet", "Star Clipper", "Apex Air"]
    mock_flights = []
    
    for i in range(4):
        price = 150 + ((i * 87) % 350)
        dep_hour = (8 + i * 4) % 24
        arr_hour = (dep_hour + 2 + i) % 24
        
        dep_time = f"{departure_date}T{dep_hour:02d}:00:00Z"
        arr_time = f"{departure_date}T{arr_hour:02d}:00:00Z"
        
        mock_flights.append({
            "id": f"mock-offer-{i}",
            "airline": airlines[i % len(airlines)],
            "price": str(price * passengers),
            "currency": "USD",
            "duration": f"PT{2+i}H30M",
            "departure_time": dep_time,
            "arrival_time": arr_time,
            "stops": "Direct" if i % 2 == 0 else "1 Stop(s)",
            "segments": [
                {
                    "origin": origin.upper(),
                    "destination": destination.upper(),
                    "departing_at": dep_time,
                    "arriving_at": arr_time,
                    "airline": airlines[i % len(airlines)],
                    "flight_number": f"FL-{100 + i * 23}"
                }
            ]
        })
    return mock_flights
