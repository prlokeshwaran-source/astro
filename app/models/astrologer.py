from typing import NotRequired, TypedDict

class AstrologerDocument(TypedDict):
    _id: str
    user_id: str
    experience: int
    specialization: list[str]
    languages: list[str]
    consultation_price: float
    bio: str
    approval_status: str
    is_online: bool
    rating_total: NotRequired[int]
    review_count: NotRequired[int]
    availability: NotRequired[dict]
