import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.config import settings
from app.models import Product

styles = getSampleStyleSheet()
_title_style = ParagraphStyle("InvTitle", parent=styles["Title"], fontSize=15, spaceAfter=2)
_subtitle_style = ParagraphStyle("InvSubtitle", parent=styles["Normal"], fontSize=9, textColor="#555555", spaceAfter=10)
_header_style = ParagraphStyle("InvHeader", parent=styles["Normal"], fontSize=8.5, textColor=colors.white, fontName="Helvetica-Bold")
_cell_style = ParagraphStyle("InvCell", parent=styles["Normal"], fontSize=8.5, leading=11)
_note_style = ParagraphStyle("InvNote", parent=styles["Normal"], fontSize=8.5, leading=12, spaceBefore=10)


def build_inventory_sheet_pdf(products: list[Product]) -> bytes:
    """Fiche d'inventaire à l'aveugle : ne montre AUCUN stock théorique du
    système, volontairement — le but est qu'une tierce personne compte sans
    être influencée par le chiffre attendu. La comparaison avec le stock
    théorique se fait après coup, une fois la fiche remplie à la main."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A4),
        topMargin=14 * mm, bottomMargin=14 * mm, leftMargin=14 * mm, rightMargin=14 * mm,
    )
    story = []

    story.append(Paragraph(f"{settings.STORE_NAME} — Fiche d'inventaire (comptage physique)", _title_style))
    story.append(Paragraph(
        f"Générée le {datetime.now().strftime('%Y-%m-%d %H:%M')}. "
        "Cette fiche ne contient volontairement aucun stock théorique : comptez ce que vous voyez "
        "physiquement, sans consulter le logiciel.",
        _subtitle_style,
    ))

    header = [Paragraph(h, _header_style) for h in [
        "Catégorie", "Produit", "Code-barres", "U./carton", "U./pack",
        "Cartons comptés", "Packs comptés", "Unités isolées comptées",
    ]]
    data = [header]
    for product in sorted(products, key=lambda p: (p.category, p.name)):
        data.append([
            Paragraph(product.category, _cell_style),
            Paragraph(product.name, _cell_style),
            Paragraph(product.barcode or "—", _cell_style),
            Paragraph(str(product.unit_carton_qty), _cell_style),
            Paragraph(str(product.unit_pack_qty), _cell_style),
            "",
            "",
            "",
        ])

    col_widths = [32 * mm, 62 * mm, 32 * mm, 18 * mm, 18 * mm, 26 * mm, 26 * mm, 32 * mm]
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#999999")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("MINROWHEIGHT", (0, 1), (-1, -1), 9 * mm),
            ]
        )
    )
    story.append(table)

    story.append(Paragraph(
        "Compté par : ______________________________ &nbsp;&nbsp;&nbsp; "
        "Date du comptage : ___ / ___ / ______ &nbsp;&nbsp;&nbsp; "
        "Vérifié par (Manager/Admin) : ______________________________",
        _note_style,
    ))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Une fois remplie, remettre cette fiche à un Manager ou Admin pour comparaison avec le stock "
        "théorique du système et, si besoin, saisie d'un mouvement d'ajustement.",
        _note_style,
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
