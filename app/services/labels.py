import io

import qrcode
from reportlab.lib.units import mm as mm_unit
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from app.config import settings
from app.models import Product

LABEL_WIDTH = 70 * mm_unit
LABEL_HEIGHT = 40 * mm_unit


def build_product_label_pdf(product: Product) -> bytes:
    """Étiquette imprimable (QR code interne) pour un produit sans code-barres
    fournisseur — à coller sur le carton/la bouteille. Lisible par un lecteur
    2D (imageur) ou une caméra de smartphone, PAS par un lecteur laser basique."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(LABEL_WIDTH, LABEL_HEIGHT))

    c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(LABEL_WIDTH / 2, LABEL_HEIGHT - 5 * mm_unit, settings.STORE_NAME)

    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(LABEL_WIDTH / 2, LABEL_HEIGHT - 10 * mm_unit, product.name[:28])

    c.setFont("Helvetica", 8)
    c.drawCentredString(LABEL_WIDTH / 2, LABEL_HEIGHT - 15 * mm_unit, f"{product.prix_vente:,} GNF")

    qr_img = qrcode.make(product.barcode)
    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)

    qr_size = 20 * mm_unit
    c.drawImage(ImageReader(qr_buffer), (LABEL_WIDTH - qr_size) / 2, 3 * mm_unit, qr_size, qr_size)

    c.setFont("Courier", 7)
    c.drawCentredString(LABEL_WIDTH / 2, 1 * mm_unit, product.barcode)

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()
