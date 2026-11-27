from datetime import datetime
from typing import NotRequired, TypedDict

class NotificationDocument(TypedDict):
    _id: str
    user_id: str
    title: str
    body: str
    created_at: datetime
    read_at: NotRequired[datetime | None]
    data: NotRequired[dict]
