from fastapi import APIRouter
from app.models.user import User
from app.models.admin import UserFeedback, MentorshipRequest
from app.models.public import Transformation
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/public", tags=["Public"])

@router.get("/stats")
async def get_public_stats():
    live_users_count = await User.find_all().count()
    total_members = live_users_count

    # Calculate average rating based on UserFeedback
    feedbacks = await UserFeedback.find_all().to_list()
    avg_rating = 5.0 if len(feedbacks) > 0 else 0.0

    return {
        "totalMembers": total_members,
        "overallRating": avg_rating
    }

@router.get("/reviews")
async def get_public_reviews():
    # Return actual member feedback from the admin panel that are published
    feedbacks = await UserFeedback.find(UserFeedback.is_published == True).sort("-timestamp").limit(10).to_list()
    
    # Transform UserFeedback into the format expected by the frontend
    formatted_reviews = []
    for f in feedbacks:
        email_clean = f.userEmail.strip()
        user = await User.find_one({"email": {"$regex": f"^{email_clean}$", "$options": "i"}})
        pic = f"https://ui-avatars.com/api/?name={f.userName if f.userName else f.userEmail[0]}&background=f5e642&color=000"
        
        if user and getattr(user, 'profilePicture', None):
            pic = user.profilePicture
            
        formatted_reviews.append({
            "quote": f.message,
            "userName": f.userName if f.userName else f.userEmail.split('@')[0],
            "avatarUrl": pic,
            "location": "Verified Member",
            "rating": getattr(f, 'rating', 5)
        })
    return formatted_reviews

@router.get("/transformations")
async def get_public_transformations():
    # Return transformations sorted by orderIdx
    transformations = await Transformation.find_all().sort("orderIdx").to_list()
    return transformations

@router.post("/mentorship")
async def submit_mentorship(data: dict):
    await MentorshipRequest(
        name=data.get("name", "Anonymous"),
        email=data.get("email", ""),
        preferred_date=data.get("preferred_date", ""),
        fitness_level=data.get("fitness_level", ""),
        message=data.get("message", "")
    ).insert()
    return {"status": "success", "message": "Mentorship request submitted successfully."}
