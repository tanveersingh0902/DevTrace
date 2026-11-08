from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative metadata target for future migrations and models."""
