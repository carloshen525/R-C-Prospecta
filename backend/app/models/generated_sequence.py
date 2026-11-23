from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class GeneratedSequence(Base):
    __tablename__ = "generated_sequences"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    
    ai_provider_used = Column(String(50), nullable=False) # openai, groq, gemini
    ai_model_used = Column(String(100), nullable=True)
    raw_ai_response = Column(JSON, nullable=True)
    tokens_used = Column(Integer, default=0)
    is_approved = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    lead = relationship("Lead", back_populates="generated_sequences")
    campaign = relationship("Campaign", back_populates="generated_sequences")
    messages = relationship("Message", back_populates="sequence", cascade="all, delete-orphan")
