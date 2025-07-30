from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import os

# PostgreSQL connection URL format
# postgresql://username:password@host:port/database_name
DB_URL = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost:5432/your_db')
engine = create_engine(DB_URL)

class Base(DeclarativeBase):
    pass

class Request(Base):
    __tablename__ = "requests"

    # Use PostgreSQL UUID type for better performance
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    modified_at = Column(DateTime(timezone=True), onupdate=func.now())
    package = Column(String(100))
    status = Column(String(30))
    username = Column(String(40))
    hostname = Column(String(60))
    ip = Column(String(15))
    
SessionLocal = sessionmaker(autoflush=False, bind=engine)