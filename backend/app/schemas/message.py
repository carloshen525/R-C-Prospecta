from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class MessageUpdate(BaseModel):
    final_content: str

class MessageResponse(BaseModel):
    id: int
    sequence_id: Optional[int]
    campaign_id: int
    lead_id: int
    part_number: int
    original_content: str
    final_content: str
    status: str
    scheduled_for: Optional[datetime]
    sent_at: Optional[datetime]
    evolution_message_id: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
