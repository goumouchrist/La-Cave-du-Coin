from sqlalchemy.orm import Session

from app.models import User
from app.security import hash_password, verify_password


class DuplicateUsernameError(Exception):
    pass


class WrongCurrentPasswordError(Exception):
    pass


class CannotDeactivateSelfError(Exception):
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


def reset_password(db: Session, user: User, new_password: str) -> User:
    """Réinitialisation par un Admin, sans connaître l'ancien mot de passe."""
    user.password_hash = hash_password(new_password)
    db.commit()
    db.refresh(user)
    return user


def change_own_password(db: Session, user: User, current_password: str, new_password: str) -> User:
    """Changement par l'utilisateur lui-même : exige l'ancien mot de passe."""
    if not verify_password(current_password, user.password_hash):
        raise WrongCurrentPasswordError("Mot de passe actuel incorrect")
    user.password_hash = hash_password(new_password)
    db.commit()
    db.refresh(user)
    return user


def set_active(db: Session, user: User, current_user: User, is_active: bool) -> User:
    """Active/désactive un compte (équivalent d'une suppression, sans jamais
    supprimer l'utilisateur : ses ventes, mouvements et logs doivent rester
    consultables pour la traçabilité)."""
    if user.id == current_user.id and not is_active:
        raise CannotDeactivateSelfError("Vous ne pouvez pas désactiver votre propre compte")
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user
