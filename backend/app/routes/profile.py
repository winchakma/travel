from fastapi import APIRouter, HTTPException, Depends, Form, UploadFile, File
from app.models.user import User
from app.models.admin import Activity, Notification, ClassSchedule, Video, Booking, UserFeedback
from app.models.workout import Workout
from app.models.community import CommunityPost
from app.schemas.user import ChangePasswordRequest
from app.routes.auth import get_current_user, pwd_context
from datetime import datetime, timezone
from beanie import PydanticObjectId
from typing import Optional
import json
import os

import cloudinary
import cloudinary.uploader
import os

# Cloudinary Config
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

router = APIRouter(prefix="/user", tags=["Profile"])

def validate_media_file(file: UploadFile, max_size_mb: int = 10):
    if not file or not file.filename:
        return
    # 1. Size Validation (prevent memory saturation)
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    
    if size > max_size_mb * 1024 * 1024:
        raise HTTPException(
            status_code=400, 
            detail=f"File exceeds maximum allowed size of {max_size_mb}MB"
        )
        
    # 2. Extension & MIME Type Check (prevent remote script execution)
    allowed_types = {
        "image/jpeg", "image/png", "image/webp", "image/gif", "image/jpg",
        "video/mp4", "video/webm", "video/quicktime", "video/ogg",
        "audio/mpeg", "audio/mp3", "audio/wav", "audio/ogg", "audio/m4a", "audio/x-m4a"
    }
    content_type = file.content_type
    if not content_type or content_type.lower() not in allowed_types:
        ext = os.path.splitext(file.filename)[1].lower() if file.filename else ""
        allowed_exts = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".mp4", ".mov", ".webm", ".ogg", ".mp3", ".wav", ".m4a"}
        if ext not in allowed_exts:
            raise HTTPException(
                status_code=400, 
                detail="Unsupported media format. Only Images, Video, and Audio are allowed."
            )

@router.get("/me")
async def get_profile(token: str):
    user = await get_current_user(token)
    return user

@router.get("/orders")
async def get_my_orders(token: str):
    user = await get_current_user(token)
    from app.models.admin import Order
    orders = await Order.find(Order.userEmail == user.email).sort("-timestamp").to_list()
    return orders

@router.get("/ai-insights")
async def get_ai_insights(token: str):
    user = await get_current_user(token)
    
    # 1. Fetch today's workouts to get cumulative calories burned today
    from app.models.workout import Workout
    from datetime import datetime, timezone
    
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    todays_workouts = await Workout.find(
        {"user_id": str(user.id), "date": {"$gte": today_start}}
    ).to_list()
    
    burned_today = sum(w.calories for w in todays_workouts)
    
    # 2. Use AI Brain to calculate macros based on the user's profile and goal
    from app.utils.ai_brain import calculate_nutrition_needs
    
    # Default height/age/gender if not in user model (for now assuming standard adult)
    height_cm = user.height if hasattr(user, 'height') else 175.0
    age = 25 # Default if not tracked
    is_male = True # Default assumption for BMR if gender isn't tracked
    weight_kg = user.weight if hasattr(user, 'weight') else 75.0
    
    nutrition = calculate_nutrition_needs(weight_kg, height_cm, age, is_male, user.goal)
    
    # 3. Adjust daily required food calories by ADDING the burned calories (eat back what you burn)
    nutrition["calories"] += burned_today
    
    # 4. Generate dynamic natural language insight
    active_days = len(todays_workouts)
    if active_days > 0:
        if "loss" in user.goal.lower():
            insight = f"You burned {burned_today} kcal today! Keep protein high ({nutrition['protein']}g) to preserve muscle while dropping body fat."
        elif "gain" in user.goal.lower() or "bulk" in user.goal.lower():
            insight = f"Great work burning {burned_today} kcal today. Ensure you consume {nutrition['calories']} kcal and {nutrition['carbs']}g carbs to stay in a surplus!"
        else:
            insight = f"You burned {burned_today} kcal today. Hit {nutrition['protein']}g of protein and maintain hydration for optimal recovery."
    else:
        insight = "Your vault is currently empty for today. Upload your first workout proof to receive personalized, AI-driven biometric insights."
        
    return {
        "insight": insight,
        "macros": nutrition,
        "burned_today": burned_today
    }

from pydantic import BaseModel
class ChatRequest(BaseModel):
    message: str

@router.post("/chat-brain")
async def chat_with_brain(request: ChatRequest, token: Optional[str] = None):
    user = None
    if token:
        try:
            user = await get_current_user(token)
        except:
            pass

    msg = request.message.lower()
    
    from app.utils.ai_brain import calculate_calories_burned, fetch_world_nutrition
    user_weight = user.weight if user and hasattr(user, 'weight') else 75.0
    
    # Intent Detection
    import re
    weight_match = re.search(r'(\d+)\s*(kg|lbs|kilos|pounds)', msg)
    height_match = re.search(r'(\d+)\s*(cm|inches|in)', msg)
    goal_match = re.search(r'(lose|reach|gain|bulk|cut|weight|shred|maintenance)\s*(\d+)?', msg)
    
    # 1. Macro / TDEE Calculation Intent (Prioritized)
    if (weight_match and goal_match) or ("macro" in msg) or ("how much" in msg and "eat" in msg):
        from app.utils.ai_brain import calculate_nutrition_needs
        if weight_match and goal_match:
            w = float(weight_match.group(1))
            h = float(height_match.group(1)) if height_match else 170.0
            goal_type = "loss" if "lose" in msg or "cut" in msg or "shred" in msg else ("gain" if "gain" in msg or "bulk" in msg else "maintenance")
            
            needs = calculate_nutrition_needs(w, h, 25, True, goal_type)
            reply = f"NEURAL ASSESSMENT: Based on your biometrics ({w}kg, {h}cm) and goal to {goal_type} weight, your target is {needs['calories']} kcal/day. You must eat exactly {needs['protein']}g Protein, {needs['carbs']}g Carbs, and {needs['fats']}g Fats daily to achieve this."
        else:
            reply = "Are you asking for your daily macros? Give me your weight, height, and goal (e.g., 'I am 80kg 180cm and want to lose weight, what should I eat?')."
            
    # 2. Specific Food Lookup Intent
    elif any(word in msg for word in ["calories in", "protein in", "carbs in", "nutrition for", "what is in", "calories of", "protein of"]):
        food_query = msg
        for word in ["how much protein in", "calories in", "nutrition for", "what is in", "how many", "calories of", "protein of"]:
            food_query = food_query.replace(word, "")
        food_query = food_query.strip(" ?!")
        
        data = fetch_world_nutrition(food_query)
        if data["calories"] > 0:
            reply = f"WORLD LIBRARY SCANNED: 100g of {data['food']} contains {data['calories']} kcal, {data['protein']}g Protein, {data['carbs']}g Carbs, and {data['fats']}g Fat."
        else:
            reply = "I couldn't find that exact food in the global database. Try being more specific (e.g., 'raw chicken breast')."
            
    # 3. Fitness / General Intent
    else:
        if goal_match and not ("eat" in msg or "food" in msg):
            if "lose" in msg or "cut" in msg:
                reply = f"NEURAL ASSESSMENT: To lose weight safely, maintain a 300-500 kcal deficit daily. Prioritize high-volume low-calorie foods. Track your burned calories in the HUD."
            elif "gain" in msg or "bulk" in msg:
                reply = f"NEURAL ASSESSMENT: To gain muscle, focus on a 300-500 kcal surplus. Load up on Oats, Avocado, and Elite Whey. Heavy compound lifts are mandatory."
            else:
                exercise, calories, _ = calculate_calories_burned(msg, user_weight)
                if exercise != "General Training" or "general" in msg:
                    reply = f"AI BIOMETRIC SCAN: Performing {exercise} for the duration you mentioned would burn approximately {calories} kcal for your specific body weight ({user_weight}kg)."
                else:
                    reply = "I am the East Blue Neural Assistant. You can ask me about the exact calories in any food worldwide, or how many calories a specific workout burns!"
        else:
            exercise, calories, _ = calculate_calories_burned(msg, user_weight)
            if exercise != "General Training" or "general" in msg:
                reply = f"AI BIOMETRIC SCAN: Performing {exercise} for the duration you mentioned would burn approximately {calories} kcal for your specific body weight ({user_weight}kg)."
            else:
                # Elite Knowledge Base Fallback
                responses = {
                    "protein": "Elite standard: 1.8g per kg of bodyweight. Check the Store for our Hydrolyzed Whey.",
                    "hiit": "Recovery is key. 48 hours between HIIT pulses is mandatory for neural recovery.",
                    "membership": "Visit our Membership hub. Elite Annual is our most optimized tier.",
                    "eat": "Are you asking for your daily macros? Give me your weight, height, and goal (e.g., 'I am 80kg 180cm and want to lose weight, what should I eat?').",
                    "food": "I can scan any food globally. Ask 'how many calories in salmon' or 'protein in eggs'."
                }
                reply = "I am the East Blue Neural Assistant. Ask me about the exact calories in any food worldwide, or how many calories a specific workout burns based on your body weight!"
                for key, val in responses.items():
                    if key in msg:
                        reply = val
                        break
            
    return {"reply": reply}

@router.post("/update")
async def update_profile(
    token: str = Form(...),
    fullName: Optional[str] = Form(None),
    firstName: Optional[str] = Form(None),
    lastName: Optional[str] = Form(None),
    nickname: Optional[str] = Form(None),
    bio: Optional[str] = Form(None),
    goal: Optional[str] = Form(None),
    phoneNumber: Optional[str] = Form(None),
    weight: Optional[float] = Form(None),
    weightGoal: Optional[float] = Form(None),
    height: Optional[float] = Form(None),
    profilePictureFile: Optional[UploadFile] = File(None)
):
    user = await get_current_user(token)
    
    # Handle Full Name splitting if provided
    if fullName:
        parts = fullName.strip().split(" ", 1)
        user.firstName = parts[0]
        user.lastName = parts[1] if len(parts) > 1 else ""
    
    if firstName: user.firstName = firstName
    if lastName: user.lastName = lastName
    if nickname: user.nickname = nickname
    if bio: user.bio = bio
    if goal: user.goal = goal
    if phoneNumber: user.phoneNumber = phoneNumber
    if weight is not None: user.weight = weight
    if weightGoal is not None: user.weightGoal = weightGoal
    if height is not None: user.height = height
    
    if profilePictureFile and profilePictureFile.filename:
        validate_media_file(profilePictureFile, max_size_mb=10)
        try:
            # Upload to Cloudinary
            upload_result = cloudinary.uploader.upload(
                profilePictureFile.file,
                folder="elite_gym/profiles",
                public_id=f"user_{str(user.id)}",
                overwrite=True,
                resource_type="image"
            )
            # Set the secure Cloudinary URL
            user.profilePicture = upload_result.get("secure_url")
        except Exception as e:
            print(f"[CLOUDINARY ERROR] {e}")
            # Fallback to DiceBear if upload fails
            user.profilePicture = f"https://api.dicebear.com/7.x/avataaars/svg?seed={user.email}_{int(datetime.utcnow().timestamp())}"
    
    # Update Social Profile dynamically for consistency across community hub
    try:
        from app.models.community import SocialProfile
        sp = await SocialProfile.find_one({"userEmail": user.email})
        if sp:
            if nickname: sp.handle = nickname
            if bio: sp.bio = bio
            if goal: sp.fitnessGoals = goal
            await sp.save()
        else:
            sp = SocialProfile(
                userEmail=user.email,
                handle=nickname if nickname else user.email.split('@')[0],
                bio=bio if bio else "No bio set.",
                fitnessGoals=goal if goal else "Maintenance"
            )
            await sp.insert()
    except Exception as e:
        print(f"[ERROR] Social Profile synchronization failed: {e}")

    await user.save()
    return {"message": "Neural profile synchronized.", "user": user}

@router.post("/change-password")
async def change_password(request: ChangePasswordRequest, token: str):
    user = await get_current_user(token)
    
    # Verify old password
    if not pwd_context.verify(request.oldPassword, user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password incorrect")
    
    # Update password
    user.hashed_password = pwd_context.hash(request.newPassword)
    await user.save()
    
    # Log Activity
    await Activity(
        userId=str(user.id), 
        userEmail=user.email, 
        action="Password Changed", 
        details="Member updated their elite credentials."
    ).insert()
    
    return {"message": "Credentials updated successfully."}


@router.get("/notifications")
async def get_notifications(token: str):
    user = await get_current_user(token)
    # Fetch notifications that are either global OR targeted specifically to this user's email
    return await Notification.find(
        {"$or": [
            {"is_global": True},
            {"userEmail": user.email}
        ]}
    ).sort("-created_at").to_list()

@router.get("/activities")
async def get_activities(token: str):
    user = await get_current_user(token)
    # Return both Activities and Bookings mapped to a common format
    activities = await Activity.find({"userEmail": user.email}).sort("-timestamp").to_list()
    bookings = await Booking.find({"userEmail": user.email}).sort("-date").to_list()
    
    combined = []
    for a in activities:
        combined.append({
            "id": str(a.id),
            "date": a.timestamp.strftime("%b %d, %H:%M"),
            "activity": a.action,
            "location": a.details,
            "status": "Logged",
            "type": "activity"
        })
    from app.utils.booking_utils import is_booking_expired
    
    for b in bookings:
        if is_booking_expired(b):
            await b.delete()
            continue
            
        combined.append({
            "id": str(b.id),
            "date": b.time or b.date.strftime("%b %d, %H:%M"),
            "activity": b.className,
            "location": b.trainerName,
            "status": "Booked",
            "type": "booking"
        })
    
    return sorted(combined, key=lambda x: x['date'], reverse=True)

@router.post("/activity")
async def log_activity(data: dict):
    activity = Activity(
        userId=data.get("userId", "GUEST"),
        userEmail=data.get("userEmail"),
        action=data.get("action"),
        details=data.get("details", "Neural sync successful")
    )
    await activity.insert()
    return {"status": "success"}

@router.post("/book")
async def book_class(class_id: str, token: str):
    user = await get_current_user(token)
    target = await ClassSchedule.get(PydanticObjectId(class_id))
    if not target or target.status != "Active":
        raise HTTPException(status_code=400, detail="Session unavailable.")
    if target.enrolled >= target.capacity:
        raise HTTPException(status_code=400, detail="Capacity reached.")
        
    target.enrolled += 1
    await target.save()
    
    new_booking = Booking(
        userId=str(user.id),
        userEmail=user.email,
        userName=f"{user.firstName} {user.lastName}",
        classId=str(target.id),
        className=target.className,
        trainerName=target.trainerName,
        time=f"{target.day} {target.time}"
    )
    await new_booking.insert()
    
    await Activity(
        userId=str(user.id),
        userEmail=user.email,
        action="Class Booked",
        details=f"Booked {target.className}"
    ).insert()
    
    user.points = getattr(user, "points", 0) + 50
    await user.save()
    
    return {"message": "Neural reservation confirmed."}

@router.post("/book/cancel/{id}")
async def cancel_booking(id: str, token: str):
    user = await get_current_user(token)
    booking = await Booking.get(PydanticObjectId(id))
    if not booking or booking.userEmail != user.email:
        raise HTTPException(status_code=404, detail="Booking not found.")
    
    # Restore capacity
    target = await ClassSchedule.get(PydanticObjectId(booking.classId))
    if target:
        target.enrolled = max(0, target.enrolled - 1)
        await target.save()
        
    await booking.delete()
    return {"message": "Reservation purged."}

@router.post("/contact")
async def contact_form(data: dict):
    await Activity(
        userId="GUEST",
        userEmail=data.get("email", "unknown@guest.com"),
        action="Contact Inquiry",
        details=f"Subject: {data.get('subject')}"
    ).insert()
    return {"status": "success", "message": "Neural transmission received."}

@router.get("/classes")
async def get_public_classes():
    return await ClassSchedule.find({"status": "Active"}).to_list()

@router.get("/videos")
async def get_public_videos():
    return await Video.find_all().sort("-created_at").to_list()

@router.post("/challenge-notify")
async def challenge_notify(data: dict):
    await Activity(
        userId="GUEST",
        userEmail=data.get("email"),
        action="Challenge Interest",
        details="Member requested challenge notification."
    ).insert()
    return {"status": "success"}

@router.post("/newsletter")
async def newsletter_signup(data: dict):
    await Activity(
        userId="GUEST",
        userEmail=data.get("email"),
        action="Newsletter Signup",
        details="Member joined the community mailing list."
    ).insert()
    return {"status": "success", "message": "Welcome to the Elite community!"}

@router.post("/invest")
async def invest_request(data: dict):
    await Activity(
        userId="PRO",
        userEmail=data.get("email"),
        action="Investment Inquiry",
        details="Professional pitch deck request."
    ).insert()
    return {"status": "success"}

@router.post("/feedback")
async def submit_feedback(data: dict):
    token = data.get("token")
    category = data.get("category")
    message = data.get("message")
    
    user = await get_current_user(token)
    
    feedback = UserFeedback(
        userEmail=user.email,
        userName=f"{user.firstName} {user.lastName}",
        category=category,
        message=message
    )
    await feedback.insert()
    
    # Log Activity
    await Activity(
        userId=str(user.id),
        userEmail=user.email,
        action="Feedback Submitted",
        details=f"Category: {category} | Sentiment: {data.get('sentiment', 'neutral')}"
    ).insert()
    
    return {"message": "Thank you! Your elite feedback has been synchronized with the command center."}
    
@router.post("/admission/submit")
async def submit_admission(data: dict, token: str):
    user = await get_current_user(token)
    
    user.admissionStatus = "submitted"
    user.admissionFeePaid = True
    
    # In a real app, you'd verify the payment here
    
    await user.save()
    
    # Log Activity
    await Activity(
        userId=str(user.id),
        userEmail=user.email,
        action="Admission Submitted",
        details=f"Legal Name: {data.get('legalName')} | Method: {data.get('paymentMethod')}"
    ).insert()
    
    return {"message": "Admission documentation and fee received. Pending verification."}
    
@router.get("/leaderboard")
async def get_leaderboard():
    # Fetch top 10 users by points
    users = await User.find_all().sort("-points").limit(10).to_list()
    # Sanitize: only return nickname/name and points
    return [{
        "name": u.nickname or f"{u.firstName} {u.lastName[:1]}.",
        "points": u.points,
        "avatar": u.profilePicture
    } for u in users]

@router.get("/pulse")
async def get_pulse():
    # Fetch last 15 activities
    activities = await Activity.find().sort("-timestamp").limit(15).to_list()
    data = []
    for a in activities:
        name = "Elite Member"
        if a.userEmail and "@" in a.userEmail:
            name = a.userEmail.split("@")[0]
            if len(name) > 3: name = name[:3] + "..."
        data.append({
            "user": name,
            "action": a.action,
            "details": a.details,
            "time": a.timestamp
        })
    return data

# Duplicated notifications endpoint removed to prevent route masking.
# All notifications are handled securely by the primary /notifications endpoint.

@router.post("/notifications/read")
async def mark_notifications_read(token: str):
    user = await get_current_user(token)
    email_lower = user.email.strip().lower()
    await Notification.find({
        "$or": [
            {"userEmail": email_lower},
            {"userEmail": {"$regex": f"^{email_lower}$", "$options": "i"}}
        ],
        "isRead": False
    }).update({"$set": {"isRead": True}})
    return {"status": "success"}

@router.get("/live-feed")
async def get_live_feed():
    # 1. Leaderboard
    top_users = await User.find_all().sort("-points").limit(3).to_list()
    leaderboard = []
    for user in top_users:
        name = getattr(user, 'firstName', None)
        if not name:
            name = user.email.split('@')[0]
        else:
            last = getattr(user, 'lastName', '')
            if last:
                name = f"{name} {last[0]}."
        leaderboard.append({
            "name": name,
            "points": user.points
        })

    # 2. Activity
    activities = []
    
    # Workouts
    recent_workouts = await Workout.find_all().sort("-date").limit(10).to_list()
    for w in recent_workouts:
        user = await User.get(PydanticObjectId(w.user_id)) if w.user_id else None
        name = "Unknown"
        if user:
            name = getattr(user, 'firstName', user.email.split('@')[0])
            last = getattr(user, 'lastName', '')
            if last:
                name = f"{name} {last[0]}."
                
        def get_ts(dt):
            return dt.timestamp() if dt.tzinfo else dt.replace(tzinfo=timezone.utc).timestamp()
            
        activities.append({
            "type": "workout",
            "userName": name,
            "text": f"verified {w.calories}kcal video proof.",
            "timestamp": w.date.isoformat(),
            "ts": get_ts(w.date)
        })

    # Posts
    recent_posts = await CommunityPost.find_all().sort("-timestamp").limit(10).to_list()
    for p in recent_posts:
        activities.append({
            "type": "post",
            "userName": p.userName,
            "text": "shared a new community post.",
            "timestamp": p.timestamp.isoformat(),
            "ts": get_ts(p.timestamp)
        })
        
    # Sort activities combined by timestamp
    activities.sort(key=lambda x: x["ts"], reverse=True)
    top_activities = activities[:10]
    
    for a in top_activities:
        del a["ts"]
        
    return {
        "leaderboard": leaderboard,
        "activities": top_activities
    }

from pydantic import BaseModel
from app.models.user import AttendanceLog

class AttendanceRequest(BaseModel):
    timeStr: str

@router.post("/attendance")
async def log_attendance(req: AttendanceRequest, token: str):
    user = await get_current_user(token)
    
    log = AttendanceLog(
        user_id=str(user.id),
        user_name=f"{user.firstName} {user.lastName}",
        arrival_time=req.timeStr
    )
    await log.insert()
    
    activity = Activity(
        userId=str(user.id),
        userEmail=user.email,
        action="Check-In",
        details=f"checked into the Elite Studio at {req.timeStr}"
    )
    await activity.insert()
    
    # Award points for checking in
    user.points += 50
    await user.save()
    
    return {"status": "success", "message": "Attendance logged successfully."}
