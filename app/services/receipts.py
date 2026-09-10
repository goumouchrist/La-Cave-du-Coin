import io

import qrcode
from reportlab.lib.pagesizes import mm
from reportlab.lib.units import mm as mm_unit
from reportlab.pdfgen import canvas

from app.config import settings
from app.models import Product, Sale


RECEIPT_WIDTH = 80 * mm


def compute_total_tva(sale: Sale, products_by_id: dict[int, Product]) -> int:
    """Montant de TVA inclus dans le total, à titre informatif (le prix de
    vente affiché/facturé ne change pas, cf. décision produit : pas de TVA
    ajoutée pour l'instant, seulement un affichage informatif si un taux a
    été renseigné sur le produit)."""
    return sum(
        round(item.unit_price * item.qty_units * products_by_id[item.product_id].tva_rate)
        for item in sale.items
        if products_by_id.get(item.product_id) and products_by_id[item.product_id].tva_rate
    )


def build_receipt_pdf(sale: Sale, products_by_id: dict[int, Product], cashier_name: str, is_duplicata: bool) -> bytes:
    total_tva = compute_total_tva(sale, products_by_id)

    height = (120 + len(sale.items) * 8 + (6 if total_tva else 0)) * mm_unit
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(RECEIPT_WIDTH, height))

    y = height - 10 * mm_unit
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(RECEIPT_WIDTH / 2, y, settings.STORE_NAME)
    y -= 5 * mm_unit
    c.setFont("Helvetica", 7)
    c.drawCentredString(RECEIPT_WIDTH / 2, y, settings.STORE_ADDRESS)
    y -= 4 * mm_unit
    c.drawCentredString(RECEIPT_WIDTH / 2, y, f"NIF: {settings.STORE_NIF}")
    y -= 6 * mm_unit

    if is_duplicata:
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(RECEIPT_WIDTH / 2, y, "*** DUPLICATA ***")
        y -= 6 * mm_unit

    c.setFont("Helvetica", 7)
    c.drawString(4 * mm_unit, y, f"Transaction: {sale.transaction_number}")
    y -= 4 * mm_unit
    c.drawString(4 * mm_unit, y, f"Date: {sale.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    y -= 4 * mm_unit
    c.drawString(4 * mm_unit, y, f"Caissier: {cashier_name}")
    y -= 6 * mm_unit

    c.line(4 * mm_unit, y, RECEIPT_WIDTH - 4 * mm_unit, y)
    y -= 5 * mm_unit

    for item in sale.items:
        product = products_by_id.get(item.product_id)
        name = product.name if product else f"Produit#{item.product_id}"
        line_total = item.unit_price * item.qty_units
        c.setFont("Helvetica", 7)
        c.drawString(4 * mm_unit, y, f"{name[:22]}")
        y -= 3.5 * mm_unit
        c.drawString(4 * mm_unit, y, f"  {item.qty_units} x {item.unit_price:,} GNF = {line_total:,} GNF")
        y -= 5 * mm_unit

    c.line(4 * mm_unit, y, RECEIPT_WIDTH - 4 * mm_unit, y)
    y -= 5 * mm_unit

    c.setFont("Helvetica-Bold", 9)
    c.drawString(4 * mm_unit, y, f"TOTAL: {sale.total_amount:,} GNF")
    y -= 5 * mm_unit

    if total_tva:
        c.setFont("Helvetica-Oblique", 6.5)
        c.drawString(4 * mm_unit, y, f"Dont TVA: {total_tva:,} GNF")
        y -= 4 * mm_unit

    c.setFont("Helvetica", 7)
    c.drawString(4 * mm_unit, y, f"Reçu: {sale.amount_given:,} GNF")
    y -= 4 * mm_unit
    c.drawString(4 * mm_unit, y, f"Monnaie rendue: {sale.change_amount:,} GNF")
    y -= 4 * mm_unit
    c.drawString(4 * mm_unit, y, f"Mode de paiement: {sale.payment_mode.value}")
    y -= 6 * mm_unit

    qr_img = qrcode.make(sale.transaction_number)
    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)
    from reportlab.lib.utils import ImageReader

    qr_size = 20 * mm_unit
    c.drawImage(ImageReader(qr_buffer), (RECEIPT_WIDTH - qr_size) / 2, y - qr_size, qr_size, qr_size)
    y -= qr_size + 4 * mm_unit

    c.setFont("Helvetica-Oblique", 6)
    c.drawCentredString(RECEIPT_WIDTH / 2, y, "Ticket valable 7 jours pour échange/retour")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()
