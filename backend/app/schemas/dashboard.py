from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class DashboardIndicators(BaseModel):
    total_leads: int
    leads_extracted: int
    leads_available: int
    contacts_sent_today: int
    daily_limit: int
    remaining_today: int
    total_messages_sent: int
    total_replies: int
    total_interested: int
    active_campaigns: int
    is_window_open: bool
    window_status_message: str

class DayMetrics(BaseModel):
    date: str
    sent: int
    replies: int

class SegmentDistribution(BaseModel):
    segment: str
    count: int

class ActivityItem(BaseModel):
    id: str
    type: str # extraction, message_sent, reply_received, campaign_status, error
    title: str
    description: str
    timestamp: str

class DashboardResponse(BaseModel):
    indicators: DashboardIndicators
    chart_daily_activity: List[DayMetrics]
    chart_segments: List[SegmentDistribution]
    recent_activities: List[ActivityItem]
