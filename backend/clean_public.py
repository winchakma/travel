import asyncio
import os
import sys
from dotenv import load_dotenv

# Ensure we can import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from app.database import init_db
from app.models.public import Review, Transformation

async def clean_data():
    await init_db()

    print("Purging fake Reviews...")
    await Review.find_all().delete()
    print("Fake Reviews deleted.")

    print("Purging fake Transformations...")
    await Transformation.find_all().delete()
    print("Fake Transformations deleted.")

    print("Database is now completely pure and empty.")

if __name__ == "__main__":
    asyncio.run(clean_data())
