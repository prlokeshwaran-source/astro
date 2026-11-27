from datetime import datetime
from typing import TypedDict

class ReviewDocument(TypedDict):
    _id: str
    consultation_id: str
    user_id: str
    astrologer_id: str
    rating: int
    comment: str
    created_at: datetime
