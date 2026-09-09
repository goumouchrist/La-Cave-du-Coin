from sqlalchemy.orm import Session

from app.models import User
from app.security import hash_password, verify_password


class DuplicateUsernameError(Exception):
    pass


def create_user(db: Session, username: str, password: str, role, full_name: str = "") -> User:
    if db.query(User).filter(User.username == username).first():
        raise DuplicateUsernameError(f"Le nom d'utilisateur '{username}' existe déjà")

    user = User(username=username, password_hash=hash_password(password), role=role, full_name=full_name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, username: str, password: str) -> User | None:
    user = db.query(User).filter(User.username == username, User.is_active.is_(True)).first()
    if not user or not verify_password(password, user.password_hash):
        return None
    return user
