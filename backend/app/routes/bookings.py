from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models.admin import Booking
from app.models.user import User
from app.routes.auth import get_current_user
from pydantic import BaseModel
from typing import Dict, Any, List
from beanie import PydanticObjectId
from datetime import datetime, timedelta

router = APIRouter(prefix="/bookings", tags=["Bookings"])
security = HTTPBearer()

async def get_user_from_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return await get_current_user(credentials.credentials)

class BookingRequest(BaseModel):
    type: str
    details: Dict[str, Any]
    price: int

@router.post("")
async def create_booking(req: BookingRequest, user: User = Depends(get_user_from_token)):
    new_booking = Booking(
        user_email=user.email,
        type=req.type,
        details=req.details,
        price=req.price
    )
    await new_booking.insert()
    return {"message": "Booking confirmed!", "booking": new_booking}

@router.get("/me")
async def get_my_bookings(user: User = Depends(get_user_from_token)):
    bookings = await Booking.find(Booking.user_email == user.email).to_list()
    return bookings

class CancelRequest(BaseModel):
    reason: str

@router.delete("/{booking_id}")
async def cancel_booking(booking_id: str, req: CancelRequest, user: User = Depends(get_user_from_token)):
    booking = await Booking.get(PydanticObjectId(booking_id))
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.user_email != user.email:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if booking.status == "cancelled":
        raise HTTPException(status_code=400, detail="Booking is already cancelled")
        
    time_diff = datetime.utcnow() - booking.created_at
    if time_diff > timedelta(hours=24):
        raise HTTPException(status_code=400, detail="Cannot cancel booking after 24 hours")
    
    booking.status = "cancelled"
    booking.cancel_reason = req.reason
    await booking.save()
    return {"message": "Booking cancelled"}
