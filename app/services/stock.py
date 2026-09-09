from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import MovementStatus, MovementType, Role, StockMovement, User
from app.services.products import convert_to_units


class SelfValidationError(Exception):
    pass


class ValidatorRoleError(Exception):
    pass


class MovementAlreadyProcessedError(Exception):
    pass


def create_movement(
    db: Session,
    product,
    type_: MovementType,
    qty: int,
    unit: str,
    created_by: int,
    invoice_number: str | None = None,
    reason: str | None = None,
    supplier_id: int | None = None,
) -> StockMovement:
    qty_units = convert_to_units(product, qty, unit)

    # Une sortie liée à une vente, ou une entrée liée à un retour client déjà
    # rattaché à une vente d'origine et un client identifié, sont appliquées
    # immédiatement (flux normal de caisse, déjà traçable). Toute autre
    # modification de stock passe par le workflow de double validation
    # (règle anti-fraude n°4 : saisie + supervision).
    AUTO_VALIDATED_TYPES = (MovementType.SORTIE_VENTE, MovementType.RETOUR)
    status = MovementStatus.VALIDATED if type_ in AUTO_VALIDATED_TYPES else MovementStatus.PENDING

    movement = StockMovement(
        product_id=product.id,
        supplier_id=supplier_id,
        type=type_,
        qty_units=qty_units,
        invoice_number=invoice_number,
        reason=reason,
        status=status,
        created_by=created_by,
        validated_by=created_by if status == MovementStatus.VALIDATED else None,
        validated_at=datetime.now(timezone.utc) if status == MovementStatus.VALIDATED else None,
    )
    db.add(movement)
    db.commit()
    db.refresh(movement)
    return movement


def validate_movement(db: Session, movement: StockMovement, validator: User, approve: bool, comment: str | None = None) -> StockMovement:
    if movement.status != MovementStatus.PENDING:
        raise MovementAlreadyProcessedError("Ce mouvement a déjà été traité")

    if validator.id == movement.created_by:
        raise SelfValidationError("Le mouvement doit être validé par une personne différente de celle qui l'a saisi")

    if movement.type == MovementType.AJUSTEMENT and validator.role != Role.ADMIN:
        raise ValidatorRoleError("Seul l'Admin peut valider un ajustement d'inventaire")

    if validator.role == Role.CAISSIER:
        raise ValidatorRoleError("Un caissier ne peut pas valider un mouvement de stock")

    movement.status = MovementStatus.VALIDATED if approve else MovementStatus.REJECTED
    movement.validated_by = validator.id
    movement.validated_at = datetime.now(timezone.utc)
    if comment:
        movement.reason = f"{movement.reason or ''}\n[Validation] {comment}".strip()
    db.commit()
    db.refresh(movement)
    return movement
