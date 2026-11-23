from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from app.database import Base

class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(150), unique=True, index=True, nullable=False)
    event_type = Column(String(100), nullable=False)
    source = Column(String(50), default="evolution", nullable=False)
    payload = Column(JSON, nullable=True)
    processed = Column(Boolean, default=True, nullable=False)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
