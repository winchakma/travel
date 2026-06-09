from fastapi import APIRouter, HTTPException, Depends
from app.models.user import User
from app.models.admin import Activity, Order
from app.routes.profile import get_current_user
from datetime import datetime
import stripe
import os
router = APIRouter(prefix="/store", tags=["Store"])

@router.post("/checkout")
async def store_checkout(data: dict, current_user: User = Depends(get_current_user)):
    # Create Order
    new_order = Order(
        userId=str(current_user.id),
        userEmail=current_user.email,
        userName=data.get("name") or f"{current_user.firstName} {current_user.lastName}",
        phone=data.get("phone", ""),
        address=data.get("address", ""),
        items=data.get("items_summary", "Neural Gear Bundle"),
        total=float(data.get("total", 0)),
        paymentMethod=data.get("payment_method", "Unknown"),
        status="Processing"
    )
    await new_order.insert()
    
    # Log Activity
    await Activity(
        userId=str(current_user.id),
        userEmail=current_user.email,
        action="Shop Purchase",
        details=f"Ordered: {new_order.items} - Total: ${new_order.total}"
    ).insert()
    
    # Reward Points
    points_earned = int(new_order.total // 10) + 50
    current_user.points = getattr(current_user, "points", 0) + points_earned
    await current_user.save()
    
    payment_method = data.get("payment_method", "Unknown")
    origin_url = data.get("origin", "http://localhost:3000")

    if payment_method == "card":
        try:
            stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': data.get("items_summary", "Elite Gear"),
                        },
                        'unit_amount': int(float(data.get("total", 0)) * 100),
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=origin_url + '/dashboard.html?payment=success',
                cancel_url=origin_url + '/checkout.html?payment=cancelled',
                metadata={
                    'order_id': str(new_order.id),
                    'user_id': str(current_user.id)
                }
            )
            return {
                "status": "stripe_redirect", 
                "url": session.url
            }
        except Exception as e:
            return {"status": "error", "detail": str(e)}

    return {
        "status": "success", 
        "order_id": str(new_order.id), 
        "points_earned": points_earned,
        "user": current_user
    }
