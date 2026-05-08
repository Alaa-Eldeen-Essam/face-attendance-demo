"""
Database configuration and session management.
"""
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models import Base, Person, Attendance, Unknown

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://attendance:attendance@localhost:5433/attendance_demo",
)

engine_kwargs = {"pool_pre_ping": True}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables."""
    if engine.dialect.name == "postgresql":
        with engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

    if os.getenv("RESET_DATABASE_ON_START", "false").lower() in {"1", "true", "yes"}:
        Base.metadata.drop_all(bind=engine)

    Base.metadata.create_all(bind=engine)

    if engine.dialect.name == "postgresql":
        with engine.begin() as conn:
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS persons_embeddings_hnsw_idx "
                "ON persons USING hnsw (embeddings vector_cosine_ops)"
            ))
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS unknown_faces_embeddings_hnsw_idx "
                "ON unknown_faces USING hnsw (embeddings vector_cosine_ops)"
            ))
