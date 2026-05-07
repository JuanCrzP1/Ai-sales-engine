from sqlalchemy import create_engine

_engine = None


def get_engine():
    global _engine
    if _engine is None:
        from app.config import settings
        _engine = create_engine(settings.database_url)
    return _engine