from beanie import Document
from datetime import datetime
from typing import Optional

class Booking(Document):
    user_email: str
    type: str  # flight, hotel, car, cruise, activity
    details: dict
    price: int
    status: str = "confirmed" # confirmed, canceled, pending
    created_at: datetime = datetime.utcnow()

    class Settings:
        name = "bookings"

class Activity(Document):
    userId: Optional[str] = None
    userEmail: Optional[str] = "guest"
    action: str # signup, login, bmr_calc, workout_verified, book_session, shop_purchase
    details: Optional[str] = None
    timestamp: datetime = datetime.utcnow()

    class Settings:
        name = "activities"

class Order(Document):
    userId: str
    userEmail: str
    userName: str
    phone: Optional[str] = None
    address: Optional[str] = None
    items: str
    total: float
    paymentMethod: str
    status: str = "processing" # processing, shipped, delivered, canceled
    timestamp: datetime = datetime.utcnow()

    class Settings:
        name = "orders"

class ClassSchedule(Document):
    className: str
    trainerName: str
    day: str # Mon, Tue, etc.
    time: str # 09:00, 18:00
    category: str # HIIT, Strength, etc.
    capacity: int = 20
    enrolled: int = 0
    status: str = "Active" # Active, Cancelled

    class Settings:
        name = "class_schedules"

class Notification(Document):
    userEmail: Optional[str] = None
    title: str
    message: str
    type: str = "info" # info, warning, success, social
    created_at: datetime = datetime.utcnow()
    is_global: bool = True
    isRead: bool = False

    class Settings:
        name = "notifications"

class Video(Document):
    title: str
    category: str
    duration: str
    thumbnail: str
    url: str
    trainer: str
    created_at: datetime = datetime.utcnow()

class UserFeedback(Document):
    userEmail: str
    userName: Optional[str] = None
    category: str # feature, bug, praise, suggestion
    message: str
    timestamp: datetime = datetime.utcnow()
    status: str = "new" # new, read, resolved

    class Settings:
        name = "user_feedbacks"

class MentorshipRequest(Document):
    name: str
    email: str
    preferred_date: str
    fitness_level: str
    message: str
    status: str = "pending"
    timestamp: datetime = datetime.utcnow()

    class Settings:
        name = "mentorship_requests"

class SupportMessage(Document):
    senderEmail: str
    senderName: str
    recipientType: str # "Owner" or "Trainer"
    message: str
    reply: Optional[str] = None
    status: str = "open" # "open", "resolved"
    timestamp: datetime = datetime.utcnow()
    
    class Settings:
        name = "support_messages"
