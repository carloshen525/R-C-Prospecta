from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    company_name = Column(String(255), nullable=False, index=True)
    phone = Column(String(50), nullable=True, index=True) # Normalized E.164
    raw_phone = Column(String(50), nullable=True)
    address = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True, index=True)
    state = Column(String(50), nullable=True, index=True)
    country = Column(String(50), default="Brasil", nullable=False)
    website = Column(String(255), nullable=True)
    category = Column(String(150), nullable=True)
    segment = Column(String(150), nullable=True, index=True)
    rating = Column(Float, nullable=True)
    rating_count = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    source = Column(String(50), default="Google Maps", nullable=False)

    # Status: novo, aguardando_processamento, mensagens_geradas, na_fila, contatado, respondeu, interessado, sem_interesse, nao_contatar, erro
    status = Column(String(50), default="novo", index=True, nullable=False)
    is_eligible = Column(Boolean, default=True, index=True, nullable=False)
    notes = Column(Text, nullable=True)

    website_analyzed_at = Column(DateTime, nullable=True)
    website_data = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    campaign_associations = relationship("CampaignLead", back_populates="lead", cascade="all, delete-orphan")
    generated_sequences = relationship("GeneratedSequence", back_populates="lead", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="lead", cascade="all, delete-orphan")
    conversation = relationship("Conversation", back_populates="lead", uselist=False, cascade="all, delete-orphan")
