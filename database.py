import os
from sqlalchemy import create_engine, Column, String, DateTime, ForeignKey, BigInteger, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import uuid
from dotenv import load_dotenv

load_dotenv()

db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT', '5432')
db_name = os.getenv('DB_NAME')

DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class SyncBatch(Base):
    __tablename__ = "sync_batches"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    template_name = Column(String)
    workspace_slug = Column(String)
    status = Column(String, default="RUNNING") # RUNNING, COMPLETED, FAILED, DELETED
    created_at = Column(DateTime, default=datetime.utcnow)

class CreatedResource(Base):
    __tablename__ = "created_resources"
    id = Column(BigInteger, primary_key=True, index=True)
    batch_id = Column(String, ForeignKey("sync_batches.id"))
    resource_type = Column(String) # PROJECT, ISSUE, CYCLE, MODULE
    plane_id = Column(String)      # Plane API에서 제공하는 UUID
    project_slug = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)