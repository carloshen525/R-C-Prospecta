from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class ExtractionJob(Base):
    __tablename__ = "extraction_jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    segment = Column(String(150), nullable=False, index=True)
    city = Column(String(100), nullable=False, index=True)
    state = Column(String(50), nullable=False)
    country = Column(String(50), default="Brasil", nullable=False)
    desired_qty = Column(Integer, default=50, nullable=False)
    has_phone_filter = Column(Boolean, default=True)
    has_website_filter = Column(Boolean, default=False)
    source = Column(String(50), default="google_scraper", nullable=True)
    auto_import = Column(Boolean, default=False, nullable=False)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True)
    
    # Status: pending, running, completed, failed
    status = Column(String(50), default="pending", index=True, nullable=False)
    found_count = Column(Integer, default=0)
    processed_count = Column(Integer, default=0)
    saved_count = Column(Integer, default=0)
    duplicate_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    execution_time_seconds = Column(Float, default=0.0)
    error_log = Column(Text, nullable=True)
    extracted_items = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    campaign = relationship("Campaign", back_populates="extraction_jobs")
