from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class LeadBase(BaseModel):
    company_name: str
    phone: Optional[str] = None
    raw_phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = "Brasil"
    website: Optional[str] = None
    category: Optional[str] = None
    segment: Optional[str] = None
    rating: Optional[float] = None
    rating_count: Optional[int] = None
    description: Optional[str] = None
    source: Optional[str] = "Manual"
    status: Optional[str] = "novo"
    is_eligible: Optional[bool] = True
    notes: Optional[str] = None

class LeadCreate(LeadBase):
    pass

class LeadUpdate(BaseModel):
    company_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    website: Optional[str] = None
    category: Optional[str] = None
    segment: Optional[str] = None
    status: Optional[str] = None
    is_eligible: Optional[bool] = None
    notes: Optional[str] = None

class LeadResponse(LeadBase):
    id: int
    user_id: Optional[int] = None
    website_analyzed_at: Optional[datetime] = None
    website_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class LeadListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    items: List[LeadResponse]

class LeadBulkAction(BaseModel):
    lead_ids: List[int]
    action: str  # add_to_campaign, change_status, block, delete
    campaign_id: Optional[int] = None
    status: Optional[str] = None

class LeadFilterParams(BaseModel):
    search: Optional[str] = None
    segment: Optional[str] = None
    city: Optional[str] = None
    campaign_id: Optional[int] = None
    status: Optional[str] = None
    has_phone: Optional[bool] = None
    has_website: Optional[bool] = None
    is_eligible: Optional[bool] = None
    skip: int = 0
    limit: int = 50
