"""Database access for the User model. No business logic here."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


def get_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def username_exists(db: Session, username: str) -> bool:
    return db.scalar(select(User.id).where(User.username == username)) is not None


def create(db: Session, **fields) -> User:
    user = User(**fields)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
