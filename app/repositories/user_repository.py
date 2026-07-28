"""
Data access for User. No business rules, no transaction control — callers
(services) own flush()/commit() so multi-entity operations can share one
transaction.
"""

from sqlalchemy.orm import Session

from app.models.user import User


def get_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def list_all(db: Session) -> list[User]:
    return db.query(User).all()


def add(db: Session, user: User) -> User:
    db.add(user)
    db.flush()
    return user


def delete(db: Session, user: User) -> None:
    db.delete(user)
