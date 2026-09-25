"""Génère un diaporama PDF (une diapo par page, format paysage) à partir du
contenu de FORMATION.md, pour présenter le logiciel aux collaborateurs en
réunion (projeté ou imprimé) — condensé et visuel, le détail complet reste
dans FORMATION.md.
Usage : .venv/Scripts/python.exe scripts/generate_formation_slides_pdf.py
Produit La_Cave_du_Coin_Formation_Diaporama.pdf à la racine du projet.
"""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "La_Cave_du_Coin_Formation_Diaporama.pdf"

GOLD = colors.HexColor("#a9782f")
GOLD_DARK = colors.HexColor("#7a5a22")
INK = colors.HexColor("#2a2019")
DIM = colors.HexColor("#6b5f4f")
WARN = colors.HexColor("#a05a3a")

styles = getSampleStyleSheet()
kicker_style = ParagraphStyle("Kicker", parent=styles["Normal"], fontSize=13, textColor=GOLD, fontName="Helvetica-Bold", spaceAfter=6)
title_style = ParagraphStyle("SlideTitle", parent=styles["Title"], fontSize=30, textColor=INK, alignment=0, spaceAfter=14)
subtitle_style = ParagraphStyle("SlideSubtitle", parent=styles["Normal"], fontSize=15, textColor=DIM, spaceAfter=14, leading=20)
bullet_style = ParagraphStyle("SlideBullet", parent=styles["Normal"], fontSize=16, textColor=INK, leading=23, spaceAfter=8)
note_style = ParagraphStyle("SlideNote", parent=styles["Normal"], fontSize=13.5, textColor=WARN, fontName="Helvetica-Bold", leading=19, spaceBefore=12)
cover_title_style = ParagraphStyle("CoverTitle", parent=styles["Title"], fontSize=40, textColor=INK, alignment=1, spaceAfter=10)
cover_sub_style = ParagraphStyle("CoverSub", parent=styles["Normal"], fontSize=17, textColor=GOLD_DARK, alignment=1, fontName="Helvetica-Bold")
table_header_style = ParagraphStyle("TblHeader", parent=styles["Normal"], fontSize=13, textColor=colors.white, fontName="Helvetica-Bold")
table_cell_style = ParagraphStyle("TblCell", parent=styles["Normal"], fontSize=12.5, textColor=INK, leading=17)


def gold_rule():
    t = Table([[""]], colWidths=[250 * mm], rowHeights=[2.5])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), GOLD)]))
    return t


def slide(kicker: str, title: str, bullets: list, note: str | None = None) -> list:
    story = [Paragraph(kicker, kicker_style), Paragraph(title, title_style), gold_rule(), Spacer(1, 10)]
    items = [ListItem(Paragraph(b, bullet_style), bulletColor=GOLD) for b in bullets]
    story.append(ListFlowable(items, bulletType="bullet", start="●", leftIndent=16, spaceBefore=4))
    if note:
        story.append(Paragraph(note, note_style))
    story.append(PageBreak())
    return story


def table_slide(kicker: str, title: str, headers: list, rows: list, col_widths: list) -> list:
    story = [Paragraph(kicker, kicker_style), Paragraph(title, title_style), gold_rule(), Spacer(1, 10)]
    data = [[Paragraph(h, table_header_style) for h in headers]]
    for row in rows:
        data.append([Paragraph(c, table_cell_style) for c in row])
    t = Table(data, colWidths=col_widths)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), GOLD_DARK),
                ("GRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#cbbfa8")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5efe0")]),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(t)
    story.append(PageBreak())
    return story


def build() -> None:
    doc = SimpleDocTemplate(
        str(OUTPUT_PATH), pagesize=landscape(A4),
        topMargin=16 * mm, bottomMargin=16 * mm, leftMargin=20 * mm, rightMargin=20 * mm,
    )
    story = []

    # ---------------------------------------------------------- Couverture
    story += [
        Spacer(1, 60),
        Paragraph("La Cave du Coin", cover_title_style),
        Paragraph("Formation à l'utilisation du logiciel de caisse & de stock", cover_sub_style),
        Spacer(1, 30),
        Paragraph(
            "Ce diaporama résume les points essentiels par rôle. Le détail complet, "
            "avec toutes les étapes, reste disponible dans le guide écrit (FORMATION.md).",
            ParagraphStyle("CoverNote", parent=styles["Normal"], fontSize=13, textColor=DIM, alignment=1),
        ),
        PageBreak(),
    ]

    # ---------------------------------------------------------- Les rôles
    story += table_slide(
        "PRISE EN MAIN", "Les 4 rôles, du plus limité au plus large",
        ["Rôle", "Peut faire"],
        [
            ["Caissier", "Vendre, encaisser, ouvrir/fermer sa caisse, gérer les retours et les créances clients"],
            ["Manager", "Tout le Caissier + stock, fournisseurs, statistiques, annuler une vente sans limite de temps"],
            ["Admin", "Tout le Manager + créer/gérer les comptes utilisateurs (sauf Admin/Super Admin)"],
            ["Super Admin", "Tout, y compris gérer les comptes Admin (le seul qui le peut)"],
        ],
        [55 * mm, 190 * mm],
    )
    story += slide(
        "PRISE EN MAIN — TOUT LE MONDE", "Se connecter et les bases",
        [
            "Identifiant + mot de passe → on arrive sur la page Caisse",
            "Déconnexion automatique après 15 minutes d'inactivité — aucune donnée perdue, la caisse reste ouverte",
            "Changer son mot de passe : menu \"Mon compte\", à tout moment, sans avoir besoin de personne",
        ],
    )

    # ---------------------------------------------------------- Caissier
    story += slide(
        "GUIDE DU CAISSIER", "Ouvrir sa session de caisse",
        [
            "Obligatoire avant toute vente",
            "Menu \"Sessions caisse\" → saisir le fond de caisse initial → \"Ouvrir\"",
            "Sans session ouverte, la page de vente bloque toute vente",
        ],
    )
    story += slide(
        "GUIDE DU CAISSIER", "Enregistrer une vente",
        [
            "Ajouter les produits : scanner le code-barres ou cliquer dans la recherche rapide",
            "Ajuster les quantités (+ / −), choisir le mode de paiement",
            "Saisir le montant remis → la monnaie s'affiche automatiquement",
            "Valider la vente → imprimer le reçu (2ᵉ impression = DUPLICATA automatique)",
        ],
        note="Plus de 5 articles identiques → confirmation manuelle obligatoire (anti-fraude).",
    )
    story += slide(
        "GUIDE DU CAISSIER", "Vente à crédit pour un client fidèle",
        [
            "Rechercher le client par téléphone, ou saisir ses infos s'il est nouveau",
            "Renseigner la date de remboursement prévue",
            "Le reste à payer devient une créance, visible dans \"Créances clients\"",
        ],
        note="Maximum 2 créances en cours par client — la 3ᵉ vente à crédit est refusée.",
    )
    story += slide(
        "GUIDE DU CAISSIER", "Retour client et avoir",
        [
            "Jamais de remboursement en espèces : le montant est crédité sur un compte \"avoir\"",
            "Rechercher le ticket d'origine par numéro de transaction",
            "Indiquer la quantité retournée, le client, le motif",
            "Le stock est réapprovisionné automatiquement, l'avoir réutilisable au prochain achat",
        ],
    )
    story += slide(
        "GUIDE DU CAISSIER", "Créances clients",
        [
            "Liste triée par échéance la plus urgente",
            "Enregistrer un règlement (partiel ou total) → reçu imprimable",
            "Réglé en priorité : la dette la plus ancienne",
            "Tout règlement est tracé (qui, quand, combien)",
        ],
    )
    story += slide(
        "GUIDE DU CAISSIER — NOUVEAU", "Créer un devis pour un client",
        [
            "Un devis : prix figé, sans encaissement ni sortie de stock",
            "Ne nécessite PAS de session de caisse ouverte",
            "Numéro court (ex : DEV-A7K9M), scannable via le QR code imprimé",
            "Validité 15 jours par défaut",
        ],
        note="Le prix imprimé reste valable même si le prix courant change entre-temps.",
    )
    story += slide(
        "GUIDE DU CAISSIER — CAS D'USAGE", "Client sans cash pendant la file d'attente",
        [
            "Créer un devis pour son panier, lui remettre le numéro imprimé",
            "Continuer à servir les clients suivants",
            "À son retour : charger le devis pour finaliser la vente",
        ],
        note="⚠️ Ne jamais remettre la marchandise avant l'encaissement réel — le devis n'est qu'une promesse de prix.",
    )
    story += slide(
        "GUIDE DU CAISSIER", "Convertir un devis en vente",
        [
            "Section \"Convertir un devis en vente\" → saisir ou scanner le numéro",
            "Choisir le mode de paiement, saisir le montant remis",
            "Nécessite une session de caisse ouverte (contrairement à la création)",
        ],
        note="Un devis expiré ou déjà converti ne peut plus être reconverti.",
    )
    story += slide(
        "GUIDE DU CAISSIER", "Fermer sa session de caisse",
        [
            "Compter physiquement l'argent en caisse",
            "Saisir le montant physique compté → \"Fermer\"",
            "Le système compare au montant théorique et affiche l'écart",
        ],
        note="⚠️ Écart > 10 000 GNF → session bloquée automatiquement, déblocage par un Manager avec commentaire obligatoire.",
    )

    # ---------------------------------------------------------- Manager
    story += slide(
        "GUIDE DU MANAGER", "Gérer le stock",
        [
            "Créer un produit : prix, catégorie, unités par carton/pack, seuil d'alerte",
            "Enregistrer un mouvement : entrée, casse, don, ajustement",
            "Ajustement uniquement : quantité négative = manque constaté, positive = surplus",
        ],
        note="Tout mouvement hors vente doit être validé par une 2ᵉ personne différente de celle qui l'a saisi.",
    )
    story += slide(
        "GUIDE DU MANAGER — NOUVEAU", "Fiche d'inventaire à l'aveugle",
        [
            "Bouton dédié au-dessus du tableau \"Produits & stock courant\"",
            "PDF listant les produits, sans afficher le stock théorique",
            "Pensé pour un comptage physique fiable par une tierce personne",
        ],
    )
    story += slide(
        "GUIDE DU MANAGER — NOUVEAU", "Péremption par lot (FEFO)",
        [
            "Chaque entrée de stock peut recevoir sa propre date de péremption",
            "Plusieurs livraisons du même produit peuvent coexister avec des dates différentes",
            "Le lot qui expire le plus tôt est considéré consommé en priorité",
            "Alerte automatique sur le tableau de bord si la péremption approche (7 jours par défaut)",
        ],
    )
    story += slide(
        "GUIDE DU MANAGER", "Fournisseurs, étiquettes, import CSV",
        [
            "Fournisseurs : ajouter, voir l'historique de livraisons, désactiver",
            "Codes-barres internes + étiquettes PDF pour les produits sans code-barres fournisseur",
            "Import CSV en masse : catalogue produits ou mouvements de stock",
        ],
    )
    story += table_slide(
        "GUIDE DU MANAGER — RÉFÉRENCE", "Import CSV — champs du catalogue produits",
        ["Colonne", "Obligatoire", "Explication"],
        [
            ["barcode", "Non", "Code-barres fabricant (facultatif — un code interne peut être généré plus tard)"],
            ["name", "Oui", "Nom du produit, affiché partout (caisse, reçus, stock)"],
            ["category", "Oui", "Catégorie libre, utilisée pour la ventilation des ventes par catégorie"],
            ["unit_carton_qty", "Non (24)", "Unités par carton — conversion automatique"],
            ["unit_pack_qty", "Non (6)", "Unités par pack — conversion automatique"],
            ["prix_achat", "Oui", "Prix d'achat unitaire (GNF)"],
            ["prix_vente", "Oui", "Prix de vente unitaire — doit rester ≥ prix d'achat − 5 % (anti-fraude)"],
            ["stock_min_cartons", "Non (5)", "Seuil d'alerte de rupture, en cartons"],
            ["supplier", "Non", "Nom du fournisseur — créé automatiquement s'il n'existe pas"],
        ],
        [45 * mm, 32 * mm, 168 * mm],
    )
    story += table_slide(
        "GUIDE DU MANAGER — RÉFÉRENCE", "Import CSV — champs des mouvements de stock",
        ["Colonne", "Obligatoire", "Explication"],
        [
            ["barcode", "Oui", "Code-barres du produit — doit déjà exister en base"],
            ["type", "Oui", "entree / casse / don / ajustement (jamais sortie_vente, réservée aux ventes)"],
            ["qty", "Oui", "Positive, sauf ajustement (négatif = manque constaté)"],
            ["unit", "Non (unite)", "unite / carton / pack — conversion automatique"],
            ["invoice_number", "Non", "N° de facture fournisseur (pertinent pour une entrée)"],
            ["expiry_date", "Non", "Date de péremption du lot, format AAAA-MM-JJ (entrée)"],
            ["reason", "Non", "Motif — recommandé pour casse/don/ajustement, utile à la validation"],
            ["supplier", "Non", "Nom du fournisseur — même comportement que l'import produits"],
        ],
        [45 * mm, 32 * mm, 168 * mm],
    )
    story += slide(
        "GUIDE DU MANAGER — NOUVEAU", "Tableau de bord \"Aujourd'hui\"",
        [
            "CA du jour, ventes, devis créés/convertis, mouvements de stock, écarts de caisse",
            "Flux d'activité chronologique de la journée",
            "Actualisation automatique toutes les 15 secondes",
            "Camembert des produits vendus aujourd'hui",
        ],
    )
    story += slide(
        "GUIDE DU MANAGER", "Comptages physiques réguliers",
        [
            "Le logiciel ne peut pas détecter une vente jamais saisie",
            "Interdire tout stock personnel du caissier près de la caisse",
            "Comptage régulier (fiche à l'aveugle) + comptages surprises",
            "Tout écart → mouvement \"Ajustement\", validation Admin obligatoire",
        ],
        note="Un écart récurrent, toujours dans le même sens, est le vrai signal à surveiller.",
    )

    # ---------------------------------------------------------- Admin / Super Admin
    story += slide(
        "GUIDE DE L'ADMIN", "Gestion des utilisateurs",
        [
            "Créer un compte (Caissier / Manager / Admin), réinitialiser un mot de passe",
            "Désactiver/réactiver un compte — l'historique reste toujours intact",
            "Un Admin ne peut pas toucher un autre compte Admin ou Super Admin",
        ],
    )
    story += slide(
        "LE SUPER ADMIN", "Un rôle de secours",
        [
            "Mêmes pages que l'Admin + gérer les comptes Admin et Super Admin",
            "À réserver à une seule personne de confiance",
            "Garantit qu'il reste toujours quelqu'un capable de débloquer les Admins",
        ],
    )

    # ---------------------------------------------------------- Anti-fraude
    story += table_slide(
        "À CONNAÎTRE PAR TOUS", "Règles anti-fraude automatiques",
        ["Règle", "Seuil"],
        [
            ["Annulation par un Caissier", "5 min max, motif obligatoire"],
            ["Vente/devis d'articles identiques", "confirmation requise au-delà de 5 unités"],
            ["Double scan du même produit", "alerte si < 2 secondes"],
            ["Écart de caisse à la fermeture", "blocage si > 10 000 GNF"],
            ["Mouvement de stock hors vente", "validation par une personne différente"],
            ["Ajustement d'inventaire", "validation Admin uniquement"],
            ["Créances non réglées", "maximum 2 par client"],
            ["Réimpression d'un ticket", "DUPLICATA automatique"],
        ],
        [110 * mm, 135 * mm],
    )

    # ---------------------------------------------------------- FAQ
    story += slide(
        "QUESTIONS FRÉQUENTES", "En bref",
        [
            "Déconnecté après 15 min ? Rien n'est perdu, reconnectez-vous",
            "Vente à crédit refusée ? Le client a déjà 2 créances en cours",
            "Le stock ne bouge pas ? Le mouvement attend une 2ᵉ validation",
            "Session \"blocked\" ? Un Manager doit \"Résoudre\" avec un commentaire",
            "Devis introuvable/expiré ? Refaites-en un, l'ancien n'est plus valable",
        ],
    )

    # ---------------------------------------------------------- Fin
    story += [
        Spacer(1, 60),
        Paragraph("Merci !", cover_title_style),
        Paragraph("Le guide complet et détaillé reste disponible dans FORMATION.md", cover_sub_style),
    ]

    doc.build(story)
    print(f"PDF généré : {OUTPUT_PATH}")


if __name__ == "__main__":
    build()
