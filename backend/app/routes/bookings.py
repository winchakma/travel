from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models.admin import Booking
from app.models.user import User
from app.routes.auth import get_current_user
from pydantic import BaseModel
from typing import Dict, Any, List
from beanie import PydanticObjectId

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

@router.delete("/{booking_id}")
async def cancel_booking(booking_id: str, user: User = Depends(get_user_from_token)):
    booking = await Booking.get(PydanticObjectId(booking_id))
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.user_email != user.email:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    booking.status = "cancelled"
    await booking.save()
    return {"message": "Booking cancelled"}
