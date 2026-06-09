from beanie import Document
from datetime import datetime

class WeightProgress(Document):
    userEmail: str
    weight: float
    timestamp: datetime = datetime.utcnow()

    class Settings:
        name = "weight_progress"
