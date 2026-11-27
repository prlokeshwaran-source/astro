from datetime import datetime
from typing import NotRequired, TypedDict

class MessageDocument(TypedDict):
    _id: str
    consultation_id: str
    sender_id: str
    content: str
    created_at: datetime
    read_at: NotRequired[datetime | None]
    attachment: NotRequired[dict]
