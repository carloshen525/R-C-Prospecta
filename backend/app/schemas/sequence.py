from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class MessageItem(BaseModel):
    part: int = Field(..., ge=1, le=3)
    message: str = Field(..., min_length=5)

class AISequenceGeneratedOutput(BaseModel):
    messages: List[MessageItem]

class SequenceResponse(BaseModel):
    id: int
    campaign_id: int
    lead_id: int
    ai_provider_used: str
    ai_model_used: Optional[str]
    is_approved: bool
    created_at: datetime

    class Config:
        from_attributes = True
