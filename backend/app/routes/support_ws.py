from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends, UploadFile, File
from typing import Dict, List
import json
import jwt
import os
from datetime import datetime
from app.models.support import SupportSession, SupportChatMessage
from app.models.user import User
import cloudinary.uploader

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"

router = APIRouter(prefix="/support-ws", tags=["Support WebSockets"])

class ConnectionManager:
    def __init__(self):
        # Maps user/admin email to a list of their active WebSocket connections
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Keep track of role for admins (to route messages)
        self.admin_roles: Dict[str, str] = {} # email -> "superadmin" or "trainer"

    async def connect(self, websocket: WebSocket, email: str, role: str = "user"):
        await websocket.accept()
        if email not in self.active_connections:
            self.active_connections[email] = []
        self.active_connections[email].append(websocket)
        if role != "user":
            self.admin_roles[email] = role

    def disconnect(self, websocket: WebSocket, email: str):
        if email in self.active_connections:
            self.active_connections[email].remove(websocket)
            if not self.active_connections[email]:
                del self.active_connections[email]
                if email in self.admin_roles:
                    del self.admin_roles[email]

    async def send_personal_message(self, message: dict, email: str):
        if email in self.active_connections:
            for connection in self.active_connections[email]:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception:
                    pass

    async def broadcast_to_admins(self, message: dict, target_role: str, exclude_email: str = None):
        # target_role is "Normal Admin" (trainer) or "Super Admin" (superadmin)
        mapped_role = "superadmin" if target_role == "Super Admin" else "trainer"
        for email, role in self.admin_roles.items():
            if role == mapped_role and email != exclude_email:
                for connection in self.active_connections.get(email, []):
                    try:
                        await connection.send_text(json.dumps(message))
                    except Exception:
                        pass

manager = ConnectionManager()

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except:
        return None

@router.websocket("/chat")
async def support_chat_endpoint(websocket: WebSocket, token: str):
    email = decode_token(token)
    if not email:
        await websocket.close(code=1008)
        return

    # Verify user and get role
    user = await User.find_one(User.email == email)
    if not user:
        await websocket.close(code=1008)
        return
    db_role = user.role.lower() if user.role else "user"
    if db_role in ["super_admin", "superadmin", "owner"]:
        role = "superadmin"
    elif db_role in ["admin", "trainer"]:
        role = "trainer"
    else:
        role = "user"
    await manager.connect(websocket, email, role)

    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            action = message_data.get("action")

            if action == "ping":
                continue

            if action == "send_message":
                target_role = message_data.get("targetRole", "Normal Admin")
                content = message_data.get("content")
                msg_type = message_data.get("type", "text")

                session = await SupportSession.find_one(
                    SupportSession.userEmail == email, 
                    SupportSession.targetRole == target_role,
                    SupportSession.status == "open"
                )
                if not session:
                    session = SupportSession(userEmail=email, userName=f"{user.firstName} {user.lastName}", targetRole=target_role)
                    await session.insert()
                else:
                    session.updated_at = datetime.utcnow()
                    await session.save()

                chat_msg = SupportChatMessage(
                    session_id=str(session.id),
                    sender_type="user",
                    sender_email=email,
                    sender_name=f"{user.firstName} {user.lastName}",
                    message_type=msg_type,
                    content=content
                )
                await chat_msg.insert()

                payload = {
                    "event": "new_message",
                    "session_id": str(session.id),
                    "sender_type": "user",
                    "sender_email": email,
                    "sender_name": chat_msg.sender_name,
                    "message_type": msg_type,
                    "content": content,
                    "created_at": chat_msg.created_at.isoformat()
                }

                await manager.send_personal_message(payload, email)
                await manager.broadcast_to_admins(payload, target_role, exclude_email=email)

            elif action == "admin_reply":
                if role == "user":
                    continue

                session_id = message_data.get("session_id")
                content = message_data.get("content")
                msg_type = message_data.get("type", "text")

                session = await SupportSession.get(session_id)
                if not session:
                    continue
                
                session.updated_at = datetime.utcnow()
                await session.save()

                chat_msg = SupportChatMessage(
                    session_id=str(session.id),
                    sender_type="admin",
                    sender_email=email,
                    sender_name=f"{user.firstName} {user.lastName}",
                    message_type=msg_type,
                    content=content
                )
                await chat_msg.insert()

                payload = {
                    "event": "new_message",
                    "session_id": str(session.id),
                    "sender_type": "admin",
                    "sender_email": email,
                    "sender_name": chat_msg.sender_name,
                    "message_type": msg_type,
                    "content": content,
                    "created_at": chat_msg.created_at.isoformat()
                }

                await manager.send_personal_message(payload, session.userEmail)
                await manager.broadcast_to_admins(payload, session.targetRole, exclude_email=session.userEmail)

            elif action == "fetch_sessions":
                if role == "user":
                    continue
                
                target_role = "Super Admin" if role == "superadmin" else "Normal Admin"
                sessions = await SupportSession.find(SupportSession.targetRole == target_role, SupportSession.status == "open").to_list()
                
                session_list = []
                for s in sessions:
                    session_list.append({
                        "id": str(s.id),
                        "userEmail": s.userEmail,
                        "userName": s.userName,
                        "updated_at": s.updated_at.isoformat()
                    })

                await manager.send_personal_message({
                    "event": "sessions_list",
                    "sessions": session_list
                }, email)

            elif action == "fetch_history":
                session_id = message_data.get("session_id")
                target_role = message_data.get("targetRole")

                if not session_id:
                    session = await SupportSession.find_one(
                        SupportSession.userEmail == email,
                        SupportSession.targetRole == target_role,
                        SupportSession.status == "open"
                    )
                    if session:
                        session_id = str(session.id)
                
                if session_id:
                    messages = await SupportChatMessage.find(SupportChatMessage.session_id == session_id).sort("created_at").to_list()
                    msg_list = [{
                        "id": str(m.id),
                        "sender_type": m.sender_type,
                        "sender_email": m.sender_email,
                        "sender_name": m.sender_name,
                        "message_type": m.message_type,
                        "content": m.content,
                        "created_at": m.created_at.isoformat()
                    } for m in messages]

                    await manager.send_personal_message({
                        "event": "chat_history",
                        "session_id": session_id,
                        "messages": msg_list
                    }, email)
                else:
                    await manager.send_personal_message({
                        "event": "chat_history",
                        "session_id": None,
                        "messages": []
                    }, email)

    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, email)

@router.post("/upload-image")
async def upload_support_image(image: UploadFile = File(...)):
    try:
        result = cloudinary.uploader.upload(image.file, folder="support_chat")
        return {"url": result.get("secure_url")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
