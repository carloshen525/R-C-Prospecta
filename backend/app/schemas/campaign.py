from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class CampaignBase(BaseModel):
    name: str = Field(..., max_length=150)
    description: Optional[str] = None
    segment: Optional[str] = None
    location: Optional[str] = None
    ai_provider: str = "gemini"
    ai_model: str = "gemini-1.5-flash"
    custom_prompt: Optional[str] = None
    daily_limit: int = Field(default=30, ge=1, le=30)
    interval_min_seconds: int = Field(default=180, ge=60)
    interval_max_seconds: int = Field(default=360, ge=120)
    followup_1_delay_hours: int = Field(default=24, ge=1)
    followup_2_delay_hours: int = Field(default=48, ge=1)

class CampaignCreate(CampaignBase):
    lead_ids: Optional[List[int]] = []

class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    segment: Optional[str] = None
    location: Optional[str] = None
    ai_provider: Optional[str] = None
    ai_model: Optional[str] = None
    custom_prompt: Optional[str] = None
    daily_limit: Optional[int] = None
    interval_min_seconds: Optional[int] = None
    interval_max_seconds: Optional[int] = None
    followup_1_delay_hours: Optional[int] = None
    followup_2_delay_hours: Optional[int] = None
    status: Optional[str] = None

class CampaignResponse(CampaignBase):
    id: int
    user_id: Optional[int]
    status: str
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    total_leads: Optional[int] = 0
    leads_processed: Optional[int] = 0
    messages_generated: Optional[int] = 0
    contacts_sent: Optional[int] = 0
    responses_count: Optional[int] = 0
    interested_count: Optional[int] = 0

    class Config:
        from_attributes = True

class CampaignActionRequest(BaseModel):
    action: str # start, pause, resume, stop
