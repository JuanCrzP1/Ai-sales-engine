from sqlalchemy import create_engine
import os

_engine = None


def get_engine():
    global _engine
    if _engine is None:
        db_url = os.getenv("DATABASE_URL")

        if not db_url:
            db_url = "sqlite:///:memory:"

        _engine = create_engine(db_url)

    return _engine