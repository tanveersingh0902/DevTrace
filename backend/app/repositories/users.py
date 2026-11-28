from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User


def find_by_email(session: Session, email: str) -> User | None:
    return session.scalar(select(User).where(User.email == email))


def create_user(
    session: Session, *, email: str, password_hash: str, display_name: str
) -> User:
    user = User(email=email, password_hash=password_hash, display_name=display_name)
    session.add(user)
    session.flush()
    return user
