from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models.admin import Booking
from app.models.user import User
from app.routes.auth import get_current_user
from pydantic import BaseModel
from typing import Dict, Any, List
from beanie import PydanticObjectId
from datetime import datetime, timedelta
import stripe
import os
from fastapi import Request

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

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
        price=req.price,
        status="confirmed"
    )
    await new_booking.insert()
    return {"message": "Booking confirmed!", "booking": new_booking}

@router.post("/create-checkout-session")
async def create_checkout_session(req: BookingRequest, user: User = Depends(get_user_from_token), request: Request = None):
    # 1. Create a pending booking in the database
    new_booking = Booking(
        user_email=user.email,
        type=req.type,
        details=req.details,
        price=req.price,
        status="pending"
    )
    await new_booking.insert()

    # Determine base URL for redirect
    # In production, this should be your frontend URL
    # We can default to the referer or an env variable
    origin = request.headers.get("origin", "https://travel-xyyl.onrender.com")

    # 2. Create Stripe Checkout Session
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f"{req.type.capitalize()} Booking: {req.details.get('name', 'Package')}",
                        'description': str(req.details.get('destination') or req.details.get('from') or 'Travel Booking'),
                    },
                    'unit_amount': int(req.price * 100), # Stripe uses cents
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f"{origin}/success.html?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{origin}/cancel.html",
            client_reference_id=str(new_booking.id),
            metadata={
                "booking_id": str(new_booking.id),
                "user_email": user.email
            }
        )
        return {"sessionId": session.id, "booking_id": str(new_booking.id)}
    except Exception as e:
        # Revert booking if Stripe fails
        await new_booking.delete()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    # Optional: verify webhook signature if STRIPE_WEBHOOK_SECRET is set
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    
    event = None
    try:
        if webhook_secret:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        else:
            # For testing without signature verification
            import json
            event = stripe.Event.construct_from(json.loads(payload), stripe.api_key)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        booking_id = session.get("client_reference_id")
        
        if booking_id:
            booking = await Booking.get(PydanticObjectId(booking_id))
            if booking:
                booking.status = "confirmed"
                await booking.save()

    return {"status": "success"}

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
