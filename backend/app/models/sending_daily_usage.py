from datetime import datetime, date
from sqlalchemy import Column, Integer, Date, Boolean, DateTime
from app.database import Base

class SendingDailyUsage(Base):
    __tablename__ = "sending_daily_usage"

    id = Column(Integer, primary_key=True, index=True)
    usage_date = Column(Date, unique=True, index=True, nullable=False, default=date.today)
    contacts_sent_count = Column(Integer, default=0, nullable=False)
    limit_max = Column(Integer, default=30, nullable=False)
    is_limit_reached = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
