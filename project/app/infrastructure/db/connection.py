from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()

_engine = None

def get_engine():
    global _engine
    if _engine is None:
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            raise RuntimeError("DATABASE_URL no definida")
        if not str(db_url).strip().lower().startswith("postgresql+psycopg"):
            raise RuntimeError("DATABASE_URL debe apuntar a PostgreSQL con psycopg")
        _engine = create_engine(db_url)
    return _engine