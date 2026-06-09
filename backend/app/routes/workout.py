from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from app.routes.profile import get_current_user, validate_media_file
from app.models.workout import Workout
from app.models.user import User
from app.models.community import CommunityPost
import random
import cloudinary
import cloudinary.uploader
import os

router = APIRouter(prefix="/workouts", tags=["Workouts"])

@router.get("/")
async def get_workouts(current_user: User = Depends(get_current_user)):
    workouts = await Workout.find({"user_id": str(current_user.id)}).to_list()
    return workouts

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from typing import Optional
from fastapi import Request

@router.post("/verify")
async def verify_workout(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    form = await request.form()
    file = form.get("file")
    text_proof = form.get("text_proof")
    if not file and not text_proof:
        raise HTTPException(status_code=400, detail="Must provide either a file or a text proof.")

    # Integrate the AI Brain to calculate exact calories based on MET values
    from app.utils.ai_brain import calculate_calories_burned
    
    # Use user's weight for accurate calculation (default to 75.0 if not set)
    user_weight = current_user.weight if hasattr(current_user, 'weight') else 75.0
    
    exercise, calories, form_score = calculate_calories_burned(text_proof, user_weight)
    
    # Process Video/Photo Upload if provided
    video_url = None
    if file and hasattr(file, "filename") and file.filename:
        validate_media_file(file, max_size_mb=25)
        try:
            upload_result = cloudinary.uploader.upload(
                file.file,
                folder="elite_gym/workouts",
                resource_type="auto"
            )
            video_url = upload_result.get("secure_url")
        except Exception as e:
            print(f"[CLOUDINARY ERROR] Workout Media: {e}")

    # Persist Workout
    new_workout = Workout(
        exercise=exercise,
        calories=calories,
        formScore=form_score,
        user_id=str(current_user.id),
        videoUrl=video_url,
        text_proof=text_proof
    )
    await new_workout.insert()
    
    # Update user points
    current_user.points += 50
    await current_user.save()
    
    return {
        "exercise": exercise,
        "calories": calories,
        "formScore": form_score,
        "message": "Neural Analysis Complete!"
    }

from bson import ObjectId

@router.delete("/{workout_id}")
async def delete_workout(workout_id: str, current_user: User = Depends(get_current_user)):
    try:
        workout = await Workout.get(workout_id)
        if not workout:
            raise HTTPException(status_code=404, detail="Workout not found")
            
        if str(workout.user_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized to delete this workout")
            
        await workout.delete()
        
        # Optionally decrement points, but for now just delete the record
        # current_user.points = max(0, current_user.points - 50)
        # await current_user.save()
        
        return {"message": "Workout proof deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))