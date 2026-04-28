from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models import Base


engine = create_engine(
	settings.database_url,
	pool_pre_ping=True,
	pool_recycle=1800,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine)


def get_db() -> Generator:
	db = SessionLocal()
	try:
		yield db
	except Exception:
		db.rollback()
		raise
	finally:
		db.close()


def init_db() -> None:
	Base.metadata.create_all(bind=engine)
