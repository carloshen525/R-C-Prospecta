from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    sequence_id = Column(Integer, ForeignKey("generated_sequences.id"), nullable=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    
    part_number = Column(Integer, nullable=False) # 1, 2, 3
    original_content = Column(Text, nullable=False)
    final_content = Column(Text, nullable=False)
    
    # Status: pendente, na_fila, enviado, entregue, lido, falhou, cancelado
    status = Column(String(50), default="pendente", index=True, nullable=False)
    
    scheduled_for = Column(DateTime, nullable=True, index=True)
    sent_at = Column(DateTime, nullable=True, index=True)
    evolution_message_id = Column(String(100), nullable=True, index=True)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    sequence = relationship("GeneratedSequence", back_populates="messages")
    campaign = relationship("Campaign", back_populates="messages")
    lead = relationship("Lead", back_populates="messages")

    __table_args__ = (
        Index("ix_messages_status_scheduled", "status", "scheduled_for"),
    )
