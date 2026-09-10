from sqlalchemy.orm import Session

from app.models import Role, User
from app.security import hash_password, verify_password

ADMIN_TIER_ROLES = (Role.ADMIN, Role.SUPER_ADMIN)


class DuplicateUsernameError(Exception):
    pass


class WrongCurrentPasswordError(Exception):
    pass


class CannotDeactivateSelfError(Exception):
    pass


class InsufficientPrivilegeError(Exception):
    pass


def _ensure_can_manage_admin_tier(acting_user: User, target: User) -> None:
    """Un Admin ne peut pas modifier (mot de passe, activation) un autre
    compte Admin ou Super Admin — seul un Super Admin le peut. Protège les
    comptes de haut niveau d'un abus ou d'une erreur d'un autre Admin."""
    if target.role in ADMIN_TIER_ROLES and acting_user.role != Role.SUPER_ADMIN:
        raise InsufficientPrivilegeError(
            "Seul un Super Admin peut modifier le mot de passe ou le statut d'un compte Admin"
        )


def create_user(db: Session, username: str, password: str, role: Role, full_name: str = "", acting_user: User | None = None) -> User:
    """acting_user=None (scripts de seed, tests) contourne le contrôle de
    hiérarchie ci-dessous — seul un vrai appel API (via le routeur) le fournit
    et se voit donc appliquer la restriction."""
    if acting_user is not None and role in ADMIN_TIER_ROLES and acting_user.role != Role.SUPER_ADMIN:
        raise InsufficientPrivilegeError("Seul un Super Admin peut créer un compte Admin ou Super Admin")

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


def reset_password(db: Session, user: User, new_password: str, acting_user: User) -> User:
    """Réinitialisation par un Admin/Super Admin, sans connaître l'ancien mot
    de passe."""
    _ensure_can_manage_admin_tier(acting_user, user)
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
    _ensure_can_manage_admin_tier(current_user, user)
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user
