import asyncio
import os
from dotenv import load_dotenv
load_dotenv('.env')

async def run_test():
    from motor.motor_asyncio import AsyncIOMotorClient
    from beanie import init_beanie
    from app.models.user import User
    from app.models.admin import UserFeedback
    
    client = AsyncIOMotorClient(os.getenv("MONGODB_URL"))
    client.append_metadata = lambda x: None
    await init_beanie(database=client.elite_gym, document_models=[User, UserFeedback])
    
    print("Testing User.count()...")
    count = await User.find_all().count()
    print("User count:", count)
    
    print("Testing UserFeedback.find()...")
    try:
        feedbacks = await UserFeedback.find({"category": "praise"}).to_list()
        print("Feedbacks using dict:", len(feedbacks))
    except Exception as e:
        print("Error with dict find:", e)
        
    try:
        feedbacks2 = await UserFeedback.find(UserFeedback.category == "praise").to_list()
        print("Feedbacks using ==:", len(feedbacks2))
    except Exception as e:
        print("Error with == find:", e)

if __name__ == "__main__":
    asyncio.run(run_test())
