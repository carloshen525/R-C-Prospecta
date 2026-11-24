from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings
import socket
import logging
from urllib.parse import urlparse

logger = logging.getLogger("prospect_ai")

def get_engine():
    if not settings.DATABASE_URL.startswith("sqlite"):
        try:
            pg_engine = create_engine(
                settings.DATABASE_URL,
                pool_pre_ping=True,
                pool_recycle=60,
                connect_args={
                    "keepalives": 1,
                    "keepalives_idle": 15,
                    "keepalives_interval": 5,
                    "keepalives_count": 5
                }
            )
            with pg_engine.connect() as conn:
                pass
            logger.info("Conectado com sucesso ao PostgreSQL!")
            return pg_engine
        except Exception as e:
            logger.warning(f"PostgreSQL não acessível com as credenciais ({e}). Utilizando SQLite local (prospect_ai.db).")
    
    sqlite_url = "sqlite:///./prospect_ai.db"
    return create_engine(
        sqlite_url,
        connect_args={"check_same_thread": False}
    )

engine = get_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


