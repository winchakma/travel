import asyncio
import os
from dotenv import load_dotenv
import sys

# Add current directory to path so we can import app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import init_db
from app.models.user import User

async def promote_to_super_admin(email: str):
    print(f"Connecting to database to promote {email}...")
    await init_db()
    
    user = await User.find_one(User.email == email)
    if not user:
        print(f"ERROR: User with email {email} not found. Please sign up on the website first.")
        return
    
    user.role = "super_admin"
    await user.save()
    print(f"SUCCESS: {email} is now a SUPER ADMIN.")
    print("You can now access the admin panel at: https://your-vercel-link.vercel.app/admin.html")

if __name__ == "__main__":
    load_dotenv()
    if len(sys.argv) < 2:
        print("Usage: python promote_admin.py <email>")
    else:
        asyncio.run(promote_to_super_admin(sys.argv[1]))
