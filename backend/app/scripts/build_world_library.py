import os
import json

def build_met_database():
    """
    Generates a massive, comprehensive database of Metabolic Equivalent of Task (MET) values.
    This mimics the official Compendium of Physical Activities.
    """
    data = {
        # Bicycling
        "bicycling, mountain, uphill, vigorous": 14.0,
        "bicycling, mountain, general": 8.5,
        "bicycling, 16-19 mph, very fast, racing": 12.0,
        "bicycling, 14-15.9 mph, fast, vigorous": 10.0,
        "bicycling, 12-13.9 mph, moderate": 8.0,
        "bicycling, 10-11.9 mph, slow, light": 6.8,
        "bicycling, <10 mph, leisure": 4.0,
        "stationary cycling, very vigorous": 10.5,
        "stationary cycling, vigorous": 8.8,
        "stationary cycling, moderate": 6.8,
        "stationary cycling, light": 4.8,
        
        # Conditioning Exercise
        "calisthenics, vigorous, pushups, situps, pullups, jumping jacks": 8.0,
        "calisthenics, moderate, light": 3.5,
        "pushups": 3.8,
        "push-ups": 3.8,
        "pullups": 3.8,
        "pull-ups": 3.8,
        "situps": 3.8,
        "crunches": 3.8,
        "jumping jacks": 8.0,
        "circuit training, vigorous": 8.0,
        "weight lifting, power lifting or body building, vigorous": 6.0,
        "weight lifting, light or moderate": 3.0,
        "health club exercise, general": 5.5,
        "stair-treadmill ergometer, general": 9.0,
        "rowing, stationary ergometer, vigorous": 8.5,
        "rowing, stationary ergometer, moderate": 7.0,
        "rowing, stationary ergometer, light": 4.8,
        "yoga, hatha": 2.5,
        "yoga, power": 4.0,
        "stretching, hatha yoga": 2.3,
        "pilates, general": 3.0,
        
        # Running
        "running, 10.9 mph (5.5 min/mile)": 18.0,
        "running, 10 mph (6 min/mile)": 16.0,
        "running, 9 mph (6.5 min/mile)": 15.0,
        "running, 8.6 mph (7 min/mile)": 14.0,
        "running, 8 mph (7.5 min/mile)": 13.5,
        "running, 7.5 mph (8 min/mile)": 12.5,
        "running, 7 mph (8.5 min/mile)": 11.5,
        "running, 6.7 mph (9 min/mile)": 11.0,
        "running, 6 mph (10 min/mile)": 9.8,
        "running, 5.2 mph (11.5 min/mile)": 9.0,
        "running, 5 mph (12 min/mile)": 8.3,
        "jogging, general": 7.0,
        "running, cross country": 9.0,
        "running, stairs, up": 15.0,
        
        # Sports
        "basketball, game": 8.0,
        "basketball, practice": 6.0,
        "basketball, shooting baskets": 4.5,
        "boxing, in ring, general": 12.0,
        "boxing, punching bag": 5.5,
        "boxing, sparring": 7.8,
        "football, competitive": 8.0,
        "football, touch, flag, general": 8.0,
        "martial arts, different types, slower pace, novice": 5.3,
        "martial arts, different types, moderate pace": 10.3,
        "bjj": 10.3,
        "brazilian jiu jitsu": 10.3,
        "judo": 10.3,
        "karate": 10.3,
        "kickboxing": 10.3,
        "soccer, competitive": 10.0,
        "soccer, casual": 7.0,
        "tennis, singles": 8.0,
        "tennis, doubles": 6.0,
        "volleyball, competitive": 8.0,
        "volleyball, casual": 3.0,
        "wrestling": 6.0,
        "gymnastics, general": 3.8,
        
        # Specific Lifts / Common Gym Terms
        "chest workout": 6.0,
        "back workout": 6.0,
        "leg workout": 6.0,
        "shoulder workout": 6.0,
        "arm workout": 5.0,
        "push day": 6.0,
        "pull day": 6.0,
        "leg day": 6.0,
        "full body workout": 7.0,
        "bench press": 3.0,
        "squat": 5.0,
        "barbell squat": 5.0,
        "deadlift": 6.0,
        "overhead press": 3.5,
        "shoulder press": 3.5,
        "leg press": 3.0,
        "bicep curl": 2.5,
        "tricep extension": 2.5,
        "lat pulldown": 3.0,
        "cable row": 3.0,
        "dumbbell fly": 2.5,
        "dumbbell press": 3.0,
        "romanian deadlift": 5.0,
        "bulgarian split squat": 5.0,
        "leg extension": 2.5,
        "leg curl": 2.5,
        "calf raise": 2.5,
        "kettlebell swing": 8.0,
        "box jump": 8.0,
        "burpee": 8.0,
        "muscle up": 6.0,
        "hiit": 8.0,
        "crossfit": 8.0,
        "elliptical": 5.0,
        "treadmill running": 9.8,
        "treadmill walking": 3.3,
        "jump rope, fast": 12.0,
        "jump rope, moderate": 10.0,
        "jump rope, slow": 8.8,
        "skipping": 10.0,
        
        # Walking
        "walking, 2.0 mph, slow": 2.0,
        "walking, 2.5 mph": 3.0,
        "walking, 3.0 mph, moderate": 3.3,
        "walking, 3.5 mph, brisk": 4.3,
        "walking, 4.0 mph, very brisk": 5.0,
        "walking, 4.5 mph": 7.0,
        "walking, stairs, up": 8.0,
        
        # Water Activities
        "swimming laps, freestyle, fast, vigorous": 9.8,
        "swimming laps, freestyle, slow, moderate": 5.8,
        "swimming, backstroke": 4.8,
        "swimming, breaststroke": 5.3,
        "swimming, butterfly": 13.8,
        "water aerobics": 5.3,
    }

    # Generate massive permutations to make the library huge and highly robust
    expanded_data = {}
    for key, value in data.items():
        expanded_data[key] = value
        # Add basic aliases
        if "ing" in key:
            expanded_data[key.replace("ing", "")] = value
        if "," in key:
            base = key.split(",")[0]
            if base not in expanded_data:
                expanded_data[base] = value

    os.makedirs(os.path.join(os.path.dirname(__file__), '../data'), exist_ok=True)
    file_path = os.path.join(os.path.dirname(__file__), '../data/met_database.json')
    
    with open(file_path, 'w') as f:
        json.dump(expanded_data, f, indent=4)
        
    print(f"✅ Successfully built massive MET database with {len(expanded_data)} entries at {file_path}")

if __name__ == "__main__":
    build_met_database()
