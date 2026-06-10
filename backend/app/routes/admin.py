from fastapi import APIRouter, HTTPException, Depends, status, Form, File, UploadFile
from app.models.user import User
from app.models.admin import Booking, Activity, Order, ClassSchedule, Notification, Video, UserFeedback, MentorshipRequest
from app.schemas.user import UserResponse
from typing import List, Optional
import jwt
import os
from datetime import datetime

router = APIRouter(prefix="/admin", tags=["Admin"])

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"

async def get_current_admin(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = await User.find_one(User.email == email)
        if not user or user.role not in ["admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Not authorized")
        return user
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_admin_or_trainer(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = await User.find_one(User.email == email)
        if not user or user.role not in ["admin", "super_admin", "trainer"]:
            raise HTTPException(status_code=403, detail="Not authorized")
        return user
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_super_admin(token: str):
    user = await get_current_admin_or_trainer(token)
    if user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Only Super Admin can perform this action")
    return user

@router.get("/stats")
async def get_stats(token: str):
    user = await get_current_admin(token)
    
    total_users = await User.count()
    total_bookings = await Booking.count()
    total_orders = await Order.count()
    recent_activities = await Activity.find().sort("-timestamp").limit(30).to_list()
    
    # Revenue from bookings (sum of prices)
    bookings = await Booking.find_all().to_list()
    booking_rev = sum(b.price for b in bookings if hasattr(b, 'price') and b.price)
    
    orders = await Order.find_all().to_list()
    order_rev = sum(o.total for o in orders if hasattr(o, 'total'))
    
    return {
        "totalUsers": total_users,
        "totalBookings": total_bookings,
        "totalOrders": total_orders,
        "estimatedRevenue": booking_rev + order_rev,
        "recentActivities": recent_activities
    }

@router.get("/users")
async def list_users(token: str):
    try:
        await get_current_admin_or_trainer(token)
        users = await User.find_all().to_list()
        # Manual conversion with strict error isolation for each record
        data = []
        for u in users:
            try:
                data.append({
                    "id": str(u.id),
                    "email": u.email,
                    "firstName": u.firstName,
                    "lastName": u.lastName,
                    "phoneNumber": getattr(u, 'phoneNumber', None),
                    "nickname": getattr(u, 'nickname', 'Elite Member'),
                    "points": getattr(u, 'points', 0),
                    "membershipType": getattr(u, 'membershipType', 'FREE GUEST'),
                    "admissionStatus": getattr(u, 'admissionStatus', 'pending'),
                    "membershipClass": getattr(u, 'membershipClass', 'D'),
                    "role": getattr(u, 'role', 'member'),
                    "monthlyFeeStatus": getattr(u, 'monthlyFeeStatus', 'Unpaid'),
                    "lastFeePaidAmount": getattr(u, 'lastFeePaidAmount', 0.0),
                    "lastFeePaidDate": getattr(u, 'lastFeePaidDate', None)
                })
            except Exception as e:
                print(f"CRITICAL: Failed to serialize user {getattr(u, 'email', 'unknown')}: {str(e)}")
                continue
        return data
    except Exception as e:
        print(f"DATABASE SYNC ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database Sync Error: {str(e)}")

@router.delete("/users/{email}")
async def delete_user(email: str, token: str):
    await get_current_admin_or_trainer(token)
    email_clean = email.strip().lower()
    target = await User.find_one(User.email == email_clean)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target.role == "super_admin":
        raise HTTPException(status_code=403, detail="Cannot delete Super Admin")
    # Cascade delete all user data
    await Booking.find(Booking.userEmail == email).delete()
    await Activity.find(Activity.userEmail == email).delete()
    await Order.find(Order.userEmail == email).delete()
    
    await target.delete()
    return {"message": f"User {email} and all associated records purged."}

@router.post("/users/{email}/fee")
async def update_user_fee(email: str, data: dict, token: str):
    await get_current_admin_or_trainer(token)
    email_clean = email.strip().lower()
    target = await User.find_one(User.email == email_clean)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    
    target.monthlyFeeStatus = data.get("status", getattr(target, 'monthlyFeeStatus', 'Unpaid'))
    target.lastFeePaidAmount = float(data.get("amount", getattr(target, 'lastFeePaidAmount', 0.0)))
    if target.monthlyFeeStatus == "Paid":
        target.lastFeePaidDate = datetime.utcnow()
        
    await target.save()
    return {"message": f"User {email} fee status updated."}

@router.get("/users")
async def list_users(token: str):
    await get_current_admin(token)
    # Fetch all users, excluding passwords
    all_users = await User.find().sort("-created_at").to_list()
    # Exclude hashed_password explicitly just in case Pydantic exposes it
    users_data = []
    for u in all_users:
        u_dict = u.dict(exclude={"hashed_password"})
        # Convert ObjectId to string
        u_dict["_id"] = str(u.id) if hasattr(u, 'id') else None
        users_data.append(u_dict)
    return users_data

@router.post("/promote")
async def promote_user(email: str, token: str):
    await get_current_admin(token)
    email_clean = email.strip().lower()
    target = await User.find_one(User.email == email_clean)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    
    target.role = "admin"
    await target.save()
    return {"message": f"User {email} promoted to Admin."}

@router.get("/bookings")
async def list_bookings(token: str):
    await get_current_admin_or_trainer(token)
    all_bookings = await Booking.find().sort("-createdAt").to_list()
    return all_bookings

@router.delete("/bookings/{id}")
async def delete_booking(id: str, token: str):
    await get_current_admin_or_trainer(token)
    from beanie import PydanticObjectId
    target = await Booking.get(PydanticObjectId(id))
    if not target:
        raise HTTPException(status_code=404, detail="Booking not found")
    await target.delete()
    return {"message": "Booking permanently deleted"}
@router.get("/orders")
async def list_orders(token: str):
    await get_current_admin(token)
    return await Order.find().sort("-timestamp").to_list()

@router.get("/classes")
async def list_classes(token: str):
    await get_current_admin_or_trainer(token)
    return await ClassSchedule.find_all().to_list()

@router.post("/classes/add")
async def add_class(data: dict, token: str):
    await get_current_admin_or_trainer(token)
    new_class = ClassSchedule(**data)
    new_class.status = "Active"
    await new_class.insert()
    
    # NEURAL BROADCAST: Notify all users via Service
    from app.utils.notifications import NotificationService
    try:
        await NotificationService.notify_new_class(
            class_name=new_class.className,
            time=f"{new_class.day} at {new_class.time}",
            trainer=new_class.trainerName
        )
    except Exception as e:
        print(f"[ERROR] Notification Service failed: {e}")

    return {"message": "Class added and all members notified via Email/SMS"}

@router.post("/classes/cancel/{id}")
async def cancel_class(id: str, token: str):
    await get_current_admin_or_trainer(token)
    from beanie import PydanticObjectId
    target = await ClassSchedule.get(PydanticObjectId(id))
    if not target:
        raise HTTPException(status_code=404, detail="Class not found")
    await target.delete()
    return {"message": "Class permanently deleted"}

@router.post("/videos/add")
async def add_video(
    token: str,
    title: str = Form(...),
    category: str = Form(...),
    mode: str = Form(...),
    url: Optional[str] = Form(None),
    duration: Optional[str] = Form("10:00"),
    trainer: Optional[str] = Form("Elite Coach"),
    videoFile: Optional[UploadFile] = File(None)
):
    await get_current_admin_or_trainer(token)
    
    final_url = url
    thumbnail = "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?w=500"
    
    if mode == "file" and videoFile:
        try:
            import cloudinary.uploader
            upload_result = cloudinary.uploader.upload(
                videoFile.file,
                resource_type="video",
                folder="elite_gym/videos"
            )
            final_url = upload_result.get("secure_url")
            # Cloudinary generates thumbnails for videos automatically if requested, 
            # but for now we use a default or the first frame if possible.
            # Simple approach: change extension to jpg for thumbnail
            if final_url:
                thumbnail = final_url.rsplit(".", 1)[0] + ".jpg"
        except Exception as e:
            print(f"[CLOUDINARY ERROR] {e}")
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    if not final_url:
        raise HTTPException(status_code=400, detail="No video URL or file provided")

    new_video = Video(
        title=title,
        category=category,
        duration=duration,
        thumbnail=thumbnail,
        url=final_url,
        trainer=trainer
    )
    await new_video.insert()
    
    await Activity(
        userId="ADMIN",
        userEmail="system@eastblue.com",
        action="Video Added",
        details=f"New technique added: {new_video.title}"
    ).insert()

    # NEURAL SYNC: Notify members
    from app.utils.notifications import NotificationService
    try:
        await NotificationService.broadcast_to_all(
            "NEW VIDEO IN VAULT",
            f"Elite Technique: '{new_video.title}' is now live. Level up your game in the Video Vault!"
        )
    except Exception as e:
        print(f"[ERROR] Notification Service failed: {e}")

    
    return {"message": "Video added to library", "video_id": str(new_video.id)}

@router.get("/videos")
async def list_videos(token: str):
    await get_current_admin_or_trainer(token)
    return await Video.find_all().to_list()

@router.delete("/videos/{id}")
async def delete_video(id: str, token: str):
    await get_current_admin_or_trainer(token)
    from beanie import PydanticObjectId
    video = await Video.get(PydanticObjectId(id))
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    await video.delete()
    return {"message": "Video purged from library"}

@router.post("/broadcast")
async def broadcast_message(data: dict, token: str):
    await get_current_admin(token)
    notif = Notification(
        title=data.get("title", "ADMIN ANNOUNCEMENT"),
        message=data.get("message"),
        type=data.get("type", "info")
    )
    await notif.insert()
    
    # Log global activity
    await Activity(
        userId="ADMIN",
        userEmail="system@eastblue.com",
        action="Broadcast Sent",
        details=f"Message: {notif.title}"
    ).insert()
    
    # NEURAL SYNC: Email/SMS
    from app.utils.notifications import NotificationService
    try:
        await NotificationService.broadcast_to_all(notif.title, notif.message)
    except Exception as e:
        print(f"[ERROR] Notification Service failed: {e}")

    return {"message": "Broadcast sent and all members notified via Email/SMS"}

@router.post("/gym-off")
async def mark_gym_off(data: dict, token: str):
    await get_current_admin_or_trainer(token)
    reason = data.get("reason", "Maintenance")
    
    from app.utils.notifications import NotificationService
    try:
        await NotificationService.notify_gym_closure(reason)
    except Exception as e:
        print(f"[ERROR] Notification Service failed: {e}")
        
    return {"message": "Gym marked as OFF and members notified"}

@router.post("/orders/{id}/status")
async def update_order_status(id: str, data: dict, token: str):
    await get_current_admin_or_trainer(token)
    from beanie import PydanticObjectId
    order = await Order.get(PydanticObjectId(id))
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order.status = data.get("status", order.status)
    await order.save()
    
    # Log the fulfillment activity
    await Activity(
        userId="ADMIN",
        userEmail="system@eastblue.com",
        action="Order Status Updated",
        details=f"Order {id} marked as {order.status}"
    ).insert()
    
    return {"message": f"Order status updated to {order.status}"}

@router.get("/feedback")
async def list_feedback(token: str):
    await get_current_admin_or_trainer(token)
    feedbacks = await UserFeedback.find_all().sort("-timestamp").to_list()
    
    result = []
    for f in feedbacks:
        f_dict = f.dict()
        email_clean = f.userEmail.strip()
        user = await User.find_one({"email": {"$regex": f"^{email_clean}$", "$options": "i"}})
        if user and getattr(user, 'profilePicture', None):
            f_dict['profilePicture'] = user.profilePicture
        else:
            f_dict['profilePicture'] = f"https://ui-avatars.com/api/?name={f.userName if f.userName else f.userEmail[0]}&background=f5e642&color=000"
        result.append(f_dict)
        
    return result

@router.post("/feedback/{id}/resolve")
async def resolve_feedback(id: str, token: str):
    await get_current_admin_or_trainer(token)
    from beanie import PydanticObjectId
    feedback = await UserFeedback.get(PydanticObjectId(id))
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    
    feedback.status = "resolved"
    await feedback.save()
    return {"message": "Feedback marked as resolved"}

@router.patch("/feedback/{id}/publish")
async def publish_feedback(id: str, token: str):
    await get_current_admin(token)
    from beanie import PydanticObjectId
    feedback = await UserFeedback.get(PydanticObjectId(id))
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    
    # Toggle publish status
    feedback.is_published = not getattr(feedback, 'is_published', False)
    await feedback.save()
    status_str = "published" if feedback.is_published else "unpublished"
    return {"message": f"Feedback successfully {status_str}", "is_published": feedback.is_published}


@router.get("/users/{email}/progress")
async def get_user_progress(email: str, token: str):
    await get_current_admin_or_trainer(token)
    user = await User.find_one(User.email == email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    bookings = await Booking.find(Booking.userEmail == email).sort("-date").to_list()
    from app.models.user import AttendanceLog
    attendance = await AttendanceLog.find(AttendanceLog.user_id == str(user.id)).sort("-date").to_list()
    
    weight = float(getattr(user, 'weight', 75.0) or 75.0)
    goal = getattr(user, 'goal', 'Maintenance') or 'Maintenance'
    
    protein_target = round(weight * 2.2)
    calorie_target = round(weight * 30)
    if goal == 'Fat Loss':
        calorie_target -= 500
    elif goal in ['Bulking', 'Hypertrophy']:
        calorie_target += 500

    return {
        "workouts": workouts,
        "weightHistory": weight_history,
        "bookings": bookings,
        "attendance": attendance,
        "monthlyFeeStatus": getattr(user, 'monthlyFeeStatus', 'Unpaid'),
        "lastFeePaidAmount": getattr(user, 'lastFeePaidAmount', 0.0),
        "lastFeePaidDate": getattr(user, 'lastFeePaidDate', None),
        "currentWeight": weight,
        "targetWeight": float(getattr(user, 'weightGoal', 80.0) or 80.0),
        "trainingGoal": goal,
        "proteinTarget": protein_target,
        "calorieTarget": calorie_target,
        "activeBurnTarget": round(weight * 10),
        "firstName": getattr(user, 'firstName', 'Elite'),
        "lastName": getattr(user, 'lastName', 'Member'),
        "role": getattr(user, 'role', 'user'),
        "height": float(getattr(user, 'height', 180.0) or 180.0),
        "profilePicture": getattr(user, 'profilePicture', None)
    }

@router.get("/admissions")
async def list_admissions(token: str):
    await get_current_admin(token)
    # Users who have submitted their admission documents
    return await User.find(User.admissionStatus == "submitted").to_list()

@router.post("/admissions/{email}/approve")
async def approve_admission(email: str, token: str):
    await get_current_admin(token)
    user = await User.find_one(User.email == email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.admissionStatus = "approved"
    user.membershipClass = "C" # Set to Admitted Class
    await user.save()
    
    # Notify user
    from app.utils.notifications import NotificationService
    try:
        await NotificationService.send_bulk_email(
            [user.email],
            "ADMISSION APPROVED",
            f"Welcome to the Elite, {user.firstName}! Your admission has been verified. You now have full access to our facilities."
        )
    except: pass
    
    return {"message": "Admission approved"}

@router.post("/admissions/{email}/reject")
async def reject_admission(email: str, token: str):
    await get_current_admin_or_trainer(token)
    user = await User.find_one(User.email == email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.admissionStatus = "pending" # Reset to pending
    user.admissionFeePaid = False # Optional: require re-payment if it was a scam
    await user.save()
    
    return {"message": "Admission rejected"}
from app.models.community import CommunityPost, SocialProfile, PrivateMessage

@router.delete("/community/posts/{id}")
async def delete_community_post(id: str, token: str):
    await get_current_admin_or_trainer(token)
    from beanie import PydanticObjectId
    post = await CommunityPost.get(PydanticObjectId(id))
    if not post: raise HTTPException(status_code=404)
    await post.delete()
    return {"message": "Broadcast purged from the hub."}

@router.delete("/community/posts/{id}/comments/{comment_id}")
async def delete_community_comment(id: str, comment_id: str, token: str):
    await get_current_admin_or_trainer(token)
    from beanie import PydanticObjectId
    post = await CommunityPost.get(PydanticObjectId(id))
    if not post: raise HTTPException(status_code=404)
    post.comments = [c for c in post.comments if c.get("id") != comment_id]
    await post.save()
    return {"message": "Comment removed from broadcast."}

@router.post("/community/users/{email}/ban")
async def ban_community_user(email: str, token: str):
    await get_current_admin_or_trainer(token)
    user = await User.find_one(User.email == email)
    if not user: raise HTTPException(status_code=404)
    user.isBanned = not user.isBanned
    await user.save()
    return {"message": f"Member status updated to {'Banned' if user.isBanned else 'Active'}."}

@router.post("/community/users/{email}/verify")
async def verify_community_trainer(email: str, token: str):
    await get_current_admin_or_trainer(token)
    profile = await SocialProfile.find_one(SocialProfile.userEmail == email)
    if not profile: raise HTTPException(status_code=404)
    profile.isVerified = not profile.isVerified
    await profile.save()
    return {"message": f"Trainer verification {'granted' if profile.isVerified else 'revoked'}."}

@router.post("/community/announcements/create")
async def create_announcement(data: dict, token: str):
    admin = await get_current_admin_or_trainer(token)
    post = CommunityPost(
        userEmail=admin.email,
        userName="GYM MANAGEMENT",
        content=data.get("content"),
        isAnnouncement=True,
        tags=["announcement"]
    )
    await post.insert()
    return {"message": "Gym-wide announcement broadcasted."}

@router.get("/mentorships")
async def get_mentorships(token: str):
    return await MentorshipRequest.find_all().sort("-timestamp").to_list()

@router.post("/mentorships/{id}/status")
async def update_mentorship_status(id: str, data: dict, token: str):
    from beanie import PydanticObjectId
    req = await MentorshipRequest.get(PydanticObjectId(id))
    if req:
        req.status = data.get("status", req.status)
        await req.save()
        return {"status": "success"}
    return {"status": "error", "detail": "Not found"}

from app.models.user import AttendanceLog
from datetime import datetime, timezone

@router.get("/attendance")
async def get_attendance(token: str):
    await get_current_admin_or_trainer(token)
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    logs = await AttendanceLog.find(AttendanceLog.date >= today_start).sort("-date").to_list()
    return logs
