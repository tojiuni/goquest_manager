# app/database/models.py
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Integer, BigInteger, Enum
import enum
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
    batch_id = Column(String, nullable=True)
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

class PlaneProject(Base):
    __tablename__ = "plane_projects"
    id = Column(String, primary_key=True) # Project UUID
    name = Column(String)
    slug = Column(String)
    workspace_id = Column(String, nullable=True)  # 선택적 필드로 변경

class BatchStatus(enum.Enum):
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class SyncBatch(Base):
    __tablename__ = "sync_batches"
    id = Column(String, primary_key=True) # UUID
    template_name = Column(String)
    status = Column(Enum(BatchStatus), default=BatchStatus.RUNNING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class CreatedResource(Base):
    __tablename__ = "created_resources"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    batch_id = Column(String, ForeignKey("sync_batches.id"))
    resource_type = Column(String) # PROJECT, CYCLE, MODULE, ISSUE
    plane_id = Column(String)      # Plane API에서 받은 UUID
    project_slug = Column(String)
    parent_id = Column(String, nullable=True) # 하위 이슈 연결용
    created_at = Column(DateTime(timezone=True), server_default=func.now())