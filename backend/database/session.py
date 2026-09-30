from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.config import settings

# Configure engine depending on database dialect (SQLite requires check_same_thread=False)
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency that yields a database session per request and closes it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
