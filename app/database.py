import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://tim@localhost/medimesh")
POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "10"))
MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "20"))

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
    pool_timeout=30,
    pool_recycle=3600,
    echo=bool(os.getenv("DB_ECHO", False))
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_connection():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        return True
    except SQLAlchemyError as e:
        logger.error(f"Database connection failed: {e}")
        return False

def create_tables():
    """Create all tables defined in models"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except SQLAlchemyError as e:
        logger.error(f"Failed to create tables: {e}")
        raise

def health_check():
    """Database health check"""
    health = {
        "database": "unknown",
        "connection": False,
        "tables_exist": False,
        "error": None
    }

    try:
        health["connection"] = test_connection()
        inspector = engine.inspect()
        tables = inspector.get_table_names()
        expected_tables = ["patients", "doctors", "beds", "appointments", "staff"]
        health["tables_exist"] = all(table in tables for table in expected_tables)
        health["database"] = "healthy" if health["connection"] and health["tables_exist"] else "unhealthy"
    except Exception as e:
        health["error"] = str(e)
        health["database"] = "error"
        logger.error(f"Health check failed: {e}")

    return health
