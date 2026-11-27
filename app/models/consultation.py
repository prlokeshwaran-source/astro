from datetime import datetime
from typing import NotRequired, TypedDict

class ConsultationDocument(TypedDict):
    _id: str
    user_id: str
    astrologer_id: str
    consultation_type: str
    scheduled_at: datetime
    duration_minutes: int
    status: str
    payment_status: str
    astrologer_notes: NotRequired[str]
