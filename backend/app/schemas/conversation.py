from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class ConversationEventCreate(BaseModel):
    message_content: str

class ConversationEventResponse(BaseModel):
    id: int
    conversation_id: int
    direction: str
    message_content: str
    evolution_message_id: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class ConversationStatusUpdate(BaseModel):
    status: str # aberta, interessado, sem_interesse, finalizada

class ConversationResponse(BaseModel):
    id: int
    lead_id: int
    company_name: Optional[str] = None
    phone: str
    status: str
    last_message_at: datetime
    unread_count: int
    created_at: datetime
    updated_at: datetime
    events: Optional[List[ConversationEventResponse]] = []

    class Config:
        from_attributes = True
