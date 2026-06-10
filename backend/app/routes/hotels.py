import os
import requests
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

router = APIRouter()

RAPID_API_KEY = os.getenv("RAPID_API_KEY")

@router.get("/")
async def search_hotels(query: str = Query("Bali")):
    if not RAPID_API_KEY:
        raise HTTPException(status_code=500, detail="RapidAPI Key not configured.")
        
    try:
        # Step 1: Resolve destination query to a dest_id
        dest_url = "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchDestination"
        headers = {
            "x-rapidapi-key": RAPID_API_KEY,
            "x-rapidapi-host": "booking-com15.p.rapidapi.com"
        }
        dest_res = requests.get(dest_url, headers=headers, params={"query": query})
        dest_res.raise_for_status()
        dest_data = dest_res.json()
        
        if not dest_data.get("status") or not dest_data.get("data"):
            raise HTTPException(status_code=404, detail="Destination not found.")
            
        # Get the first valid destination ID
        dest_id = dest_data["data"][0]["dest_id"]
        search_type = dest_data["data"][0]["search_type"]
        
        # Step 2: Fetch hotels for that dest_id
        hotels_url = "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchHotels"
        hotels_qs = {
            "dest_id": dest_id,
            "search_type": search_type,
            "arrival_date": "2026-10-10", # Using hardcoded future dates for demo
            "departure_date": "2026-10-15",
            "adults": "2",
            "room_qty": "1",
            "page_number": "1"
        }
        
        hotels_res = requests.get(hotels_url, headers=headers, params=hotels_qs)
        hotels_res.raise_for_status()
        hotels_data = hotels_res.json()
        
        if 'data' in hotels_data and 'hotels' in hotels_data['data']:
            # Return a simplified list of hotels
            results = []
            for h in hotels_data['data']['hotels'][:10]: # Limit to 10 to save bandwidth on frontend
                prop = h.get('property', {})
                results.append({
                    "id": prop.get('id'),
                    "name": prop.get('name'),
                    "price": prop.get('priceBreakdown', {}).get('grossPrice', {}).get('value', 0),
                    "currency": prop.get('priceBreakdown', {}).get('grossPrice', {}).get('currency', 'USD'),
                    "rating": prop.get('reviewScore', 0),
                    "reviews": prop.get('reviewCount', 0),
                    "image": prop.get('photoUrls', [''])[0] if prop.get('photoUrls') else ''
                })
            return {"status": "success", "data": results}
        else:
            return {"status": "success", "data": []}
            
    except Exception as e:
        print(f"RapidAPI Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch live hotels from RapidAPI.")
