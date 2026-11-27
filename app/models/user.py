from datetime import datetime
from typing import NotRequired, TypedDict

class UserDocument(TypedDict):
    _id: str
    name: str
    email: str
    mobile: str
    password_hash: str
    role: str
    is_active: bool
    created_at: datetime
    date_of_birth: NotRequired[str]
    time_of_birth: NotRequired[str]
    place_of_birth: NotRequired[str]
    profile_photo: NotRequired[str]
    preferred_language: NotRequired[str]
