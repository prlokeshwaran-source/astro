from datetime import datetime
from typing import NotRequired, TypedDict

class PaymentDocument(TypedDict):
    _id: str
    consultation_id: str
    user_id: str
    amount: float
    currency: str
    provider: str
    status: str
    created_at: datetime
    provider_reference: NotRequired[str | None]
