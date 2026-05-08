"""
Database configuration and session management.
"""
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models import Base, Person, PersonEmbedding, Attendance, Unknown

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
            legacy_embeddings = conn.execute(text(
                "SELECT 1 FROM information_schema.columns "
                "WHERE table_schema = 'public' "
                "AND table_name = 'persons' "
                "AND column_name = 'embeddings'"
            )).first()
            has_person_embeddings = conn.execute(text(
                "SELECT 1 FROM information_schema.tables "
                "WHERE table_schema = 'public' "
                "AND table_name = 'person_embeddings'"
            )).first()
            embedding_columns = {
                row[0]
                for row in conn.execute(text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_schema = 'public' "
                    "AND table_name = 'person_embeddings'"
                ))
            }
            expected_embedding_columns = {
                "id",
                "person_id",
                "image_data",
                "embedding",
                "source",
                "quality_score",
                "created_at",
                "active",
            }
            if legacy_embeddings and not has_person_embeddings:
                Base.metadata.drop_all(bind=conn)
            elif embedding_columns and embedding_columns != expected_embedding_columns:
                Base.metadata.drop_all(bind=conn)

    if os.getenv("RESET_DATABASE_ON_START", "false").lower() in {"1", "true", "yes"}:
        Base.metadata.drop_all(bind=engine)

    Base.metadata.create_all(bind=engine)

    if engine.dialect.name == "postgresql":
        with engine.begin() as conn:
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS person_embeddings_embedding_hnsw_idx "
                "ON person_embeddings USING hnsw (embedding vector_cosine_ops)"
            ))
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS unknown_faces_embeddings_hnsw_idx "
                "ON unknown_faces USING hnsw (embeddings vector_cosine_ops)"
            ))
