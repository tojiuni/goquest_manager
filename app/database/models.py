# app/database/models.py
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Integer
from sqlalchemy.orm import relationship
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

class PlaneMember(Base):
    __tablename__ = "plane_members"
    id = Column(String, primary_key=True) # Plane의 User UUID
    email = Column(String, index=True)
    display_name = Column(String)

class PlaneState(Base):
    __tablename__ = "plane_states"
    id = Column(String, primary_key=True) # State UUID
    project_id = Column(String, index=True)
    name = Column(String) # 예: Todo, In Progress
    group = Column(String) # 예: backlog, unstarted, started, completed