from beanie import Document, Indexed
from datetime import datetime
from pydantic import Field
from typing import Optional

class User(Document):
    firstName: str
    lastName: str
    email: str = Indexed(unique=True)
    hashed_password: Optional[str] = Field(None)
    phoneNumber: Optional[str] = None
    nickname: str = "Elite Member"
    bio: str = "No bio set."
    weight: float = 75.0
    height: float = 180.0
    weightGoal: float = 80.0
    goal: str = "Maintenance"
    points: int = 1250
    membershipType: str = "FREE GUEST"
    membershipClass: str = "D" # A: Elite, B: Pro, C: Admitted, D: Free Trial
    admissionStatus: str = "pending" # pending, submitted, approved
    admissionFeePaid: bool = False
    profilePicture: str = "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
    role: str = "member" # member, admin, super_admin
    isBanned: bool = False
    monthlyFeeStatus: str = "Unpaid" # Paid, Unpaid
    lastFeePaidAmount: float = 0.0
    lastFeePaidDate: Optional[datetime] = None
    created_at: datetime = datetime.utcnow()

    class Settings:
        name = "users"

class AttendanceLog(Document):
    user_id: str
    user_name: str
    arrival_time: str
    date: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "attendance_logs"
