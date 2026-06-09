from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
import os
from dotenv import load_dotenv
from app.models.user import User, AttendanceLog
from app.models.admin import SupportMessage
from app.models import Booking, Activity, Order, ClassSchedule, Notification, Video, UserFeedback, MentorshipRequest
from app.models.support import SupportSession, SupportChatMessage
from app.models.community import CommunityPost, CommunityChat, PrivateMessage, SocialLink, Story, SocialProfile, CommunityForumTopic, CommunityEvent, MemberSpotlight
from app.models.public import Review, Transformation

load_dotenv()

async def init_db():
    mongodb_url = os.getenv("MONGODB_URL")
    if not mongodb_url:
        print("[CRITICAL] MONGODB_URL is missing from Environment Variables!", flush=True)
        return
        
    print(f"Connecting to MongoDB... (Target: {mongodb_url.split('@')[-1]})", flush=True)
    
    try:
        # Added 10s timeout to fail faster than Render's health check
        client = AsyncIOMotorClient(mongodb_url, serverSelectionTimeoutMS=10000)
        
        # Verify connection immediately
        await client.admin.command('ping')
        print("MongoDB Ping Successful.", flush=True)
        
        db_name = mongodb_url.split("/")[-1].split("?")[0] or "gotrip_db"
        
        # NUCLEAR GHOST FIX: 
        # Force-override the attribute to bypass Motor's dynamic __getattr__.
        client.append_metadata = lambda x: None
            
        await init_beanie(
            database=client[db_name],
            document_models=[
                User, AttendanceLog, Booking, Activity, Order, ClassSchedule, Notification, Video, UserFeedback, MentorshipRequest, SupportMessage, 
                SupportSession, SupportChatMessage,
                CommunityPost, CommunityChat, PrivateMessage, SocialLink, Story, SocialProfile,
                CommunityForumTopic, CommunityEvent, MemberSpotlight,
                Review, Transformation
            ]
        )

        print(f"Beanie initialized with database: {db_name}", flush=True)
    except Exception as e:
        print(f"[DATABASE ERROR] Connection failed: {str(e)}", flush=True)
        raise e
