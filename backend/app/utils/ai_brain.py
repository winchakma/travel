import re
import os
import json
import difflib
import requests
from typing import Dict, Tuple

# Load the massive Local Database
DB_PATH = os.path.join(os.path.dirname(__file__), '../data/met_database.json')
try:
    with open(DB_PATH, 'r') as f:
        MET_DB = json.load(f)
except FileNotFoundError:
    MET_DB = {"general training": 3.5}

def _estimate_duration_minutes(text: str) -> float:
    """Extracts duration from text."""
    text_lower = text.lower()
    
    min_match = re.search(r'(\d+)\s*(min|minute)', text_lower)
    if min_match: return float(min_match.group(1))
        
    hr_match = re.search(r'(\d+)\s*(hr|hour)', text_lower)
    if hr_match: return float(hr_match.group(1)) * 60.0
        
    reps_match = re.search(r'(\d+)\s*(rep|times|x)', text_lower)
    sets_match = re.search(r'(\d+)\s*(set)', text_lower)
    
    reps = int(reps_match.group(1)) if reps_match else 0
    sets = int(sets_match.group(1)) if sets_match else 1
    
    if reps > 0:
        total_reps = reps * sets
        return max(5.0, (total_reps * 4.0 / 60.0) * 1.5)
        
    if "workout" in text_lower or "training" in text_lower or "day" in text_lower or "session" in text_lower:
        return 60.0
        
    return 15.0

def _identify_exercise_and_met(text: str) -> Tuple[str, float]:
    """Uses Natural Language Processing (Fuzzy Matching) to search the massive JSON library."""
    text_lower = text.lower()
    
    # 1. Advanced Compound Detection (Full Body)
    body_parts = ["chest", "back", "leg", "shoulder", "arm", "bicep", "tricep", "belly", "core", "abs"]
    parts_mentioned = [part for part in body_parts if part in text_lower]
    
    if len(parts_mentioned) >= 3:
        return "Intense Full Body Workout", 7.0
    elif len(parts_mentioned) == 2:
        return f"{parts_mentioned[0].title()} & {parts_mentioned[1].title()} Split", 6.0
        
    # 2. Check for direct exact matches
    best_match = "General Training"
    best_met = 3.5
    
    for exercise, met in MET_DB.items():
        if exercise in text_lower:
            if met > best_met or best_match == "General Training":
                best_match = exercise
                best_met = met
                
    # 3. Smart Fuzzy Matching (Find the highest intensity match, not just the first one)
    if best_match == "General Training":
        words = text_lower.split()
        possible_matches = []
        for word in words:
            if len(word) < 4: continue # Skip small words
            matches = difflib.get_close_matches(word, MET_DB.keys(), n=1, cutoff=0.75)
            if matches:
                possible_matches.append(matches[0])
                
        if possible_matches:
            # Pick the match with the highest MET score to reward the user's effort
            best_match = max(possible_matches, key=lambda m: MET_DB[m])
            best_met = MET_DB[best_match]
                
    return best_match.title(), best_met

def calculate_calories_burned(text_proof: str, user_weight_kg: float) -> Tuple[str, int, int]:
    """Calculates exact calories using the massive local library."""
    if not text_proof or not text_proof.strip():
        return ("General Training", int((3.5 * 3.5 * user_weight_kg / 200) * 15), 90)
        
    exercise, met_value = _identify_exercise_and_met(text_proof)
    duration_mins = _estimate_duration_minutes(text_proof)
    
    calories = (met_value * 3.5 * user_weight_kg / 200) * duration_mins
    form_score = min(99, max(85, 80 + len(text_proof.split())))
    
    return (exercise, int(calories), int(form_score))

def fetch_world_nutrition(food_query: str) -> Dict[str, float]:
    """
    Connects to the open-source OpenFoodFacts API (The entire world's nutrition data).
    This requires ZERO paid API tokens.
    """
    try:
        url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms={food_query}&search_simple=1&action=process&json=1&page_size=1"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("products") and len(data["products"]) > 0:
                product = data["products"][0]
                nutriments = product.get("nutriments", {})
                return {
                    "food": product.get("product_name", food_query).title(),
                    "calories": nutriments.get("energy-kcal_100g", 0),
                    "protein": nutriments.get("proteins_100g", 0),
                    "carbs": nutriments.get("carbohydrates_100g", 0),
                    "fats": nutriments.get("fat_100g", 0)
                }
    except Exception as e:
        print(f"Error fetching global nutrition data: {e}")
    
    return {"food": food_query, "calories": 0, "protein": 0, "carbs": 0, "fats": 0}

def calculate_nutrition_needs(weight_kg: float, height_cm: float, age: int, is_male: bool, goal: str, activity_multiplier: float = 1.3) -> Dict[str, int]:
    """Harris-Benedict Equation for exact macro goals."""
    if is_male:
        bmr = (13.397 * weight_kg) + (4.799 * height_cm) - (5.677 * age) + 88.362
    else:
        bmr = (9.247 * weight_kg) + (3.098 * height_cm) - (4.330 * age) + 447.593
        
    tdee = bmr * activity_multiplier
    
    goal_lower = goal.lower() if goal else "maintenance"
    if "loss" in goal_lower or "six-pack" in goal_lower or "cut" in goal_lower:
        target_calories = tdee - 500
        protein_multiplier = 2.2 
    elif "gain" in goal_lower or "bulk" in goal_lower or "muscle" in goal_lower:
        target_calories = tdee + 300
        protein_multiplier = 1.8 
    else:
        target_calories = tdee
        protein_multiplier = 1.6 
        
    protein_grams = int(weight_kg * protein_multiplier)
    fat_grams = int((target_calories * 0.25) / 9) 
    
    protein_cals = protein_grams * 4
    fat_cals = fat_grams * 9
    carb_grams = int(max(0, target_calories - protein_cals - fat_cals) / 4)
    
    return {
        "calories": int(target_calories),
        "protein": protein_grams,
        "carbs": carb_grams,
        "fats": fat_grams
    }
