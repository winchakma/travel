from beanie import Document
from datetime import datetime
from pydantic import Field
from typing import Optional

class Review(Document):
    userName: str
    location: str
    avatarUrl: str
    quote: str
    rating: float = 5.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "public_reviews"

class Transformation(Document):
    userName: str
    badge: str
    avatarUrl: str
    quote: str
    beforeImgUrl: str
    afterImgUrl: str
    stat1Value: str
    stat1Label: str
    stat2Value: str
    stat2Label: str
    orderIdx: int = 0
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "public_transformations"
