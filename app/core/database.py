from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool

from app.core.config import settings

engine = create_engine(
    settings["DATABASE_URL"],
    poolclass=QueuePool,
    pool_size=10,         
    max_overflow=20,      
    pool_pre_ping=True,   
    pool_recycle=1800,    
    echo=False            
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


Base = declarative_base()

def get_db():
    """
    FastAPI dependency that provides a SQLAlchemy session
    and ensures proper cleanup.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()