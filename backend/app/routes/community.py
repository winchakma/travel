from fastapi import APIRouter, HTTPException, Depends, Form, UploadFile, File, WebSocket, WebSocketDisconnect
from app.models.user import User
from app.models.community import CommunityPost, CommunityChat, PrivateMessage, SocialLink, Story, SocialProfile, CommunityForumTopic, CommunityEvent, MemberSpotlight
from app.models.admin import Notification
from app.routes.auth import get_current_user
from app.routes.profile import validate_media_file
from app.brain import CommunityBrain
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import os
import cloudinary.uploader
import uuid
import json
import time
import hashlib

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, email: str):
        email_key = email.strip().lower()
        await websocket.accept()
        if email_key not in self.active_connections:
            self.active_connections[email_key] = []
        self.active_connections[email_key].append(websocket)
        # Broadcast online status
        await self.broadcast({"type": "status", "email": email_key, "status": "online"})

    def disconnect(self, email: str, websocket: WebSocket):
        email_key = email.strip().lower()
        if email_key in self.active_connections:
            if websocket in self.active_connections[email_key]:
                self.active_connections[email_key].remove(websocket)
            if not self.active_connections[email_key]:
                del self.active_connections[email_key]

    async def send_personal_message(self, message: dict, email: str):
        email_key = email.strip().lower() if email else ""
        if email_key in self.active_connections:
            for ws in list(self.active_connections[email_key]):
                try:
                    await ws.send_json(message)
                except:
                    if ws in self.active_connections[email_key]:
                        self.active_connections[email_key].remove(ws)
            if not self.active_connections[email_key]:
                del self.active_connections[email_key]

    async def broadcast(self, message: dict):
        for email_key, ws_list in list(self.active_connections.items()):
            for ws in list(ws_list):
                try:
                    await ws.send_json(message)
                except:
                    if ws in ws_list:
                        ws_list.remove(ws)
            if not ws_list:
                del self.active_connections[email_key]

    def is_online(self, email: str) -> bool:
        email_key = email.strip().lower()
        return email_key in self.active_connections and len(self.active_connections[email_key]) > 0

manager = ConnectionManager()

router = APIRouter(prefix="/community", tags=["Community"])

async def enrich_posts(posts: List[CommunityPost]) -> List[dict]:
    if not posts: return []
    
    # 1. Gather all unique user emails
    emails = {p.userEmail.strip().lower() for p in posts if p.userEmail}
    
    # 2. Fetch users and their social profiles in bulk
    from app.models.user import User
    from app.models.community import SocialProfile
    
    users = await User.find({"email": {"$in": list(emails)}}).to_list()
    user_map = {u.email.strip().lower(): u for u in users}
    
    profiles = await SocialProfile.find({"userEmail": {"$in": list(emails)}}).to_list()
    profile_map = {p.userEmail.strip().lower(): p for p in profiles}
    
    # 3. Enrich posts with user avatar, actual name, handle and formatted comments avatars
    enriched = []
    for p in posts:
        email_key = p.userEmail.strip().lower()
        u = user_map.get(email_key)
        sp = profile_map.get(email_key)
        
        # Determine latest avatar
        avatar = u.profilePicture if (u and u.profilePicture) else "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
        
        # Determine actual display handle or name
        handle = sp.handle if (sp and sp.handle) else (u.username if u else p.userName)
        
        post_dict = p.model_dump()
        post_dict["id"] = str(p.id)
        post_dict["_id"] = str(p.id)
        post_dict["userAvatar"] = avatar
        # Keep handle / username in sync
        post_dict["userName"] = handle
        
        # Also enrich comments with their latest avatars!
        comments = []
        for c in (p.comments or []):
            c_email = c.get("userEmail", "").strip().lower()
            cu = user_map.get(c_email) or await User.find_one({"email": c_email})
            csp = profile_map.get(c_email) or await SocialProfile.find_one({"userEmail": c_email})
            
            c_avatar = cu.profilePicture if (cu and cu.profilePicture) else "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
            c_name = csp.handle if (csp and csp.handle) else (cu.username if cu else c.get("userName"))
            
            comments.append({
                **c,
                "userAvatar": c_avatar,
                "userName": c_name
            })
        post_dict["comments"] = comments
        enriched.append(post_dict)
        
    return enriched

@router.get("/posts")
async def get_posts(
    token: Optional[str] = None,
    email: Optional[str] = None,
    show_archived: bool = False,
    tagged_email: Optional[str] = None
):
    query = {}
    if email:
        query["userEmail"] = email.strip().lower()
    if tagged_email:
        query["taggedUsers"] = tagged_email.strip().lower()
    if not show_archived:
        query["isArchived"] = {"$ne": True}
        
    if email or tagged_email:
        posts = await CommunityPost.find(query).sort("-timestamp").to_list()
    elif token:
        try:
            user = await get_current_user(token)
            ranked = await CommunityBrain.rank_feed(user.email)
            posts = [p for p in ranked if not getattr(p, "isArchived", False)]
        except:
            posts = await CommunityPost.find(query).sort("-timestamp").to_list()
    else:
        posts = await CommunityPost.find(query).sort("-timestamp").to_list()
        
    return await enrich_posts(posts)

@router.get("/analytics")
async def get_social_analytics(token: str):
    user = await get_current_user(token)
    return await CommunityBrain.get_analytics(user.email)

@router.post("/posts/create")
async def add_post(
    token: str = Form(...),
    content: str = Form(""),
    mediaFile: Optional[UploadFile] = File(None)
):
    user = await get_current_user(token)
    
    # Neural Moderation
    if not CommunityBrain.moderate_content(content):
        raise HTTPException(status_code=400, detail="Content does not meet elite community standards.")

    media_url = None
    media_type = None

    if mediaFile and mediaFile.filename:
        validate_media_file(mediaFile, max_size_mb=10)
        try:
            filename_lower = mediaFile.filename.lower()
            is_video = False
            is_audio = False
            if (mediaFile.content_type and mediaFile.content_type.startswith("audio")) or \
               any(filename_lower.endswith(ext) for ext in [".mp3", ".wav", ".ogg", ".m4a"]):
                is_audio = True
            elif (mediaFile.content_type and mediaFile.content_type.startswith("video")) or \
               any(filename_lower.endswith(ext) for ext in [".mp4", ".mov", ".avi", ".mkv", ".webm", ".3gp", ".m4v"]):
                is_video = True

            resource_type = "video" if (is_video or is_audio) else "image"
            
            upload_result = cloudinary.uploader.upload(
                mediaFile.file,
                folder="elite_gym/community",
                resource_type=resource_type
            )
            media_url = upload_result.get("secure_url")
            media_type = "audio" if is_audio else ("video" if is_video else "image")
        except Exception as e:
            print(f"[POST MEDIA ERROR] {e}")

    import re
    tagged_emails = []
    handles = re.findall(r"@([a-zA-Z0-9_]+)", content)
    for h in handles:
        sp = await SocialProfile.find_one({"handle": re.compile(f"^{h}$", re.IGNORECASE)})
        if sp:
            tagged_emails.append(sp.userEmail.strip().lower())
        else:
            u = await User.find_one({"nickname": re.compile(f"^{h}$", re.IGNORECASE)})
            if u:
                tagged_emails.append(u.email.strip().lower())
    tagged_emails = list(set(tagged_emails))

    new_post = CommunityPost(
        userEmail=user.email,
        userName=f"{user.firstName} {user.lastName}",
        content=content,
        mediaUrl=media_url,
        mediaType=media_type,
        likes=[],
        comments=[],
        taggedUsers=tagged_emails
    )
    await new_post.insert()

    # Update Neural Profile Stats
    profile = await SocialProfile.find_one({"userEmail": user.email})
    if profile:
        profile.postsCount += 1
        await profile.save()

    user.points = getattr(user, "points", 0) + 50
    await user.save()

    return {"message": "Post shared with the community!", "post": new_post}

@router.delete("/posts/{id}")
async def delete_post(id: str, token: str):
    user = await get_current_user(token)
    from beanie import PydanticObjectId
    try:
        post = await CommunityPost.get(PydanticObjectId(id))
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        if post.userEmail.lower() != user.email.lower() and getattr(user, "role", "member").lower() != "admin":
            raise HTTPException(status_code=403, detail="Not authorized to delete this post")
        
        await post.delete()
        
        # Decrement counter in profile
        profile = await SocialProfile.find_one({"userEmail": user.email})
        if profile and profile.postsCount > 0:
            profile.postsCount -= 1
            await profile.save()
            
        return {"status": "success", "message": "Post deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
async def enrich_chats(chats: List[CommunityChat]) -> List[dict]:
    if not chats: return []
    emails = {c.userEmail.strip().lower() for c in chats if c.userEmail}
    
    users = await User.find({"email": {"$in": list(emails)}}).to_list()
    user_map = {u.email.strip().lower(): u for u in users}
    
    profiles = await SocialProfile.find({"userEmail": {"$in": list(emails)}}).to_list()
    profile_map = {p.userEmail.strip().lower(): p for p in profiles}
    
    enriched = []
    for c in chats:
        email_key = c.userEmail.strip().lower()
        u = user_map.get(email_key)
        sp = profile_map.get(email_key)
        
        avatar = u.profilePicture if (u and u.profilePicture) else "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
        handle = sp.handle if (sp and sp.handle) else (f"{u.firstName} {u.lastName}" if u else c.userName)
        
        role = "MEMBER"
        if u:
            u_role = getattr(u, "role", "member").lower()
            if "admin" in u_role:
                role = "ADMIN"
            elif "trainer" in u_role:
                role = "TRAINER"
        
        is_verified = sp.isVerified if sp else False
        
        chat_dict = c.model_dump()
        chat_dict["id"] = str(c.id)
        chat_dict["_id"] = str(c.id)
        chat_dict["avatar"] = avatar
        chat_dict["userName"] = handle
        chat_dict["role"] = role
        chat_dict["isVerified"] = is_verified
        chat_dict["timestamp"] = c.timestamp.isoformat()
        enriched.append(chat_dict)
    return enriched

@router.get("/chat/members")
async def get_chat_members(token: str):
    current_user = await get_current_user(token)
    
    profiles = await SocialProfile.find_all().to_list()
    emails = {p.userEmail.strip().lower() for p in profiles if p.userEmail}
    
    users = await User.find({"email": {"$in": list(emails)}}).to_list()
    user_map = {u.email.strip().lower(): u for u in users}
    
    members = []
    for p in profiles:
        email_key = p.userEmail.strip().lower()
        u = user_map.get(email_key)
        
        avatar = u.profilePicture if (u and u.profilePicture) else "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
        role = "MEMBER"
        points = 0
        if u:
            u_role = getattr(u, "role", "member").lower()
            if "admin" in u_role:
                role = "ADMIN"
            elif "trainer" in u_role:
                role = "TRAINER"
            points = getattr(u, "points", 0)
            
        status = "online" if manager.is_online(email_key) else "offline"
        
        members.append({
            "email": p.userEmail,
            "handle": p.handle or (f"{u.firstName} {u.lastName}" if u else "gym_member"),
            "avatar": avatar,
            "role": role,
            "isVerified": p.isVerified,
            "points": points,
            "status": status
        })
        
    def sort_key(m):
        role_val = 0 if m["role"] == "ADMIN" else (1 if m["role"] == "TRAINER" else 2)
        status_val = 0 if m["status"] == "online" else 1
        return (status_val, role_val, -m["points"])
        
    members.sort(key=sort_key)
    return members

@router.get("/chat")
async def get_chat():
    chats = await CommunityChat.find_all().sort("-timestamp").limit(50).to_list()
    chats = chats[::-1] # Chronological order
    return await enrich_chats(chats)

@router.post("/chat/send")
async def send_chat(
    token: str = Form(...),
    message: str = Form(...),
    mediaFile: Optional[UploadFile] = File(None),
    clientMsgId: Optional[str] = Form(None)
):
    user = await get_current_user(token)
    
    # Indempotency Guard: prevent duplicate writes from network replay/retry storms
    if clientMsgId:
        existing = await CommunityChat.find_one({"clientMsgId": clientMsgId})
        if existing:
            return {"status": "success", "message": existing}

    media_url = None
    media_type = None
    
    if mediaFile and mediaFile.filename:
        validate_media_file(mediaFile, max_size_mb=10)
        try:
            resource_type = "auto"
            if mediaFile.content_type.startswith("video"): resource_type = "video"
            elif mediaFile.content_type.startswith("audio"): resource_type = "video"

            upload_result = cloudinary.uploader.upload(
                mediaFile.file,
                folder="elite_gym/chat",
                resource_type=resource_type
            )
            media_url = upload_result.get("secure_url")
            media_type = "video" if resource_type == "video" else "image"
        except Exception as e:
            print(f"[CHAT MEDIA ERROR] {e}")

    # Fetch display name from social profile
    sp = await SocialProfile.find_one({"userEmail": user.email})
    display_name = sp.handle if (sp and sp.handle) else f"{user.firstName} {user.lastName}"
    avatar = user.profilePicture if user.profilePicture else "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"

    new_msg = CommunityChat(
        userEmail=user.email,
        userName=display_name,
        message=message,
        mediaUrl=media_url,
        mediaType=media_type,
        clientMsgId=clientMsgId
    )
    await new_msg.insert()

    role = "MEMBER"
    u_role = getattr(user, "role", "member").lower()
    if "admin" in u_role:
        role = "ADMIN"
    elif "trainer" in u_role:
        role = "TRAINER"

    is_verified = sp.isVerified if sp else False

    # Real-time WebSocket Broadcast to ALL connected users
    msg_broadcast = {
        "type": "wall-message",
        "message": {
            "_id": str(new_msg.id),
            "id": str(new_msg.id),
            "userEmail": new_msg.userEmail,
            "userName": display_name,
            "message": message,
            "mediaUrl": media_url,
            "mediaType": media_type,
            "avatar": avatar,
            "role": role,
            "isVerified": is_verified,
            "clientMsgId": clientMsgId,
            "timestamp": new_msg.timestamp.isoformat()
        }
    }
    await manager.broadcast(msg_broadcast)

    return {"status": "success", "message": new_msg}

@router.websocket("/ws")
@router.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: Optional[str] = None):
    try:
        if not token:
            token = websocket.query_params.get("token")
            
        if not token:
            await websocket.close(code=4003)
            return
            
        user = await get_current_user(token)
        user_email = user.email.strip().lower()
        await manager.connect(websocket, user_email)
        try:
            while True:
                data = await websocket.receive_text()
                msg_data = json.loads(data)
                msg_type = msg_data.get("type")
                if msg_type == "ping":
                    await websocket.send_json({"type": "pong"})
                elif msg_type == "typing":
                    await manager.send_personal_message({
                        "type": "typing",
                        "senderEmail": user_email,
                        "isTyping": msg_data.get("isTyping")
                    }, msg_data.get("receiverEmail"))
        except WebSocketDisconnect:
            manager.disconnect(user_email, websocket)
    except Exception as e:
        print(f"[WS ERROR] {e}")

@router.post("/posts/{id}/view")
async def view_post(id: str, token: str):
    user = await get_current_user(token)
    from beanie import PydanticObjectId
    post = await CommunityPost.get(PydanticObjectId(id))
    if not post: return {"status": "ignored"}
    
    if getattr(post, "viewers", None) is None:
        post.viewers = []
    
    email = user.email.strip().lower()
    if email not in post.viewers:
        post.viewers.append(email)
        post.views = len(post.viewers)
        await post.save()
    
    # Track subtle interest
    if post.tags:
        await CommunityBrain.track_interest(user.email, post.tags, weight=0.1)
    
    return {"status": "success", "views": post.views}

@router.post("/posts/{id}/like")
async def like_post(id: str, data: dict):
    token = data.get("token")
    user = await get_current_user(token)
    from beanie import PydanticObjectId
    post = await CommunityPost.get(PydanticObjectId(id))
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post.likes is None: post.likes = []
    is_like = False
    if user.email in post.likes:
        post.likes.remove(user.email)
    else:
        post.likes.append(user.email)
        is_like = True
        # Track Interest
        if post.tags:
            await CommunityBrain.track_interest(user.email, post.tags, weight=1.0)
    
    await post.save()
    
    # Notify Post Owner if it's someone else
    if user.email != post.userEmail and is_like:
        msg = {
            "type": "notification",
            "title": "New Like! ❤️",
            "message": f"{user.firstName} {user.lastName} liked your post.",
            "data": {"postId": id}
        }
        await manager.send_personal_message(msg, post.userEmail)
        await Notification(
            userEmail=post.userEmail,
            title=msg["title"],
            message=msg["message"],
            type="social",
            isRead=False
        ).insert()
        
    return {"likes": len(post.likes)}

@router.post("/posts/{id}/comment")
async def comment_post(id: str, data: dict):
    token = data.get("token")
    user = await get_current_user(token)
    from beanie import PydanticObjectId
    post = await CommunityPost.get(PydanticObjectId(id))
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post.comments is None: post.comments = []
    comment = {
        "id": str(uuid.uuid4()),
        "userEmail": user.email,
        "userName": f"{user.firstName} {user.lastName}",
        "userAvatar": user.profilePicture,
        "text": data.get("text"),
        "parentId": data.get("parentId"),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    post.comments.append(comment)
    
    # Track Interest (Higher weight for comments)
    if post.tags:
        await CommunityBrain.track_interest(user.email, post.tags, weight=2.0)
        
    await post.save()
    
    # Notify Post Owner if it's someone else
    if user.email != post.userEmail:
        msg = {
            "type": "notification",
            "title": "New Comment! 💬",
            "message": f"{user.firstName} {user.lastName} commented on your post.",
            "data": {"postId": id}
        }
        await manager.send_personal_message(msg, post.userEmail)
        await Notification(
            userEmail=post.userEmail,
            title=msg["title"],
            message=msg["message"],
            type="social",
            isRead=False
        ).insert()
        
    return {"comments": post.comments}

@router.post("/transformations/upload")
async def upload_transformation(
    token: str = Form(...),
    mediaFile: UploadFile = File(...)
):
    user = await get_current_user(token)
    validate_media_file(mediaFile, max_size_mb=10)
    
    # Upload to Cloudinary
    upload_result = cloudinary.uploader.upload(
        mediaFile.file,
        folder="elite_gym/transformations"
    )
    media_url = upload_result.get("secure_url")

    # Update Profile
    profile = await SocialProfile.find_one({"userEmail": user.email})
    if profile:
        profile.transformations.append(media_url)
        await profile.save()

    # Also create a post for engagement
    new_post = CommunityPost(
        userEmail=user.email,
        userName=f"{user.firstName} {user.lastName}",
        content=f"Achieved a new elite transformation milestone! 💪 #transformation",
        mediaUrl=media_url,
        mediaType="image",
        tags=["transformation"],
        likes=[],
        comments=[]
    )
    await new_post.insert()
    
    user.points = getattr(user, "points", 0) + 50
    await user.save()

    return {"status": "success", "mediaUrl": media_url}



@router.post("/private/send")
async def send_private_msg(
    token: str = Form(...),
    receiverEmail: str = Form(...),
    message: str = Form(...),
    mediaFile: Optional[UploadFile] = File(None),
    clientMsgId: Optional[str] = Form(None)
):
    user = await get_current_user(token)
    receiverEmail = receiverEmail.strip().lower()

    # Idempotency Guard: prevent duplicate writes from network replay/retry storms
    if clientMsgId:
        existing = await PrivateMessage.find_one({"clientMsgId": clientMsgId})
        if existing:
            return {"status": "success", "message": existing}
    
    media_url = None
    media_type = None
    if mediaFile and mediaFile.filename:
        validate_media_file(mediaFile, max_size_mb=10)
        try:
            resource_type = "video" if mediaFile.content_type.startswith("video") else "image"
            upload_result = cloudinary.uploader.upload(
                mediaFile.file,
                folder="elite_gym/chat",
                resource_type=resource_type
            )
            media_url = upload_result.get("secure_url")
            media_type = "video" if resource_type == "video" else "image"
        except Exception as e:
            print(f"[CHAT UPLOAD ERROR] {e}")

    new_msg = PrivateMessage(
        senderEmail=user.email.strip().lower(),
        receiverEmail=receiverEmail,
        message=message,
        mediaUrl=media_url,
        mediaType=media_type,
        isRead=False,
        clientMsgId=clientMsgId
    )
    await new_msg.insert()

    # Instant WebSocket Alert
    msg_alert = {
        "type": "message",
        "messageId": str(new_msg.id),
        "clientMsgId": clientMsgId,
        "senderName": f"{user.firstName} {user.lastName}",
        "senderEmail": user.email,
        "receiverEmail": receiverEmail,
        "message": message,
        "mediaUrl": media_url,
        "mediaType": media_type,
        "avatar": user.profilePicture,
        "timestamp": new_msg.timestamp.isoformat()
    }
    await manager.send_personal_message(msg_alert, receiverEmail)
    await manager.send_personal_message(msg_alert, user.email)
    
    return {"status": "success", "message": new_msg}

@router.get("/private/history/{otherEmail}")

async def get_private_history(otherEmail: str, token: str):
    user = await get_current_user(token)
    otherEmail = otherEmail.strip().lower()
    userEmail = user.email.strip().lower()
    
    messages = await PrivateMessage.find({
        "$and": [
            {
                "$or": [
                    {"senderEmail": userEmail, "receiverEmail": otherEmail},
                    {"senderEmail": otherEmail, "receiverEmail": userEmail}
                ]
            },
            {"deletedFor": {"$ne": userEmail}}
        ]
    }).sort("timestamp").to_list()
    
    # Sanitize unsent messages
    for m in messages:
        if m.isUnsent:
            m.message = "Message unsent"
            m.mediaUrl = None
            m.mediaType = None
            
    return messages

@router.get("/conversations")

async def get_conversations(token: str):
    user = await get_current_user(token)
    email = user.email.strip().lower()
    
    # Find unique users the current user has chatted with
    sent = await PrivateMessage.find({"senderEmail": email}).to_list()
    received = await PrivateMessage.find({"receiverEmail": email}).to_list()
    
    partners = set()
    for m in sent: partners.add(m.receiverEmail)
    for m in received: partners.add(m.senderEmail)
    
    data = []
    for p_email in partners:
        p_user = await User.find_one(User.email == p_email)
        if not p_user: continue
        
        # Get last message
        last_msg = await PrivateMessage.find({
            "$and": [
                {
                    "$or": [
                        {"senderEmail": email, "receiverEmail": p_email},
                        {"senderEmail": p_email, "receiverEmail": email}
                    ]
                },
                {"deletedFor": {"$ne": email}}
            ]
        }).sort("-timestamp").first_or_none()
        
        last_msg_text = ""
        if last_msg:
            last_msg_text = "Message unsent" if last_msg.isUnsent else last_msg.message
            
        unread_count = await PrivateMessage.find({
            "senderEmail": p_email,
            "receiverEmail": email,
            "isRead": False
        }).count()

        data.append({
            "email": p_email,
            "name": f"{p_user.firstName} {p_user.lastName}",
            "avatar": p_user.profilePicture,
            "lastMessage": last_msg_text,
            "timestamp": last_msg.timestamp if last_msg else datetime.utcnow(),
            "isOnline": manager.is_online(p_email),
            "unreadCount": unread_count
        })
    
    # Sort by most recent
    data.sort(key=lambda x: x["timestamp"], reverse=True)
    return data

@router.get("/notifications")
async def get_activity_notifications(token: str):
    user = await get_current_user(token)
    email_lower = user.email.strip().lower()
    notes = await Notification.find({
        "$or": [
            {"is_global": True},
            {"userEmail": email_lower},
            {"userEmail": {"$regex": f"^{email_lower}$", "$options": "i"}}
        ]
    }).sort("-created_at").limit(20).to_list()
    return notes

@router.get("/explore/trending")
async def get_trending(token: str):
    await get_current_user(token)
    # Aggregate top tags from recent posts
    all_posts = await CommunityPost.find_all().to_list()
    tag_counts = {}
    for p in all_posts:
        if p.tags:
            for t in p.tags:
                tag_counts[t] = tag_counts.get(t, 0) + 1
    
    trending_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:4]
    
    # Get high-engagement posts for discovery
    discovery_posts = sorted(all_posts, key=lambda x: len(x.likes) + x.views, reverse=True)[:15]
    enriched_discovery = await enrich_posts(discovery_posts)
    
    return {
        "tags": [t[0] for t in trending_tags],
        "discovery": enriched_discovery
    }

@router.get("/explore/tags/{tag}")
async def search_hashtag(tag: str, token: str):
    await get_current_user(token)
    posts = await CommunityPost.find({"tags": tag}).sort("-timestamp").to_list()
    return await enrich_posts(posts)

@router.get("/rankings")
async def get_public_rankings(token: str):
    await get_current_user(token)
    # Fetch all social profiles and join with User data for names/avatars
    profiles = await SocialProfile.find_all().to_list()
    
    rankings = []
    for p in profiles:
        u = await User.find_one(User.email == p.userEmail)
        if not u: continue
        rankings.append({
            "handle": p.handle,
            "firstName": u.firstName,
            "lastName": u.lastName,
            "avatar": u.profilePicture,
            "points": getattr(u, 'points', 0),
            "rank": "ELITE MEMBER" if not p.isVerified else "ELITE TRAINER",
            "isVerified": p.isVerified
        })
    
    # Sort by points descending
    rankings.sort(key=lambda x: x["points"], reverse=True)
    return rankings[:4] # Return top 20 for public view

@router.get("/search/global")
async def search_global(q: str, token: str):
    await get_current_user(token)
    # Search Users
    users = await User.find({
        "$or": [
            {"email": {"$regex": q, "$options": "i"}},
            {"firstName": {"$regex": q, "$options": "i"}},
            {"lastName": {"$regex": q, "$options": "i"}},
            {"nickname": {"$regex": q, "$options": "i"}}
        ]
    }).limit(10).to_list()
    
    # Search Profiles (Trainers)
    profiles = await SocialProfile.find({
        "$or": [
            {"handle": {"$regex": q, "$options": "i"}},
            {"fitnessGoals": {"$regex": q, "$options": "i"}}
        ]
    }).limit(10).to_list()
    
    # Search Posts (Hashtags/Content)
    posts = await CommunityPost.find({
        "$or": [
            {"content": {"$regex": q, "$options": "i"}},
            {"tags": {"$regex": q, "$options": "i"}}
        ]
    }).limit(10).to_list()
    
    enriched_posts = await enrich_posts(posts)
    return {
        "users": users,
        "profiles": profiles,
        "posts": enriched_posts
    }

@router.get("/users/search")
async def search_users(q: str, token: str):
    await get_current_user(token)
    # Search by firstName, lastName or email
    users = await User.find({
        "$or": [
            {"firstName": {"$regex": q, "$options": "i"}},
            {"lastName": {"$regex": q, "$options": "i"}},
            {"email": {"$regex": q, "$options": "i"}}
        ]
    }).limit(10).to_list()
    
    return [{
        "email": u.email,
        "name": f"{u.firstName} {u.lastName}",
        "avatar": u.profilePicture
    } for u in users]

@router.get("/unread")
async def get_unread_count(token: str):
    user = await get_current_user(token)
    count = await PrivateMessage.find({
        "receiverEmail": user.email.strip().lower(),
        "isRead": False
    }).count()
    return {"unread": count}

@router.post("/private/read/{otherEmail}")
async def mark_as_read(otherEmail: str, token: str):
    user = await get_current_user(token)
    otherEmail = otherEmail.strip().lower()
    userEmail = user.email.strip().lower()
    
    messages = await PrivateMessage.find({
        "senderEmail": otherEmail,
        "receiverEmail": userEmail,
        "isRead": False
    }).to_list()
    
    for msg in messages:
        msg.isRead = True
        await msg.save()
        
    # Notify sender that their messages have been read
    if messages:
        try:
            await manager.send_personal_message({
                "type": "read-receipt",
                "readerEmail": userEmail
            }, otherEmail)
        except Exception as ws_err:
            print(f"[WS READ RECEIPT ERROR] {ws_err}")
        
    return {"status": "success"}

@router.post("/users/{email}/follow")
async def toggle_follow(email: str, token: str):
    user = await get_current_user(token)
    target_email = email.strip().lower()
    my_email = user.email.strip().lower()

    if target_email == my_email:
        raise HTTPException(status_code=400, detail="Cannot follow yourself.")

    my_profile = await SocialProfile.find_one({"userEmail": my_email})
    target_profile = await SocialProfile.find_one({"userEmail": target_email})

    if not my_profile or not target_profile:
        raise HTTPException(status_code=404, detail="Profile not found.")

    is_following = my_email in target_profile.followers
    if is_following:
        target_profile.followers.remove(my_email)
        my_profile.following.remove(target_email)
    else:
        target_profile.followers.append(my_email)
        my_profile.following.append(target_email)
        
        # Notify target
        msg = {
            "type": "notification",
            "title": "New Follower! 👤",
            "message": f"{user.firstName} started following you.",
            "data": {"userEmail": my_email}
        }
        await manager.send_personal_message(msg, target_email)
        await Notification(
            userEmail=target_email,
            title=msg["title"],
            message=msg["message"],
            type="social",
            isRead=False
        ).insert()

    await my_profile.save()
    await target_profile.save()

    return {"isFollowing": not is_following, "followers": len(target_profile.followers)}

@router.get("/profile/followers")
async def get_followers(token: str, email: Optional[str] = None):
    user = await get_current_user(token)
    target_email = email.strip().lower() if email else user.email.strip().lower()
    
    profile = await SocialProfile.find_one({"userEmail": target_email})
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")
    
    result = []
    followers_list = profile.followers or []
    for follower_email in followers_list:
        follower_user = await User.find_one({"email": follower_email})
        follower_profile = await SocialProfile.find_one({"userEmail": follower_email})
        if follower_user:
            result.append({
                "email": follower_email,
                "name": f"{follower_user.firstName} {follower_user.lastName}",
                "nickname": follower_profile.handle if follower_profile else (follower_user.nickname or follower_email.split('@')[0]),
                "avatar": follower_user.profilePicture or "https://cdn-icons-png.flaticon.com/512/3135/3135715.png",
                "bio": follower_user.bio or "",
                "isFollowing": user.email.strip().lower() in [e.strip().lower() for e in (follower_profile.followers or []) if e]
            })
    return result

@router.get("/profile/following")
async def get_following(token: str, email: Optional[str] = None):
    user = await get_current_user(token)
    target_email = email.strip().lower() if email else user.email.strip().lower()
    
    profile = await SocialProfile.find_one({"userEmail": target_email})
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")
    
    result = []
    following_list = profile.following or []
    for following_email in following_list:
        following_user = await User.find_one({"email": following_email})
        following_profile = await SocialProfile.find_one({"userEmail": following_email})
        if following_user:
            result.append({
                "email": following_email,
                "name": f"{following_user.firstName} {following_user.lastName}",
                "nickname": following_profile.handle if following_profile else (following_user.nickname or following_email.split('@')[0]),
                "avatar": following_user.profilePicture or "https://cdn-icons-png.flaticon.com/512/3135/3135715.png",
                "bio": following_user.bio or "",
                "isFollowing": user.email.strip().lower() in [e.strip().lower() for e in (following_profile.followers or []) if e]
            })
    return result

@router.get("/users/suggestions")
async def get_suggestions(token: str):
    user = await get_current_user(token)
    my_email = user.email.strip().lower()
    my_profile = await SocialProfile.find_one({"userEmail": my_email})
    
    # Get profiles I don't follow yet (excluding myself)
    all_profiles = await SocialProfile.find({"userEmail": {"$ne": my_email}}).to_list()
    suggestions = []
    
    for p in all_profiles:
        if p.userEmail not in my_profile.following:
            u = await User.find_one({"email": p.userEmail})
            if u:
                suggestions.append({
                    "email": p.userEmail,
                    "handle": p.handle,
                    "name": f"{u.firstName} {u.lastName}",
                    "avatar": u.profilePicture
                })
    
    return suggestions[:5] # Return top 5 suggestions

@router.get("/users/{email}/profile")
async def get_any_profile(email: str, token: str):
    user = await get_current_user(token)
    target_email = email.strip().lower()
    my_email = user.email.strip().lower()

    profile = await SocialProfile.find_one({"userEmail": target_email})
    if not profile: raise HTTPException(status_code=404)
    
    u = await User.find_one({"email": target_email})
    my_p = await SocialProfile.find_one({"userEmail": my_email})

    # Calculate mutuals
    mutuals = [e for e in profile.followers if e in my_p.following]
    
    return {
        "handle": profile.handle,
        "bio": profile.bio,
        "avatar": u.profilePicture if u else None,
        "name": f"{u.firstName} {u.lastName}" if u else "Elite Member",
        "followers": len(profile.followers),
        "following": len(profile.following),
        "isFollowing": my_email in profile.followers,
        "mutualsCount": len(mutuals),
        "userEmail": target_email
    }

@router.post("/stories/create")
async def create_story(token: str = Form(...), mediaFile: UploadFile = File(...)):
    user = await get_current_user(token)
    validate_media_file(mediaFile, max_size_mb=10)
    
    resource_type = "video" if mediaFile.content_type.startswith("video") else "image"
    import cloudinary.uploader
    upload_result = cloudinary.uploader.upload(
        mediaFile.file,
        folder="elite_gym/stories",
        resource_type=resource_type
    )

    story = Story(
        userEmail=user.email,
        userName=f"{user.firstName} {user.lastName}",
        mediaUrl=upload_result.get("secure_url"),
        mediaType="video" if resource_type == "video" else "image",
        expiresAt=datetime.utcnow() + timedelta(hours=24)
    )
    await story.insert()
    return {"status": "success", "story": story}

@router.post("/profile/update")
async def update_profile(
    token: str = Form(...),
    handle: Optional[str] = Form(None),
    bio: Optional[str] = Form(None),
    fitnessGoals: Optional[str] = Form(None),
    profileFile: Optional[UploadFile] = File(None)
):
    user = await get_current_user(token)
    
    # Update Social Profile
    sp = await SocialProfile.find_one({"userEmail": user.email})
    if not sp:
        sp = SocialProfile(userEmail=user.email, handle=user.email.split('@')[0])
        await sp.insert()

    if handle is not None and handle != sp.handle:
        # Check uniqueness
        existing = await SocialProfile.find_one({"handle": handle})
        if existing:
            raise HTTPException(status_code=400, detail="Handle already manifest by another elite member.")
        sp.handle = handle

    if bio is not None: sp.bio = bio
    if fitnessGoals is not None: sp.fitnessGoals = fitnessGoals
    
    # Update User Model for bio consistency
    u = await User.find_one({"email": user.email})
    if bio is not None: u.bio = bio

    if profileFile and profileFile.filename:
        validate_media_file(profileFile, max_size_mb=10)
        try:
            upload_result = cloudinary.uploader.upload(
                profileFile.file,
                folder="elite_gym/profiles",
                transformation=[
                    {"width": 400, "height": 400, "crop": "fill", "gravity": "face"},
                    {"quality": "auto", "fetch_format": "auto"}
                ]
            )
            pic_url = upload_result.get("secure_url")
            u.profilePicture = pic_url
            # SocialProfile doesn't store avatar, it fetches from User or we can add it
        except Exception as e:
            print(f"[PROFILE PIC ERROR] {e}")

    await sp.save()
    await u.save()
    
    return {"status": "success", "profile": sp, "user": {"bio": u.bio, "profilePicture": u.profilePicture}}

@router.post("/initialize")
async def initialize_social(token: str = Form(...), handle: str = Form(...), bio: str = Form("")):
    user = await get_current_user(token)
    
    # Check if handle already exists
    existing_handle = await SocialProfile.find_one({"handle": handle})
    if existing_handle:
        raise HTTPException(status_code=400, detail="Handle already taken by another elite member.")

    profile = await SocialProfile.find_one({"userEmail": user.email})
    if not profile:
        profile = SocialProfile(userEmail=user.email, handle=handle, bio=bio, isInitialized=True)
        await profile.insert()
    else:
        profile.handle = handle
        profile.bio = bio
        profile.isInitialized = True
        await profile.save()
    
    return {"status": "success", "profile": profile}

@router.get("/profile")
async def get_social_profile(token: str):
    user = await get_current_user(token)
    profile = await SocialProfile.find_one({"userEmail": user.email})
    if not profile:
        profile = SocialProfile(userEmail=user.email, handle=user.email.split('@')[0], isInitialized=False)
        await profile.insert()
    
    # Unified Data Manifest
    return {
        "userEmail": user.email,
        "userName": f"{user.firstName} {user.lastName}",
        "avatar": user.profilePicture,
        "handle": profile.handle,
        "bio": profile.bio,
        "fitnessGoals": profile.fitnessGoals,
        "transformations": profile.transformations,
        "badges": profile.badges,
        "followers": profile.followers,
        "following": profile.following,
        "isVerified": profile.isVerified,
        "isInitialized": profile.isInitialized
    }

@router.get("/stories")
async def get_stories(token: str):
    await get_current_user(token)
    now = datetime.utcnow()
    stories = await Story.find({"expiresAt": {"$gt": now}}).sort("-timestamp").to_list()
    
    # Group by user
    grouped = {}
    for s in stories:
        if s.userEmail not in grouped:
            u = await User.find_one({"email": s.userEmail})
            grouped[s.userEmail] = {
                "userEmail": s.userEmail,
                "userName": s.userName,
                "avatar": u.profilePicture if u else None,
                "items": []
            }
        
        # Ensure likes exists safely
        story_likes = getattr(s, 'likes', [])
        if story_likes is None:
            story_likes = []
            
        grouped[s.userEmail]["items"].append({
            "id": str(s.id),
            "url": s.mediaUrl,
            "type": s.mediaType,
            "timestamp": s.timestamp,
            "likes": story_likes
        })
    
    return list(grouped.values())

@router.post("/stories/{id}/like")
async def like_story(id: str, data: dict):
    token = data.get("token")
    user = await get_current_user(token)
    
    from beanie import PydanticObjectId
    story = await Story.get(PydanticObjectId(id))
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
        
    if not hasattr(story, 'likes') or story.likes is None:
        story.likes = []
        
    is_liked = False
    if user.email in story.likes:
        story.likes.remove(user.email)
    else:
        story.likes.append(user.email)
        is_liked = True
        
    await story.save()
    return {"status": "success", "isLiked": is_liked, "likes": story.likes}

@router.get("/posts/{id}/likes")
async def get_post_likers(id: str, token: str):
    await get_current_user(token)
    from beanie import PydanticObjectId
    post = await CommunityPost.get(PydanticObjectId(id))
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
        
    likes_emails = post.likes or []
    if not likes_emails:
        return []
        
    # Bulk fetch users and profiles
    users = await User.find({"email": {"$in": likes_emails}}).to_list()
    user_map = {u.email.strip().lower(): u for u in users}
    
    profiles = await SocialProfile.find({"userEmail": {"$in": likes_emails}}).to_list()
    profile_map = {p.userEmail.strip().lower(): p for p in profiles}
    
    likers = []
    for email in likes_emails:
        email_key = email.strip().lower()
        u = user_map.get(email_key)
        sp = profile_map.get(email_key)
        if u:
            likers.append({
                "email": u.email,
                "name": f"{u.firstName} {u.lastName}",
                "handle": sp.handle if (sp and sp.handle) else (u.username or u.email.split('@')[0]),
                "avatar": u.profilePicture or "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
            })
    return likers

@router.post("/posts/{id}/edit")
async def edit_post(id: str, data: dict):
    token = data.get("token")
    user = await get_current_user(token)
    from beanie import PydanticObjectId
    post = await CommunityPost.get(PydanticObjectId(id))
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
        
    if post.userEmail != user.email:
        raise HTTPException(status_code=403, detail="Not authorized to edit this broadcast.")
        
    post.content = data.get("content", post.content)
    post.tags = [tag.strip("#").lower() for tag in post.content.split() if tag.startswith("#")]
    
    import re
    tagged_emails = []
    handles = re.findall(r"@([a-zA-Z0-9_]+)", post.content)
    for h in handles:
        sp = await SocialProfile.find_one({"handle": re.compile(f"^{h}$", re.IGNORECASE)})
        if sp:
            tagged_emails.append(sp.userEmail.strip().lower())
        else:
            u = await User.find_one({"nickname": re.compile(f"^{h}$", re.IGNORECASE)})
            if u:
                tagged_emails.append(u.email.strip().lower())
    post.taggedUsers = list(set(tagged_emails))
    
    await post.save()
    return {"status": "success", "post": post}

@router.post("/posts/{id}/archive")
async def archive_post(id: str, data: dict):
    token = data.get("token")
    user = await get_current_user(token)
    from beanie import PydanticObjectId
    post = await CommunityPost.get(PydanticObjectId(id))
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
        
    if post.userEmail != user.email:
        raise HTTPException(status_code=403, detail="Not authorized to archive this broadcast.")
        
    post.isArchived = data.get("archive", not post.isArchived)
    await post.save()
    return {"status": "success", "isArchived": post.isArchived}

@router.post("/posts/{id}/delete")
async def delete_post(id: str, data: dict):
    token = data.get("token")
    user = await get_current_user(token)
    from beanie import PydanticObjectId
    post = await CommunityPost.get(PydanticObjectId(id))
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
        
    if post.userEmail != user.email:
        raise HTTPException(status_code=403, detail="Not authorized to delete this broadcast.")
        
    await post.delete()
    return {"status": "success", "message": "Broadcast removed from the database."}

@router.post("/private/unsend/{msgId}")
async def unsend_private_message(msgId: str, token: str):
    user = await get_current_user(token)
    user_email = user.email.strip().lower()
    
    from beanie import PydanticObjectId
    msg = await PrivateMessage.get(PydanticObjectId(msgId))
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
        
    # Authorization check: only sender can unsend
    if msg.senderEmail.strip().lower() != user_email:
        raise HTTPException(status_code=403, detail="Unauthorized to unsend this message")
        
    msg.isUnsent = True
    await msg.save()
    
    # Broadcast unsend event
    unsend_event = {
        "type": "message_unsend",
        "messageId": str(msg.id),
        "senderEmail": msg.senderEmail,
        "receiverEmail": msg.receiverEmail
    }
    await manager.send_personal_message(unsend_event, msg.receiverEmail)
    await manager.send_personal_message(unsend_event, msg.senderEmail)
    
    return {"status": "success", "messageId": str(msg.id)}

@router.post("/private/delete/{msgId}")
async def delete_private_message_for_me(msgId: str, token: str):
    user = await get_current_user(token)
    user_email = user.email.strip().lower()
    
    from beanie import PydanticObjectId
    msg = await PrivateMessage.get(PydanticObjectId(msgId))
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
        
    # Authorization check: must be sender or receiver
    if msg.senderEmail.strip().lower() != user_email and msg.receiverEmail.strip().lower() != user_email:
        raise HTTPException(status_code=403, detail="Unauthorized to delete this message")
        
    if user_email not in msg.deletedFor:
        msg.deletedFor.append(user_email)
        await msg.save()
        
    # Broadcast delete-for-me event to all client devices of this user
    delete_event = {
        "type": "message_delete_for_me",
        "messageId": str(msg.id)
    }
    await manager.send_personal_message(delete_event, user_email)
    
    return {"status": "success", "messageId": str(msg.id)}

# =========================================
# FORUMS ENDPOINTS
# =========================================
@router.get("/forums")
async def get_forums(token: str, category: Optional[str] = None):
    await get_current_user(token)
    query = {}
    if category and category != "All":
        query["category"] = category
    topics = await CommunityForumTopic.find(query).sort("-timestamp").to_list()
    return topics

@router.post("/forums/create")
async def create_forum_topic(
    token: str = Form(...),
    category: str = Form(...),
    title: str = Form(...),
    content: str = Form(...),
    mediaFiles: List[UploadFile] = File(default=[])
):
    user = await get_current_user(token)
    
    uploaded_media = []
    if mediaFiles:
        for file in mediaFiles:
            if file and file.filename:
                validate_media_file(file, max_size_mb=20)
                try:
                    filename_lower = file.filename.lower()
                    is_audio = False
                    is_video = False
                    if (file.content_type and file.content_type.startswith("audio")) or \
                       any(filename_lower.endswith(ext) for ext in [".mp3", ".wav", ".ogg", ".m4a"]):
                        is_audio = True
                    elif (file.content_type and file.content_type.startswith("video")) or \
                       any(filename_lower.endswith(ext) for ext in [".mp4", ".mov", ".avi", ".mkv", ".webm", ".3gp", ".m4v"]):
                        is_video = True
                    
                    resource_type = "video" if (is_video or is_audio) else "image"
                    upload_result = cloudinary.uploader.upload(
                        file.file,
                        folder="elite_gym/forums",
                        resource_type=resource_type
                    )
                    media_type = "audio" if is_audio else ("video" if is_video else "image")
                    uploaded_media.append({
                        "url": upload_result.get("secure_url"),
                        "type": media_type
                    })
                except Exception as e:
                    print(f"[FORUM MEDIA ERROR] {e}")

    topic = CommunityForumTopic(
        userEmail=user.email,
        userName=f"{user.firstName} {user.lastName}",
        category=category,
        title=title,
        content=content,
        mediaFiles=uploaded_media
    )
    await topic.insert()
    
    user.points = getattr(user, "points", 0) + 50
    await user.save()
    
    return {"status": "success", "topic": topic}

@router.delete("/forums/{id}")
async def delete_forum_topic(id: str, token: str):
    user = await get_current_user(token)
    from beanie import PydanticObjectId
    try:
        topic = await CommunityForumTopic.get(PydanticObjectId(id))
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")
        if topic.userEmail.lower() != user.email.lower() and getattr(user, "role", "member").lower() != "admin":
            raise HTTPException(status_code=403, detail="Not authorized to delete this topic")
        await topic.delete()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/forums/{id}/reply")
async def reply_forum(id: str, token: str = Form(...), text: str = Form(...)):
    user = await get_current_user(token)
    from beanie import PydanticObjectId
    topic = await CommunityForumTopic.get(PydanticObjectId(id))
    if not topic: raise HTTPException(404, "Not found")
    
    reply = {
        "id": str(uuid.uuid4()),
        "userEmail": user.email,
        "userName": f"{user.firstName} {user.lastName}",
        "text": text,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    topic.replies.append(reply)
    await topic.save()
    return {"status": "success", "replies": topic.replies}

# =========================================
# EVENTS ENDPOINTS
# =========================================
@router.get("/events")
async def get_events(token: str):
    await get_current_user(token)
    events = await CommunityEvent.find(CommunityEvent.date >= datetime.utcnow()).sort("date").to_list()
    from datetime import timezone
    for e in events:
        if e.date and e.date.tzinfo is None:
            e.date = e.date.replace(tzinfo=timezone.utc)
    return events

@router.delete("/events/{id}")
async def delete_event(id: str, token: str):
    user = await get_current_user(token)
    role = getattr(user, "role", "member").lower()
    if "admin" not in role and "trainer" not in role:
        raise HTTPException(403, "Not authorized to delete events")
        
    from beanie import PydanticObjectId
    event = await CommunityEvent.get(PydanticObjectId(id))
    if not event:
        raise HTTPException(404, "Event not found")
        
    await event.delete()
    return {"message": "Event deleted successfully"}

@router.post("/events/create")
async def create_event(
    token: str = Form(...),
    title: str = Form(...),
    description: str = Form(...),
    date: str = Form(...), # ISO string
    location: str = Form(...),
    type: str = Form(...)
):
    user = await get_current_user(token)
    # Check if admin/trainer
    role = getattr(user, "role", "member").lower()
    if "admin" not in role and "trainer" not in role:
        raise HTTPException(403, "Not authorized to create events")
        
    dt = datetime.fromisoformat(date.replace("Z", "+00:00"))
    event = CommunityEvent(
        title=title,
        description=description,
        date=dt,
        location=location,
        type=type,
        createdBy=user.email
    )
    await event.insert()
    return {"status": "success"}

@router.post("/events/{id}/rsvp")
async def rsvp_event(id: str, data: dict):
    token = data.get("token")
    user = await get_current_user(token)
    from beanie import PydanticObjectId
    event = await CommunityEvent.get(PydanticObjectId(id))
    if not event: raise HTTPException(404, "Not found")
    
    if user.email in event.rsvps:
        event.rsvps.remove(user.email)
    else:
        event.rsvps.append(user.email)
    await event.save()
    return {"status": "success", "rsvps": event.rsvps}

# =========================================
# SPOTLIGHT ENDPOINTS
# =========================================
@router.get("/spotlight")
async def get_spotlight(token: str):
    await get_current_user(token)
    now = datetime.utcnow()
    spotlight = await MemberSpotlight.find(
        MemberSpotlight.activeFrom <= now,
        MemberSpotlight.activeUntil >= now
    ).sort("-timestamp").first_or_none()
    
    if spotlight:
        from datetime import timezone
        if spotlight.activeFrom and spotlight.activeFrom.tzinfo is None:
            spotlight.activeFrom = spotlight.activeFrom.replace(tzinfo=timezone.utc)
        if spotlight.activeUntil and spotlight.activeUntil.tzinfo is None:
            spotlight.activeUntil = spotlight.activeUntil.replace(tzinfo=timezone.utc)
            
    return spotlight

@router.post("/spotlight/create")
async def create_spotlight(
    token: str = Form(...),
    userName: str = Form(...),
    userEmail: str = Form(...),
    bio: str = Form(...),
    achievement: str = Form(...),
    transformationImage: UploadFile = File(...),
    activeFrom: str = Form(...),
    activeUntil: str = Form(...)
):
    user = await get_current_user(token)
    role = getattr(user, "role", "member").lower()
    if "admin" not in role and "trainer" not in role:
        raise HTTPException(403, "Not authorized to create spotlights")

    try:
        dt_from = datetime.fromisoformat(activeFrom.replace("Z", "+00:00"))
        dt_until = datetime.fromisoformat(activeUntil.replace("Z", "+00:00"))
    except Exception:
        raise HTTPException(400, "Invalid date format")

    validate_media_file(transformationImage, max_size_mb=10)
    
    import cloudinary.uploader
    upload_result = cloudinary.uploader.upload(
        transformationImage.file,
        folder="elite_gym/spotlights"
    )
    media_url = upload_result.get("secure_url")

    spotlight = MemberSpotlight(
        userName=userName,
        userEmail=userEmail,
        bio=bio,
        achievement=achievement,
        transformationImage=media_url,
        activeFrom=dt_from,
        activeUntil=dt_until
    )
    await spotlight.insert()
    return {"status": "success", "message": "Spotlight created successfully"}

@router.delete("/spotlight/{id}")
async def delete_spotlight(id: str, token: str):
    user = await get_current_user(token)
    role = getattr(user, "role", "member").lower()
    if "admin" not in role and "trainer" not in role:
        raise HTTPException(403, "Not authorized to delete spotlights")
        
    from beanie import PydanticObjectId
    spotlight = await MemberSpotlight.get(PydanticObjectId(id))
    if not spotlight:
        raise HTTPException(404, "Spotlight not found")
        
    await spotlight.delete()
    return {"message": "Spotlight deleted successfully"}

# =========================================
# LEADERBOARD ENDPOINTS
# =========================================
@router.get("/leaderboard")
async def get_leaderboard(token: str):
    await get_current_user(token)
    users = await User.find_all().to_list()
    # Simple leaderboard based on points
    ranked = []
    for u in users:
        points = getattr(u, "points", 0)
        if points > 0:
            ranked.append({
                "email": u.email,
                "name": f"{u.firstName} {u.lastName}",
                "avatar": getattr(u, "profilePicture", ""),
                "points": points
            })
    ranked.sort(key=lambda x: x["points"], reverse=True)
    return ranked[:50]