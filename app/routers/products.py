from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_role
from app.models import Product, Role, User
from app.schemas import ProductCreate, ProductImportResult, ProductOut, ProductUpdatePrice
from app.services import inventory as inventory_service
from app.services import labels as labels_service
from app.services import product_import as product_import_service
from app.services import products as products_service

router = APIRouter(prefix="/api/products", tags=["products"])


def _to_out(db: Session, product: Product) -> ProductOut:
    out = ProductOut.model_validate(product)
    out.current_stock_units = products_service.get_current_stock_units(db, product.id)
    return out


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: Session = Depends(get_db), _: User = Depends(require_role(Role.ADMIN))):
    try:
        product = products_service.create_product(db, payload.model_dump())
    except products_service.PriceBelowMinMarginError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except products_service.DuplicateBarcodeError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return _to_out(db, product)


@router.get("", response_model=list[ProductOut])
def list_products(db: Session = Depends(get_db), _: User = Depends(require_role(Role.ADMIN, Role.MANAGER, Role.CAISSIER))):
    products = db.query(Product).filter(Product.is_active.is_(True)).all()
    return [_to_out(db, p) for p in products]


@router.get("/inventory-sheet.pdf")
def get_inventory_sheet(db: Session = Depends(get_db), _: User = Depends(require_role(Role.ADMIN, Role.MANAGER))):
    """Fiche d'inventaire à l'aveugle (sans stock théorique) pour un comptage
    physique par une tierce personne — voir app/services/inventory.py."""
    products = db.query(Product).filter(Product.is_active.is_(True)).all()
    pdf_bytes = inventory_service.build_inventory_sheet_pdf(products)
    return Response(content=pdf_bytes, media_type="application/pdf")


@router.get("/import/template")
def download_import_template():
    """Modèle CSV sans données sensibles : accessible sans authentification
    pour permettre un simple lien de téléchargement depuis le navigateur."""
    return Response(
        content="﻿" + product_import_service.CSV_TEMPLATE,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=modele_produits.csv"},
    )


@router.post("/import", response_model=ProductImportResult)
async def import_products(
    file: UploadFile,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(Role.ADMIN)),
):
    raw = await file.read()
    csv_text = raw.decode("utf-8-sig")
    result = product_import_service.import_products_from_csv(db, csv_text)
    return ProductImportResult(created=result.created, errors=result.errors)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(get_db), _: User = Depends(require_role(Role.ADMIN))):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produit introuvable")
    products_service.deactivate_product(db, product)


@router.get("/barcode/{barcode}", response_model=ProductOut)
def get_by_barcode(barcode: str, db: Session = Depends(get_db), _: User = Depends(require_role(Role.ADMIN, Role.MANAGER, Role.CAISSIER))):
    product = products_service.find_by_barcode(db, barcode)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produit inconnu")
    return _to_out(db, product)


@router.post("/{product_id}/generate-barcode", response_model=ProductOut)
def generate_barcode(
    product_id: int,
    force: bool = False,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(Role.ADMIN, Role.MANAGER)),
):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produit introuvable")
    try:
        products_service.generate_internal_barcode(db, product, force=force)
    except products_service.BarcodeAlreadySetError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return _to_out(db, product)


@router.get("/{product_id}/label.pdf")
def get_product_label(product_id: int, db: Session = Depends(get_db), _: User = Depends(require_role(Role.ADMIN, Role.MANAGER))):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produit introuvable")
    if not product.barcode:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Ce produit n'a pas encore de code-barres — générez-le d'abord")

    pdf_bytes = labels_service.build_product_label_pdf(product)
    return Response(content=pdf_bytes, media_type="application/pdf")


@router.patch("/{product_id}/price", response_model=ProductOut)
def update_price(
    product_id: int,
    payload: ProductUpdatePrice,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(Role.ADMIN)),
):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produit introuvable")

    new_achat = payload.prix_achat if payload.prix_achat is not None else product.prix_achat
    new_vente = payload.prix_vente if payload.prix_vente is not None else product.prix_vente

    try:
        products_service.validate_price(new_achat, new_vente, payload.is_promo)
    except products_service.PriceBelowMinMarginError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    product.prix_achat = new_achat
    product.prix_vente = new_vente
    if payload.tva_rate is not None:
        product.tva_rate = payload.tva_rate
    db.commit()
    db.refresh(product)
    return _to_out(db, product)
