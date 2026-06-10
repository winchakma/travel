import os
import random
import requests
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

router = APIRouter()

RAPID_API_KEY = os.getenv("RAPID_API_KEY")

def get_local_images(category=None):
    base_path = os.path.join("..", "frontend", "images", "activity")
    if category:
        cat_path = os.path.join(base_path, category)
        if os.path.exists(cat_path):
            files = [f"images/activity/{category}/{f}" for f in os.listdir(cat_path) if f.endswith('.jpg') or f.endswith('.png')]
            if files:
                return files
    
    if os.path.exists(base_path):
        files = [f"images/activity/{f}" for f in os.listdir(base_path) if f.endswith('.jpg') or f.endswith('.png')]
        if files:
            return files
            
    return ["images/activity/pexels-asadphoto-1430676.jpg"]

@router.get("/")
async def search_activities(query: str = Query("Hiking")):
    if not RAPID_API_KEY:
        raise HTTPException(status_code=500, detail="RapidAPI Key not configured.")
        
    categories = ["Hiking", "Water Sports", "Photography", "Ski & Snow", "Cycling", "Horse Riding"]
    
    try:
        if query in categories:
            raise Exception("Category search, using fallback data")
            
        # Try to use Booking.com API to find activities, otherwise fallback
        dest_url = "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchDestination"
        headers = {
            "x-rapidapi-key": RAPID_API_KEY,
            "x-rapidapi-host": "booking-com15.p.rapidapi.com"
        }
        dest_res = requests.get(dest_url, headers=headers, params={"query": query})
        dest_res.raise_for_status()
        dest_data = dest_res.json()
        
        if not dest_data.get("status") or not dest_data.get("data"):
            raise Exception("No destination found, fallback")
            
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
                    "name": prop.get('name') + " Excursion",
                    "price": prop.get('priceBreakdown', {}).get('grossPrice', {}).get('value', 0) * 0.2,
                    "currency": prop.get('priceBreakdown', {}).get('grossPrice', {}).get('currency', 'USD'),
                    "rating": prop.get('reviewScore', 0),
                    "reviews": prop.get('reviewCount', 0),
                    "image": image
                })
            return {"status": "success", "data": results}
        else:
            raise Exception("No hotels found, fallback")
            
    except Exception as e:
        print(f"Fallback triggered for Activities: {e}")
        name_templates = [
            "Guided {} Experience", "Beginner's {} Class", "Full-Day {} Adventure", 
            "{} Excursion for Families", "Private {} Lesson", "Sunset {} Trip", 
            "Extreme {} Tour", "{} Photography Session", "Morning {} Workout", 
            "{} Explorer Package", "Group {} Activity", "{} Weekend Getaway", 
            "The Ultimate {} Challenge", "Relaxing {} Retreat", "{} Masterclass", 
            "{} with Local Guides", "Scenic {} Trail", "{} Coastal Tour", 
            "Intensive {} Training", "{} Discovery Day"
        ]
        
        mock_data = []
        cap_query = query.capitalize()
        
        # Determine the correct local folder mapping based on user's exact folder names
        category_map = {
            "Hiking": "hiking",
            "Water Sports": "Water Sports",
            "Photography": "Photography",
            "Ski & Snow": "Ski & Snow",
            "Cycling": "Cycling",
            "Horse Riding": "Horse Riding"
        }
        
        folder_name = category_map.get(query)
        category_images = get_local_images(folder_name)
        
        for i in range(20):
            mock_data.append({
                "id": i + 1,
                "name": name_templates[i].format(cap_query),
                "price": 20 + ((i * 13) % 150),
                "currency": "USD",
                "rating": round(4.0 + ((i * 7) % 10) * 0.1, 1),
                "reviews": 10 + ((i * 87) % 300),
                "image": category_images[i % len(category_images)]
            })
            
        return {"status": "success", "data": mock_data}
