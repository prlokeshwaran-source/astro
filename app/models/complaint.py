from typing import NotRequired, TypedDict

class ComplaintDocument(TypedDict):
    _id: str
    reporter_id: str
    role: str
    subject: str
    description: str
    status: str
    consultation_id: NotRequired[str | None]
    resolution_notes: NotRequired[str | None]
