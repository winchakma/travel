from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime
import re

class UserBase(BaseModel):
    email: str
    firstName: str
    lastName: str
    phoneNumber: Optional[str] = None

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(regex, v):
            raise ValueError('Invalid email format. Please provide a real email address.')
        return v

class UserCreate(UserBase):
    password: str
    membershipType: Optional[str] = "FREE GUEST"

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(UserBase):
    id: str
    nickname: Optional[str] = "Elite Member"
    bio: Optional[str] = ""
    weight: Optional[float] = 0
    height: Optional[float] = 0
    weightGoal: Optional[float] = 0
    goal: Optional[str] = "Maintenance"
    points: Optional[int] = 0
    membershipType: Optional[str] = "FREE GUEST"
    profilePicture: Optional[str] = "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class ForgotPasswordRequest(BaseModel):
    email: str

class ChangePasswordRequest(BaseModel):
    oldPassword: str
    newPassword: str
    
    @field_validator('newPassword')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v