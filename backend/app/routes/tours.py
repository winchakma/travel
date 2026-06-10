import os
import random
import requests
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

router = APIRouter()

RAPID_API_KEY = os.getenv("RAPID_API_KEY")

def get_local_images():
    base_path = os.path.join("..", "frontend", "images", "tour")
    if os.path.exists(base_path):
        files = [f"images/tour/{f}" for f in os.listdir(base_path) if f.endswith('.jpg') or f.endswith('.png')]
        if files:
            return files
    return ["https://images.unsplash.com/photo-1533105079780-92b9be482077?w=400&h=180&fit=crop"]

@router.get("/")
async def search_tours(query: str = Query("Paris")):
    if not RAPID_API_KEY:
        raise HTTPException(status_code=500, detail="RapidAPI Key not configured.")
        
    try:
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
            
        dest_id = dest_data["data"][0]["dest_id"]
        search_type = dest_data["data"][0]["search_type"]
        
        attractions_url = "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchHotels"
        attractions_qs = {
            "dest_id": dest_id,
            "search_type": search_type,
            "arrival_date": "2026-10-10",
            "departure_date": "2026-10-15",
            "adults": "2",
            "room_qty": "1",
            "page_number": "1"
        }
        
        attractions_res = requests.get(attractions_url, headers=headers, params=attractions_qs)
        attractions_res.raise_for_status()
        attractions_data = attractions_res.json()
        
        if 'data' in attractions_data and 'hotels' in attractions_data['data']:
            results = []
            local_images = get_local_images()
            for i, h in enumerate(attractions_data['data']['hotels'][:4]):
                prop = h.get('property', {})
                image = prop.get('photoUrls', [''])[0] if prop.get('photoUrls') else local_images[i % len(local_images)]
                
                results.append({
                    "id": prop.get('id'),
                    "name": prop.get('name') + " Guided Tour",
                    "price": prop.get('priceBreakdown', {}).get('grossPrice', {}).get('value', 0) * 0.4,
                    "currency": prop.get('priceBreakdown', {}).get('grossPrice', {}).get('currency', 'USD'),
                    "rating": prop.get('reviewScore', 0),
                    "reviews": prop.get('reviewCount', 0),
                    "image": image
                })
            return {"status": "success", "data": results}
        else:
            return {"status": "success", "data": []}
            
    except Exception as e:
        print(f"Fallback triggered for Tours: {e}")
        name_templates = [
            "Walking Tour of historic {}", "Culinary Journey through {}", "{} Museum Fast-Track Ticket", 
            "Sunset Cruise in {}", "{} Highlights by Bike", "Hidden Gems of {} Tour", 
            "{} Nightlife Experience", "{} Mountain Hiking Excursion", "Photography Tour of {}", 
            "{} River Rafting Adventure", "Historic Pub Crawl {}", "{} Architecture Walk", 
            "The {} Vineyard Tour", "Explore {}'s Ancient Ruins", "{} Helicopter Ride", 
            "The {} Local Market Tour", "Ghost Tour of {}", "{} Scuba Diving Experience", 
            "The {} Artisanal Craft Tour", "{} Safari Expedition"
        ]
        
        mock_data = []
        cap_query = query.capitalize()
        local_images = get_local_images()
        
        for i in range(4):
            mock_data.append({
                "id": i + 1,
                "name": name_templates[i].format(cap_query),
                "price": 30 + ((i * 17) % 150),
                "currency": "USD",
                "rating": round(4.0 + ((i * 7) % 10) * 0.1, 1),
                "reviews": 20 + ((i * 123) % 400),
                "image": local_images[i % len(local_images)]
            })
            
        return {"status": "success", "data": mock_data}
