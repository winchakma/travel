from fastapi import APIRouter, HTTPException, Depends, status
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, Token, UserResponse, ForgotPasswordRequest
import secrets
import string

from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/auth", tags=["Auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 1 week

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@router.post("/register")
async def register(user_data: UserCreate):
    email_clean = user_data.email.strip().lower()
    # Check if user exists
    existing_user = await User.find_one(User.email == email_clean)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Bcrypt has a 72-byte limit. Truncate for safety.
    safe_password = user_data.password[:72]
    hashed_password = pwd_context.hash(safe_password)
    
    new_user = User(
        firstName=user_data.firstName,
        lastName=user_data.lastName,
        email=email_clean,
        phoneNumber=user_data.phoneNumber,
        hashed_password=hashed_password,
        membershipType=user_data.membershipType
    )
    await new_user.insert()
    
    # Log Activity
    from app.models.admin import Activity
    await Activity(userId=str(new_user.id), userEmail=new_user.email, action="signup", details="New member joined the Elite.").insert()
    
    token = create_access_token({"sub": new_user.email})
    return {
        "message": "Welcome to the Elite, " + new_user.firstName + "!",
        "token": token, 
        "token_type": "bearer", 
        "user": new_user
    }

@router.post("/login")
async def login(credentials: UserLogin):
    # Dual Login: Search by Email or Phone Number
    email_clean = credentials.email.strip().lower()
    user = await User.find_one({
        "$or": [
            {"email": email_clean},
            {"phoneNumber": credentials.email}
        ]
    })
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    safe_password = credentials.password[:72]
    if not pwd_context.verify(safe_password, user.hashed_password):
        # Log failed attempt if desired, but for now just success
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Log Activity
    from app.models.admin import Activity
    await Activity(userId=str(user.id), userEmail=user.email, action="login", details="Member accessed the HUD.").insert()
    
    # Award points for signing in
    user.points = getattr(user, "points", 0) + 50
    await user.save()
    
    token = create_access_token({"sub": user.email})
    return {
        "message": "Access Granted. Welcome back, " + user.firstName + ".",
        "token": token, 
        "token_type": "bearer", 
        "user": user
    }

@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    email_clean = request.email.strip().lower()
    user = await User.find_one(User.email == email_clean)
    if not user:
        # For security, don't reveal if user exists. Just say email sent.
        return {"message": "If this email is registered, a temporary password has been sent."}
    
    # Generate random 10-character password
    temp_pass = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(10))
    
    # Send Email first to make sure SMTP works
    from app.utils.notifications import NotificationService
    try:
        await NotificationService.send_bulk_email(
            [user.email],
            "Elite Recovery: Your Temporary Password",
            f"Hello {user.firstName},\n\nWe received a request to reset your password. Here is your temporary secure password:\n\n{temp_pass}\n\nUse this to sign in, and then update your password in the Settings menu.\n\nStay Elite!"
        )
    except Exception as e:
        print(f"[ERROR] Recovery email failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to send recovery email. Your password has not been changed.")
    
    # Only update user in DB if the email was sent successfully
    user.hashed_password = pwd_context.hash(temp_pass)
    await user.save()

    return {"message": "A temporary password has been sent to your inbox."}


import time
# High-performance handshake cache to bypass CPU-intensive JWT decode and database lookup during connection storms
_token_cache = {}

async def get_current_user(token: str):
    now = time.time()
    if token in _token_cache:
        expiry, user = _token_cache[token]
        if now < expiry:
            return user
        else:
            del _token_cache[token]
            
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Could not validate credentials")
        email_clean = email.strip().lower()
        user = await User.find_one(User.email == email_clean)
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
            
        # Cache verified user for 120 seconds
        _token_cache[token] = (now + 120, user)
        
        # Periodic cache garbage collection
        if len(_token_cache) > 2000:
            expired_tokens = [t for t, (exp, _) in _token_cache.items() if now > exp]
            for t in expired_tokens:
                del _token_cache[t]
                
        return user
    except Exception:
        raise HTTPException(status_code=401, detail="Could not validate credentials")