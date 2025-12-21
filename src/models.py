import enum
from sqlalchemy import (
    create_engine,
    Column,
    String,
    TIMESTAMP,
    BigInteger,
    ForeignKey,
    Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.sql import func
import uuid

from src.config import get_settings

DATABASE_URL = get_settings().DATABASE_URL
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class SyncStatus(enum.Enum):
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PARTIAL_DELETED = "PARTIAL_DELETED"
    DELETED = "DELETED"


class ResourceType(enum.Enum):
    PROJECT = "PROJECT"
    CYCLE = "CYCLE"
    MODULE = "MODULE"
    ISSUE = "ISSUE"


class SyncBatch(Base):
    __tablename__ = "sync_batches"

    id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    template_name = Column(String, nullable=False)
    status = Column(SAEnum(SyncStatus), nullable=False, default=SyncStatus.RUNNING)
    created_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    resources = relationship("CreatedResource", back_populates="batch")


class CreatedResource(Base):
    __tablename__ = "created_resources"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    batch_id = Column(
        UUID(as_uuid=True), ForeignKey("sync_batches.id"), nullable=False, index=True
    )
    resource_type = Column(SAEnum(ResourceType), nullable=False)
    plane_id = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)
    project_slug = Column(String, nullable=True)  # Projects won't have this
    parent_id = Column(UUID(as_uuid=True), nullable=True)  # For sub-issues
    created_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    batch = relationship("SyncBatch", back_populates="resources")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)