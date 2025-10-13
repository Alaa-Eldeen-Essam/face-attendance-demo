"""
SQLAlchemy models for the attendance system.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, LargeBinary, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Person(Base):
    """Known person with stored face embeddings."""
    __tablename__ = "persons"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    identifier = Column(String, unique=True, nullable=False, index=True)  # e.g., military ID
    image_data = Column(LargeBinary, nullable=False)  # Stored face photo
    embeddings = Column(LargeBinary, nullable=False)  # Numpy array as bytes
    created_at = Column(DateTime, nullable=False)
    deleted = Column(Boolean, default=False, nullable=False)


class Attendance(Base):
    """Attendance records for personnel."""
    __tablename__ = "attendance"
    
    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=False, index=True)
    name = Column(String, nullable=False)  # Denormalized for quick queries
    identifier = Column(String, nullable=False)  # Denormalized
    arrival_time = Column(DateTime, nullable=False, index=True)
    departure_time = Column(DateTime, nullable=True)
    auto = Column(Boolean, default=True, nullable=False)  # Auto-detected vs manual
    created_at = Column(DateTime, nullable=False)


class Unknown(Base):
    """Unknown faces detected for later review."""
    __tablename__ = "unknown_faces"
    
    id = Column(Integer, primary_key=True, index=True)
    image_data = Column(LargeBinary, nullable=False)
    embeddings = Column(LargeBinary, nullable=False)
    detected_at = Column(DateTime, nullable=False, index=True)