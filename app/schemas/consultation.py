from datetime import datetime
from pydantic import BaseModel, Field
class ConsultationCreate(BaseModel):
    astrologer_id: str
    consultation_type: str
    scheduled_at: datetime
    duration_minutes: int = Field(default=30, ge=5, le=240)
class ConsultationStatusUpdate(BaseModel):
    status: str
    notes: str | None = None
