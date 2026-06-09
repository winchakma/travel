from beanie import Document
from datetime import datetime
from typing import Optional, List
from pydantic import Field

class SupportSession(Document):
    userEmail: str
    userName: str
    targetRole: str # "Normal Admin" or "Super Admin"
    status: str = "open" # open, closed
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "support_sessions"

class SupportChatMessage(Document):
    session_id: str
    sender_type: str # "user" or "admin"
    sender_email: str
    sender_name: str
    message_type: str = "text" # text, image
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "support_chat_messages"
