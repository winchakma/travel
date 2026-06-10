import os
import re
import random

frontend_dir = r"c:\Users\user\Desktop\mytravelproject\frontend"

# Load local images for different categories
local_images = {
    "hotel": [f"images/hotel/{f}" for f in os.listdir(os.path.join(frontend_dir, "images", "hotel")) if f.endswith('.jpg')],
    "tour": [f"images/tour/{f}" for f in os.listdir(os.path.join(frontend_dir, "images", "tour")) if f.endswith('.jpg')],
    "cruise": [f"images/Cruise/{f}" for f in os.listdir(os.path.join(frontend_dir, "images", "Cruise")) if f.endswith('.jpg')],
    "activity": [f"images/activity/{f}" for f in os.listdir(os.path.join(frontend_dir, "images", "activity")) if f.endswith('.jpg')],
    "rental": [f"images/rental/{f}" for f in os.listdir(os.path.join(frontend_dir, "images", "rental")) if f.endswith('.jpg')]
}

# Regex to match Unsplash URLs
unsplash_pattern = re.compile(r'https://images\.unsplash\.com/photo-[a-zA-Z0-9-]+\?w=[0-9]+&h=[0-9]+&fit=crop')

for root, _, files in os.walk(frontend_dir):
    for filename in files:
        if filename.endswith(".html"):
            filepath = os.path.join(root, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Decide which category to pull images from based on the filename
            category = "hotel" # Default
            if "cruise" in filename.lower(): category = "cruise"
            elif "tour" in filename.lower(): category = "tour"
            elif "activity" in filename.lower(): category = "activity"
            elif "rental" in filename.lower() or "apartment" in filename.lower(): category = "rental"
            elif "flight" in filename.lower(): category = "tour" # No flight images, use tours
            
            # Find all unsplash matches
            matches = unsplash_pattern.findall(content)
            
            if matches:
                # Replace each match with a random image from the chosen category
                for match in matches:
                    replacement = random.choice(local_images[category])
                    content = content.replace(match, replacement, 1)
                    
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Replaced {len(matches)} images in {filename}")
