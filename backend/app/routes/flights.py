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

@router.get("/search")
def search_flights(
    origin: str = Query(..., description="IATA code for origin, e.g., LHR"),
    destination: str = Query(..., description="IATA code for destination, e.g., JFK"),
    departure_date: str = Query(..., description="YYYY-MM-DD"),
    passengers: int = Query(1, description="Number of adult passengers")
):
    if not DUFFEL_API_KEY:
        raise HTTPException(status_code=500, detail="Duffel API key not configured")

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
            return {"status": "error", "message": f"Duffel API error: {req_res.text}"}
        
        req_data = req_res.json()
        offers = req_data.get("data", {}).get("offers", [])
        
        # Format the response
        formatted_flights = []
        # Sort by total amount
        offers.sort(key=lambda x: float(x.get('total_amount', 0)))
        
        # Return top 20 offers
        for offer in offers[:20]:
            slice_data = offer.get("slices", [{}])[0]
            segments = slice_data.get("segments", [])
            
            if not segments:
                continue
                
            first_segment = segments[0]
            last_segment = segments[-1]
            
            airline = offer.get("owner", {}).get("name", "Unknown Airline")
            price = offer.get("total_amount")
            currency = offer.get("total_currency")
            
            # Duration format from ISO (e.g., PT7H30M -> we will let frontend or keep it simple)
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
                "duration": duration, # Need parsing in JS
                "departure_time": dep_time,
                "arrival_time": arr_time,
                "stops": stop_text,
                "segments": formatted_segments
            })
            
        return {"status": "success", "flights": formatted_flights}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
