import os
import random
import requests
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

router = APIRouter()

RAPID_API_KEY = os.getenv("RAPID_API_KEY")

def get_local_images(category=None):
    base_path = os.path.join("..", "frontend", "images", "rental")
    if category and category.lower() != "villa":
        cat_path = os.path.join(base_path, category.lower())
        if os.path.exists(cat_path):
            files = [f"images/rental/{category.lower()}/{f}" for f in os.listdir(cat_path) if f.endswith('.jpg') or f.endswith('.png')]
            if files:
                return files
    
    if os.path.exists(base_path):
        files = [f"images/rental/{f}" for f in os.listdir(base_path) if f.endswith('.jpg') or f.endswith('.png')]
        if files:
            return files
            
    return ["https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?w=400&h=180&fit=crop"]

@router.get("/")
async def search_rentals(query: str = Query("Bali")):
    if not RAPID_API_KEY:
        raise HTTPException(status_code=500, detail="RapidAPI Key not configured.")
        
    categories = ["Villa", "Apartment", "Cabin", "Camping", "Beachfront", "Mountain"]
    
    try:
        if query in categories:
            raise Exception("Category search, using fallback data")
            
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
            
        dest_id = dest_data["data"][0]["dest_id"]
        search_type = dest_data["data"][0]["search_type"]
        
        hotels_url = "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchHotels"
        hotels_qs = {
            "dest_id": dest_id,
            "search_type": search_type,
            "arrival_date": "2026-10-10",
            "departure_date": "2026-10-15",
            "adults": "2",
            "room_qty": "1",
            "page_number": "1"
        }
        
        hotels_res = requests.get(hotels_url, headers=headers, params=hotels_qs)
        hotels_res.raise_for_status()
        hotels_data = hotels_res.json()
        
        if 'data' in hotels_data and 'hotels' in hotels_data['data']:
            results = []
            local_images = get_local_images()
            for i, h in enumerate(hotels_data['data']['hotels'][:20]):
                prop = h.get('property', {})
                image = prop.get('photoUrls', [''])[0] if prop.get('photoUrls') else local_images[i % len(local_images)]
                
                results.append({
                    "id": prop.get('id'),
                    "name": prop.get('name'),
                    "price": prop.get('priceBreakdown', {}).get('grossPrice', {}).get('value', 0),
                    "currency": prop.get('priceBreakdown', {}).get('grossPrice', {}).get('currency', 'USD'),
                    "rating": prop.get('reviewScore', 0),
                    "reviews": prop.get('reviewCount', 0),
                    "image": image
                })
            return {"status": "success", "data": results}
        else:
            return {"status": "success", "data": []}
            
    except Exception as e:
        print(f"Fallback triggered for Rentals: {e}")
        name_templates = [
            "Luxury Villa with Private Pool in {}", "Modern Apartment in Central {}", 
            "Beachfront Cottage in {}", "Cozy Mountain Cabin near {}", 
            "{} Downtown Loft", "The {} Retreat House", 
            "Panoramic {} Penthouse", "Rustic Cabin in {}", "The Pearl of {} Villas", 
            "{} Riverside Apartment", "Golden Sands {} Rental", "{} Boutique Studio", 
            "The {} Country House", "Emerald {} Condo", "{} Skyline Penthouse", 
            "The {} Oasis Villa", "Crown {} Family Home", "{} Seaside Bungalow", 
            "The {} Enclave Apartment", "{} Majestic Manor"
        ]
        
        mock_data = []
        cap_query = query.capitalize()
        
        # Use images tailored to the specific category they clicked
        category_images = get_local_images(query if query in categories else None)
        
        for i in range(20):
            mock_data.append({
                "id": i + 1,
                "name": name_templates[i].format(cap_query),
                "price": 80 + ((i * 43) % 400),
                "currency": "USD",
                "rating": round(4.0 + ((i * 7) % 10) * 0.1, 1),
                "reviews": 50 + ((i * 87) % 600),
                "image": category_images[i % len(category_images)]
            })
            
        return {"status": "success", "data": mock_data}
