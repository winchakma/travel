import asyncio
import os
import sys
from dotenv import load_dotenv

# Ensure we can import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from app.database import init_db
from app.models.public import Review, Transformation

async def seed_data():
    await init_db()

    print("Checking if Reviews exist...")
    existing_reviews = await Review.find_all().to_list()
    if len(existing_reviews) == 0:
        print("Seeding Reviews...")
        reviews = [
            Review(
                userName="Marcus Johnson",
                location="New York, USA",
                avatarUrl="https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=90&h=90&fit=crop",
                quote="I have NEVER liked working out, especially in a gym! I LOVE East Blue! All of the trainers are so encouraging and helpful. I feel better than I have felt in years. I am 58 years old — if I can do it, so can you!",
                rating=5.0
            ),
            Review(
                userName="Aisha Rahman",
                location="London, UK",
                avatarUrl="https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=90&h=90&fit=crop",
                quote="I've seen more results in 6 months with East Blue than in 5 years at my old gym. The coaches are knowledgeable and make the workouts genuinely enjoyable. Best fitness decision I ever made.",
                rating=5.0
            ),
            Review(
                userName="Carlos Mendez",
                location="Sydney, Australia",
                avatarUrl="https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?w=90&h=90&fit=crop",
                quote="East Blue is not just a place to work out — it's a family. The community is incredible, non-judgmental, and will celebrate every victory with you. It completely changed my relationship with fitness.",
                rating=4.9
            )
        ]
        for r in reviews:
            await r.insert()
        print("Reviews seeded!")
    else:
        print("Reviews already exist.")

    print("Checking if Transformations exist...")
    existing_trans = await Transformation.find_all().to_list()
    if len(existing_trans) == 0:
        print("Seeding Transformations...")
        transformations = [
            Transformation(
                userName="Mark Stevens",
                badge="Elite Member since 2023",
                avatarUrl="https://ui-avatars.com/api/?name=Mark+S&background=f5e642&color=000",
                quote="The environment at East Blue is unlike any other. I lost 15kg of fat and gained muscle mass I never thought possible. The personalized tracking and HIIT sessions were game-changers.",
                beforeImgUrl="img/trans-1-before.png",
                afterImgUrl="img/trans-1-after.png",
                stat1Value="-15kg",
                stat1Label="Weight Loss",
                stat2Value="+8kg",
                stat2Label="Muscle Gain",
                orderIdx=0
            ),
            Transformation(
                userName="Sarah Kovac",
                badge="Transformation Winner",
                avatarUrl="https://ui-avatars.com/api/?name=Sarah+K&background=f5e642&color=000",
                quote="I joined for the community, but stayed for the results. My strength tripled in 12 weeks, and for the first time in my life, I actually look forward to leg day. The coaching is world-class.",
                beforeImgUrl="",
                afterImgUrl="",
                stat1Value="3X",
                stat1Label="Strength",
                stat2Value="12wk",
                stat2Label="Journey",
                orderIdx=1
            ),
            Transformation(
                userName="James Liang",
                badge="Performance Athlete",
                avatarUrl="https://ui-avatars.com/api/?name=James+L&background=f5e642&color=000",
                quote="As a busy professional, I needed efficiency. The 45-minute sessions at East Blue are the most productive part of my day. I'm in the best shape of my life at 45.",
                beforeImgUrl="",
                afterImgUrl="",
                stat1Value="-12%",
                stat1Label="Body Fat",
                stat2Value="Best",
                stat2Label="Conditioning",
                orderIdx=2
            )
        ]
        for t in transformations:
            await t.insert()
        print("Transformations seeded!")
    else:
        print("Transformations already exist.")

    print("Seed complete.")

if __name__ == "__main__":
    asyncio.run(seed_data())
