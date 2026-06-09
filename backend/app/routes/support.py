from fastapi import APIRouter, HTTPException, Depends
from app.models.admin import SupportMessage
from app.models.user import User
from app.routes.auth import get_current_user
from datetime import datetime
import jwt
import os

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"

async def get_current_admin(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email: raise HTTPException(status_code=401, detail="Invalid token")
        user = await User.find_one(User.email == email.strip().lower())
        if not user or user.role != "superadmin":
            raise HTTPException(status_code=403, detail="Not authorized. Superadmin only.")
        return user
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_trainer(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email: raise HTTPException(status_code=401, detail="Invalid token")
        user = await User.find_one(User.email == email.strip().lower())
        if not user or user.role not in ["superadmin", "trainer"]:
            raise HTTPException(status_code=403, detail="Not authorized. Trainer only.")
        return user
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_admin_or_trainer(token: str):
    return await get_current_trainer(token)

router = APIRouter(prefix="/support", tags=["Support Chat"])

@router.post("/send")
async def send_support_message(data: dict, token: str):
    user = await get_current_user(token)
    recipient_type = data.get("recipientType")
    message = data.get("message")
    
    if not recipient_type or recipient_type not in ["Owner", "Trainer"]:
        raise HTTPException(status_code=400, detail="Invalid recipient type")
        
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
        
    new_message = SupportMessage(
        senderEmail=user.email,
        senderName=f"{user.firstName} {user.lastName}",
        recipientType=recipient_type,
        message=message
    )
    await new_message.insert()
    return {"message": "Support message sent successfully", "id": str(new_message.id)}

@router.get("/history")
async def get_support_history(token: str):
    user = await get_current_user(token)
    messages = await SupportMessage.find(SupportMessage.senderEmail == user.email).sort("-timestamp").to_list()
    return messages

@router.get("/owner")
async def get_owner_messages(token: str):
    await get_current_admin(token)
    messages = await SupportMessage.find(SupportMessage.recipientType == "Owner").sort("-timestamp").to_list()
    return messages

@router.get("/trainer")
async def get_trainer_messages(token: str):
    await get_current_trainer(token)
    messages = await SupportMessage.find(SupportMessage.recipientType == "Trainer").sort("-timestamp").to_list()
    return messages

@router.post("/{msg_id}/reply")
async def reply_support_message(msg_id: str, data: dict, token: str):
    user = await get_current_admin_or_trainer(token)
    from beanie import PydanticObjectId
    
    msg = await SupportMessage.get(PydanticObjectId(msg_id))
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
        
    reply_text = data.get("reply")
    if not reply_text:
        raise HTTPException(status_code=400, detail="Reply cannot be empty")
        
    msg.reply = reply_text
    msg.status = "resolved"
    await msg.save()
    
    # Also resolve any other open messages from this user so the unread dot disappears
    open_msgs = await SupportMessage.find(
        SupportMessage.senderEmail == msg.senderEmail,
        SupportMessage.recipientType == msg.recipientType,
        SupportMessage.status == "open"
    ).to_list()
    
    for m in open_msgs:
        if m.id != msg.id:
            m.status = "resolved"
            await m.save()
    
    # Notify user via email
    from app.utils.notifications import NotificationService
    try:
        await NotificationService.send_bulk_email(
            [msg.senderEmail],
            "Support Reply from East Blue Gym",
            f"Hi {msg.senderName},<br><br>You received a reply from the {msg.recipientType} regarding your recent inquiry:<br><br><i>\"{msg.message}\"</i><br><br><b>Reply:</b><br>{msg.reply}"
        )
    except Exception as e:
        print(f"[ERROR] Failed to send support reply email: {e}")
        
    return {"message": "Reply sent successfully"}
