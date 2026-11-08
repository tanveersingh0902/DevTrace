from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings, get_settings


class Database:
    """Lazy SQLAlchemy engine and session factory; migrations own schema creation."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._engine: Engine | None = None
        self._session_factory: sessionmaker[Session] | None = None

    @property
    def engine(self) -> Engine:
        if self._engine is None:
            self._engine = create_engine(
                self._settings.database_url,
                pool_pre_ping=True,
                pool_recycle=1800,
                pool_size=self._settings.database_pool_size,
                max_overflow=self._settings.database_max_overflow,
            )
        return self._engine

    @property
    def session_factory(self) -> sessionmaker[Session]:
        if self._session_factory is None:
            self._session_factory = sessionmaker(bind=self.engine, autoflush=False, expire_on_commit=False)
        return self._session_factory

    def session(self) -> Generator[Session, None, None]:
        with self.session_factory() as session:
            yield session

    def check_connection(self) -> bool:
        try:
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return True
        except SQLAlchemyError:
            return False

    def dispose(self) -> None:
        if self._engine is not None:
            self._engine.dispose()


database = Database(get_settings())


def get_database() -> Database:
    return database


def get_db() -> Generator[Session, None, None]:
    yield from database.session()
