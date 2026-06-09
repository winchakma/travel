from datetime import datetime, timedelta
from app.models.admin import Booking

def is_booking_expired(b: Booking) -> bool:
    if not b.time:
        return (datetime.utcnow() - b.date).days > 7
    
    parts = b.time.split()
    if not parts:
        return (datetime.utcnow() - b.date).days > 7
        
    days_map = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
    day_str = parts[0].lower()[:3]
    
    if day_str not in days_map:
        return (datetime.utcnow() - b.date).days > 7
        
    day_idx = days_map[day_str]
    booked_at = b.date
    days_ahead = day_idx - booked_at.weekday()
    
    if days_ahead < 0:
        days_ahead += 7
        
    # default fallback time if parsing fails
    dt_time = datetime.strptime("23:59", "%H:%M").time()
    try:
        time_str = " ".join(parts[1:])
        if "am" in time_str.lower() or "pm" in time_str.lower():
            dt_time = datetime.strptime(time_str.strip(), "%I:%M %p").time()
        else:
            if ":" not in time_str: time_str += ":00"
            dt_time = datetime.strptime(time_str.strip(), "%H:%M").time()
            
        class_dt = booked_at.replace(hour=dt_time.hour, minute=dt_time.minute, second=0, microsecond=0)
        if days_ahead == 0 and class_dt < booked_at:
            days_ahead += 7
    except Exception:
        pass
        
    class_datetime = datetime.combine(booked_at.date() + timedelta(days=days_ahead), dt_time)
    
    # It expires immediately after the exact class time passes (e.g. 7:01 AM)
    return datetime.utcnow() > class_datetime
