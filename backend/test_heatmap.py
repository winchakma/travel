import asyncio
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Ensure the backend directory is in the python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import init_db
from app.models.workout import Workout
from app.models.user import User

async def run_heatmap_test():
    load_dotenv()
    await init_db()
    
    email = 'winchakma123@gmail.com'
    user = await User.find_one(User.email == email)
    if not user:
        print(f"User {email} not found. Cannot run test.")
        return
    
    print(f"\n--- Heatmap Test for User: {user.firstName} {user.lastName} ---")
    
    # Clean up existing workouts for this test
    deleted = await Workout.find(Workout.user_id == str(user.id)).delete()
    print(f"Cleared {deleted.deleted_count} existing workouts.")
    
    # 1. Create fake data for the last 14 days
    # Let's say:
    # 0 workouts on days: 1, 4, 10
    # 1 workout on days: 0 (today), 2, 5, 8, 12, 13
    # 2 workouts on days: 3, 6, 9
    # 3+ workouts on days: 7, 11
    
    workout_pattern = {
        0: 1,  # today, index 13 in UI array
        1: 0,  
        2: 1,
        3: 2,
        4: 0,
        5: 1,
        6: 2,
        7: 3,
        8: 1,
        9: 2,
        10: 0,
        11: 4,
        12: 1,
        13: 1  # 13 days ago, index 0 in UI array
    }
    
    today = datetime.utcnow()
    total_inserted = 0
    
    for days_ago, num_workouts in workout_pattern.items():
        for i in range(num_workouts):
            workout_date = today - timedelta(days=days_ago)
            new_workout = Workout(
                exercise="Fake Exercise",
                calories=200,
                formScore=90,
                user_id=str(user.id),
                date=workout_date
            )
            await new_workout.insert()
            total_inserted += 1
            
    print(f"Inserted {total_inserted} fake workouts across 14 days.")
    
    # 2. Emulate frontend heatmap generation logic
    # (From frontend/js/script.js: generateHeatmap function)
    workouts = await Workout.find(Workout.user_id == str(user.id)).to_list()
    
    workout_counts = [0] * 14
    today_end = datetime.utcnow().replace(hour=23, minute=59, second=59, microsecond=999999)
    
    for w in workouts:
        diff_time = abs((today_end - w.date).total_seconds())
        diff_days = int(diff_time // (24 * 3600))
        if 0 <= diff_days < 14:
            workout_counts[13 - diff_days] += 1
            
    # 3. Print the heatmap matrix (2 rows, 7 columns) and colors
    print("\n--- Heatmap Generation Results ---")
    print("Array Index represents chronological order: [0] = 13 days ago, [13] = Today")
    print(f"Workout Counts Array: {workout_counts}")
    
    grid = []
    for i in range(2):
        row = []
        for j in range(7):
            day_index = (i * 7) + j
            count = workout_counts[day_index]
            
            color = 'bg-[#111]' # 0 workouts
            if count == 1:
                color = 'bg-yellow-900'
            elif count == 2:
                color = 'bg-yellow-700'
            elif count >= 3:
                color = 'bg-yellow-500'
                
            day_label = f"Day[{(13 - day_index)} ago]"
            if day_index == 13:
                day_label = "Today"
                
            row.append(f"[{day_label}: {count} w/o -> {color}]")
        grid.append(row)
        
    print("\nRow 1:")
    print(" | ".join(grid[0]))
    print("\nRow 2:")
    print(" | ".join(grid[1]))
    
    # 4. Consistency calculation
    active_days = sum(1 for c in workout_counts if c > 0)
    consistency = round((active_days / 14) * 100)
    print(f"\nConsistency Score: {consistency}% ({active_days} active days out of 14)")

if __name__ == "__main__":
    asyncio.run(run_heatmap_test())
