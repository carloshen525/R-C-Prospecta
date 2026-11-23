from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), unique=True, nullable=False, index=True)
    phone = Column(String(50), nullable=False, index=True)
    
    # Status: aberta, interessado, sem_interesse, finalizada
    status = Column(String(50), default="aberta", index=True, nullable=False)
    last_message_at = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    unread_count = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    lead = relationship("Lead", back_populates="conversation")
    events = relationship("ConversationEvent", back_populates="conversation", cascade="all, delete-orphan", order_by="ConversationEvent.created_at")

class ConversationEvent(Base):
    __tablename__ = "conversation_events"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    
    # Direction: incoming, outgoing
    direction = Column(String(20), nullable=False, index=True)
    message_content = Column(Text, nullable=False)
    evolution_message_id = Column(String(100), nullable=True, index=True)
    raw_payload = Column(JSON, nullable=True)
    status = Column(String(50), default="sent", nullable=False) # sent, delivered, read, received

    created_at = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)

    conversation = relationship("Conversation", back_populates="events")
