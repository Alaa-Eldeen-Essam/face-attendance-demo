"""
SQLAlchemy models for the attendance system.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, LargeBinary, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

Base = declarative_base()


class Person(Base):
    """Known person identity."""
    __tablename__ = "persons"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    identifier = Column(String, unique=True, nullable=False, index=True)  # e.g., military ID
    image_data = Column(LargeBinary, nullable=True)  # Primary display photo
    created_at = Column(DateTime, nullable=False)
    deleted = Column(Boolean, default=False, nullable=False)
    
    face_embeddings = relationship(
        "PersonEmbedding",
        back_populates="person",
        cascade="all, delete-orphan"
    )


class PersonEmbedding(Base):
    """One face embedding/photo sample for a person."""
    __tablename__ = "person_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=False, index=True)
    image_data = Column(LargeBinary, nullable=False)
    embedding = Column(Vector(512), nullable=False)
    source = Column(String, nullable=False, default="camera")
    quality_score = Column(Float, nullable=True)
    created_at = Column(DateTime, nullable=False)
    active = Column(Boolean, default=True, nullable=False)

    person = relationship("Person", back_populates="face_embeddings")


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
    embeddings = Column(Vector(512), nullable=False)
    detected_at = Column(DateTime, nullable=False, index=True)
