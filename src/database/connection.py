"""Database connection and session management."""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from contextlib import contextmanager
from typing import Generator
from dotenv import load_dotenv

from src.database.models import Base

# Load environment variables
load_dotenv()

# Database URL from environment
# Default to SQLite if PostgreSQL is not configured
DATABASE_URL = os.getenv('DATABASE_URL')

# If no DATABASE_URL is set, use SQLite
if not DATABASE_URL or DATABASE_URL == 'postgresql://postgres:postgres@localhost:5432/shadow_api_scanner':
    # Check if PostgreSQL is really available by trying a simple connection
    if DATABASE_URL and DATABASE_URL.startswith('postgresql'):
        try:
            import psycopg2
            # Try to connect
            conn = psycopg2.connect(DATABASE_URL)
            conn.close()
            print("[+] Using PostgreSQL database")
        except:
            # PostgreSQL not available, fall back to SQLite
            db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'scanner.db')
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            DATABASE_URL = f'sqlite:///{db_path}'
            print(f"[+] PostgreSQL not available, using SQLite: {db_path}")
    else:
        # Default to SQLite
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'scanner.db')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        DATABASE_URL = f'sqlite:///{db_path}'
        print(f"[+] Using SQLite database: {db_path}")

# Create engine
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,  # Use NullPool for simpler connection management
    echo=False,  # Set to True for SQL query logging
    future=True
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database - create all tables."""
    try:
        Base.metadata.create_all(bind=engine)
        print("[+] Database initialized successfully")
        return True
    except Exception as e:
        print(f"[!] Failed to initialize database: {e}")
        return False


def drop_db():
    """Drop all tables - USE WITH CAUTION."""
    try:
        Base.metadata.drop_all(bind=engine)
        print("[+] Database tables dropped")
        return True
    except Exception as e:
        print(f"[!] Failed to drop database tables: {e}")
        return False


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Get database session as context manager.

    Usage:
        with get_db() as db:
            # use db session
            pass
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def get_db_session() -> Session:
    """
    Get database session (must be closed manually).

    Usage:
        db = get_db_session()
        try:
            # use db
        finally:
            db.close()
    """
    return SessionLocal()


def test_connection() -> bool:
    """Test database connection."""
    try:
        with get_db() as db:
            db.execute(text("SELECT 1"))
        print("[+] Database connection successful")
        return True
    except Exception as e:
        print(f"[!] Database connection failed: {e}")
        return False
