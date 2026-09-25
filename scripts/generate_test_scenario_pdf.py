"""Génère un PDF du scénario de test manuel couvrant les fonctionnalités
récemment ajoutées (crédit client, créances, sessions de caisse). Usage :
    .venv/Scripts/python.exe scripts/generate_test_scenario_pdf.py
Produit Scenario_de_test.pdf à la racine du projet.
"""
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "Scenario_de_test.pdf"

styles = getSampleStyleSheet()
title_style = ParagraphStyle("TitleFR", parent=styles["Title"], fontSize=18, spaceAfter=6)
subtitle_style = ParagraphStyle("SubtitleFR", parent=styles["Normal"], fontSize=10, textColor="#555555", spaceAfter=16)
section_style = ParagraphStyle("SectionFR", parent=styles["Heading2"], fontSize=13, spaceBefore=14, spaceAfter=6)
body_style = ParagraphStyle("BodyFR", parent=styles["Normal"], fontSize=10.5, leading=15)
step_style = ParagraphStyle("StepFR", parent=styles["Normal"], fontSize=10.5, leading=15, spaceAfter=4)

SECTIONS = [
    ("Préparation", [
        "Connectez-vous en <b>Admin</b> (<i>admin</i> / <i>Admin123!</i>).",
        "Menu “Stock” → repérez un produit avec du stock disponible (colonne “Stock (unités)”). "
        "S'il est à 0, enregistrez un mouvement “Entrée” de 20 unités sur ce produit, puis reconnectez-vous en "
        "<b>Manager</b> (<i>manager</i> / <i>Manager123!</i>) pour le <b>valider</b> dans “Mouvements en attente de "
        "validation” (rappel : la personne qui saisit ne peut pas valider elle-même).",
    ]),
    ("Test 1 — Vente normale + suivi de caisse en temps réel", [
        "Connectez-vous en <b>Caissier</b> (<i>caissier</i> / <i>Caissier123!</i>).",
        "Menu “Sessions caisse” → ouvrez avec un fond de caisse de <b>20 000 GNF</b>.",
        "Menu “Caisse” → vendez 1 unité du produit en <b>Espèces</b>, montant remis = le prix exact.",
        "Retournez sur “Sessions caisse” : la vente doit apparaître dans “Mouvements espèces de la "
        "session” avec un <b>total cumulé</b> = 20 000 + le prix du produit. La répartition par mode de paiement "
        "au-dessus affiche aussi “Espèces : ...”.",
    ]),
    ("Test 2 — Vente à crédit + limite de 2 par client", [
        "Toujours sur “Caisse” : ajoutez le produit au panier, choisissez le mode “Crédit (client "
        "fidèle)”.",
        "Remplissez nom = <i>Test Client</i>, téléphone = <i>+224600000999</i>, adresse = <i>Test</i>, montant remis "
        "<b>inférieur</b> au total (ex : moitié du prix). Validez. Le reçu doit indiquer un <b>“reste dû”</b>.",
        "Refaites la même vente à crédit une <b>2e fois</b> pour ce même client → ça passe encore.",
        "Refaites-la une <b>3e fois</b> → doit être <b>refusée</b> avec le message “a dépassé le nombre de "
        "crédits autorisés (2)”.",
    ]),
    ("Test 3 — Créances clients + reçu de règlement", [
        "Menu “Créances clients” → <i>Test Client</i> doit apparaître avec le montant total dû (cumul "
        "des 2 ventes à crédit).",
        "Saisissez un montant de règlement (par exemple la totalité) → “Enregistrer”.",
        "Cliquez “Imprimer le reçu” → un PDF “REÇU DE RÈGLEMENT” doit s'ouvrir.",
        "<i>Test Client</i> doit avoir disparu de la liste des créances.",
        "Refaites une vente à crédit pour lui → ça repasse (le compteur est retombé à zéro).",
    ]),
    ("Test 4 — Écart de caisse bloqué + résolution", [
        "Sur “Sessions caisse”, fermez la session en cours en saisissant un montant physique <b>très "
        "différent</b> du théorique affiché (au moins 10 001 GNF d'écart, par exemple théorique + 15 000).",
        "Le statut doit passer à <b>“blocked”</b>, visible dans “Historique des sessions” en bas de "
        "page.",
        "Reconnectez-vous en <b>Manager</b> → sur cette même ligne de l'historique, cliquez “Résoudre”, "
        "saisissez un commentaire (3 caractères minimum).",
        "Le statut doit passer à <b>“closed”</b>, avec le commentaire visible dans la colonne "
        "“Résolution”.",
    ]),
    ("Test 5 — Déconnexion automatique (optionnel, plus long)", [
        "Restez sur une page sans rien toucher pendant 15 minutes → vous devez être redirigé vers la connexion "
        "avec le message “déconnecté après une période d'inactivité”. Reconnectez-vous : rien n'est perdu.",
    ]),
]


def build() -> None:
    doc = SimpleDocTemplate(
        str(OUTPUT_PATH), pagesize=A4,
        topMargin=20 * mm, bottomMargin=20 * mm, leftMargin=20 * mm, rightMargin=20 * mm,
    )
    story = [
        Paragraph("La Cave du Coin — Scénario de test manuel", title_style),
        Paragraph("Vérification des fonctionnalités crédit client / créances / sessions de caisse.", subtitle_style),
    ]

    for section_title, steps in SECTIONS:
        story.append(Paragraph(section_title, section_style))
        story.append(
            ListFlowable(
                [ListItem(Paragraph(step, step_style)) for step in steps],
                bulletType="1",
                start=1,
                leftIndent=14,
            )
        )
        story.append(Spacer(1, 4))

    doc.build(story)
    print(f"PDF généré : {OUTPUT_PATH}")


if __name__ == "__main__":
    build()
