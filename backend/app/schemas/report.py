from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class PerformanceByCampaign(BaseModel):
    campaign_name: str
    leads_count: int
    sent_count: int
    reply_count: int
    reply_rate: float
    interested_count: int
    interested_rate: float

class PerformanceBySegment(BaseModel):
    segment: str
    leads_count: int
    sent_count: int
    reply_count: int
    reply_rate: float

class PerformanceByAIProvider(BaseModel):
    ai_provider: str
    sequences_generated: int
    reply_count: int
    reply_rate: float

class ReportsSummary(BaseModel):
    total_extracted: int
    total_eligible: int
    total_contacts_sent: int
    total_messages: int
    total_responses: int
    total_interested: int
    response_rate: float
    interest_rate: float
    total_errors: int
    campaigns: List[PerformanceByCampaign]
    segments: List[PerformanceBySegment]
    ai_providers: List[PerformanceByAIProvider]
