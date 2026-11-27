from datetime import datetime
from typing import NotRequired, TypedDict

class ReportDocument(TypedDict):
    _id: str
    consultation_id: str
    user_id: str
    astrologer_id: str
    title: str
    content: dict
    created_at: datetime
    pdf_url: NotRequired[str | None]
    status: NotRequired[str]
    shared_at: NotRequired[datetime]
