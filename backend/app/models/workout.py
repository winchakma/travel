from beanie import Document
from datetime import datetime, timezone
from typing import Optional

from pydantic import Field

def get_utc_now():
    return datetime.now(timezone.utc)

class Workout(Document):
    exercise: str
    calories: int
    formScore: int
    videoUrl: Optional[str] = None
    text_proof: Optional[str] = None
    user_id: str
    date: datetime = Field(default_factory=get_utc_now)

    class Settings:
        name = "workouts"
