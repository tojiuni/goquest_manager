# app/database/models.py
from sqlalchemy import Column, String, DateTime, JSON, UUID, Integer
from sqlalchemy.sql import func
from .session import Base
import uuid

class LogTable(Base):
    __tablename__ = "operation_logs"
    id = Column(Integer, primary_key=True, index=True)
    level = Column(String)  # INFO, ERROR, DEBUG
    step = Column(String)   # CONNECTION, CREATE, DELETE
    message = Column(String)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())