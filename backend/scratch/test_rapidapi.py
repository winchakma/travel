import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("RAPID_API_KEY")
url = "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchHotels"

querystring = {
    "dest_id": "-2701757", # Ubud, Bali
    "search_type": "city",
    "arrival_date": "2026-10-10",
    "departure_date": "2026-10-15",
    "adults": "2",
    "room_qty": "1",
    "page_number": "1"
}

headers = {
	"x-rapidapi-key": api_key,
	"x-rapidapi-host": "booking-com15.p.rapidapi.com"
}

response = requests.get(url, headers=headers, params=querystring)
data = response.json()
print("Keys in data:", data.keys())
if 'data' in data and 'hotels' in data['data']:
    hotels = data['data']['hotels']
    print(f"Found {len(hotels)} hotels. First hotel:")
    if len(hotels) > 0:
        print(hotels[0])
else:
    print(data)
