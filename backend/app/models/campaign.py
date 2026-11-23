from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    name = Column(String(150), nullable=False, index=True)
    description = Column(Text, nullable=True)
    segment = Column(String(150), nullable=True, index=True)
    location = Column(String(150), nullable=True)
    
    # IA Configuration
    ai_provider = Column(String(50), default="gemini", nullable=False) # openai, groq, gemini
    ai_model = Column(String(100), default="gemini-1.5-flash", nullable=False)
    custom_prompt = Column(Text, nullable=True)

    # Sending rules per campaign
    daily_limit = Column(Integer, default=30, nullable=False)
    interval_min_seconds = Column(Integer, default=180, nullable=False)
    interval_max_seconds = Column(Integer, default=360, nullable=False)
    followup_1_delay_hours = Column(Integer, default=24, nullable=False)
    followup_2_delay_hours = Column(Integer, default=48, nullable=False)

    # Status: rascunho, preparando, aguardando_inicio, ativa, pausada, concluida, erro
    status = Column(String(50), default="rascunho", index=True, nullable=False)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    campaign_leads = relationship("CampaignLead", back_populates="campaign", cascade="all, delete-orphan")
    extraction_jobs = relationship("ExtractionJob", back_populates="campaign")
    generated_sequences = relationship("GeneratedSequence", back_populates="campaign")
    messages = relationship("Message", back_populates="campaign")
