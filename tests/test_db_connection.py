from sqlalchemy import text

from app.infrastructure.db.connection import get_engine


def test_db_connection():
    engine = get_engine()

    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.fetchone()[0] == 1