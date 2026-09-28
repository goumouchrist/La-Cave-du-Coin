"""Génère un PDF de référence listant tous les scripts du projet (scripts/*),
leur rôle, leurs dépendances entre eux, et l'ordre dans lequel on les exécute
selon le scénario (déploiement initial, vie courante, rollback, documentation).
Usage : .venv/Scripts/python.exe scripts/generate_scripts_reference_pdf.py
Produit Reference_Scripts_Projet.pdf à la racine du projet.
"""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "Reference_Scripts_Projet.pdf"

styles = getSampleStyleSheet()
title_style = ParagraphStyle("TitleFR", parent=styles["Title"], fontSize=18, spaceAfter=4)
subtitle_style = ParagraphStyle("SubtitleFR", parent=styles["Normal"], fontSize=10, textColor="#555555", spaceAfter=16)
h1_style = ParagraphStyle("H1FR", parent=styles["Heading1"], fontSize=14, spaceBefore=16, spaceAfter=8, textColor="#1a1a1a")
h2_style = ParagraphStyle("H2FR", parent=styles["Heading2"], fontSize=11.5, spaceBefore=10, spaceAfter=4, textColor="#1a1a1a")
body_style = ParagraphStyle("BodyFR", parent=styles["Normal"], fontSize=9.7, leading=14, spaceAfter=6)
cmd_style = ParagraphStyle("CmdFR", parent=styles["Normal"], fontName="Courier", fontSize=8.7, leading=12, textColor="#0a3d62")
explain_style = ParagraphStyle("ExplainFR", parent=styles["Normal"], fontSize=9, leading=12.5)
note_style = ParagraphStyle("NoteFR", parent=styles["Normal"], fontSize=9, leading=13, textColor="#7a4a00", spaceBefore=4, spaceAfter=6)


def script_table(rows):
    """rows: list of (script, role/dependances) -> tableau 2 colonnes."""
    data = [[Paragraph("Script", styles["Heading4"]), Paragraph("Rôle et dépendances", styles["Heading4"])]]
    for cmd, explanation in rows:
        data.append([Paragraph(cmd, cmd_style), Paragraph(explanation, explain_style)])
    t = Table(data, colWidths=[55 * mm, 110 * mm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return t


def build() -> None:
    doc = SimpleDocTemplate(
        str(OUTPUT_PATH), pagesize=A4,
        topMargin=16 * mm, bottomMargin=16 * mm, leftMargin=16 * mm, rightMargin=16 * mm,
    )
    story = []

    story.append(Paragraph("La Cave du Coin — Référence des scripts du projet", title_style))
    story.append(Paragraph(
        "Rôle de chaque script présent dans scripts/, ses dépendances vis-à-vis des autres "
        "fichiers/scripts, et l'ordre dans lequel ils s'exécutent selon le scénario "
        "(déploiement initial, vie courante, rollback, documentation).",
        subtitle_style,
    ))

    # ------------------------------------------------------------------
    story.append(Paragraph("1. Vue d'ensemble par catégorie", h1_style))
    story.append(Paragraph(
        "Les scripts se répartissent en cinq familles. Toutes s'exécutent sur le VPS depuis le "
        "dossier du projet (<font face='Courier'>/opt/La_Cave_du_Coin</font>), sauf "
        "<font face='Courier'>register_backup_task.ps1</font> qui est un script Windows destiné "
        "à un PC hébergeant lui-même l'application.",
        body_style,
    ))
    story.append(
        ListFlowable(
            [
                ListItem(Paragraph("<b>Initialisation / configuration</b> — <font face='Courier'>seed_data.py</font>, "
                                    "<font face='Courier'>add_pgadmin_env_vars.sh</font>, "
                                    "<font face='Courier'>add_pgadmin_domain.sh</font>.", explain_style)),
                ListItem(Paragraph("<b>Sauvegarde</b> — <font face='Courier'>backup.py</font>, "
                                    "<font face='Courier'>register_backup_task.ps1</font>.", explain_style)),
                ListItem(Paragraph("<b>Restauration / rollback</b> — <font face='Courier'>restore_prod_from_backup.sh</font>, "
                                    "<font face='Courier'>restore_dump_into_staging.sh</font>, "
                                    "<font face='Courier'>restore_latest_reset_backup_into_staging.sh</font>.", explain_style)),
                ListItem(Paragraph("<b>Environnement staging</b> — <font face='Courier'>refresh_staging_from_prod.sh</font>, "
                                    "<font face='Courier'>verify_staging.sh</font>.", explain_style)),
                ListItem(Paragraph("<b>Réinitialisation prod</b> — <font face='Courier'>reset_prod_database.sh</font> "
                                    "(script pivot : produit un fichier consommé par deux scripts de la famille "
                                    "\"staging\").", explain_style)),
                ListItem(Paragraph("<b>Génération de documentation PDF</b> — les cinq scripts "
                                    "<font face='Courier'>generate_*_pdf.py</font>, indépendants les uns des autres.", explain_style)),
            ],
            bulletType="bullet",
            leftIndent=12,
        )
    )

    # ------------------------------------------------------------------
    story.append(Paragraph("2. Initialisation et configuration", h1_style))
    story.append(script_table([
        ("scripts/seed_data.py", "Crée les 4 comptes par défaut (superadmin/admin/manager/caissier) et, sauf appel avec "
         "<font face='Courier'>--users-only</font>, 8 produits de démonstration. <b>Prérequis</b> : le schéma de "
         "base doit déjà exister (fait automatiquement par <font face='Courier'>alembic upgrade head</font> au "
         "démarrage du conteneur app, cf. Dockerfile). <b>Appelé par</b> : "
         "<font face='Courier'>reset_prod_database.sh</font> (en mode <font face='Courier'>--users-only</font>) ; "
         "peut aussi être lancé seul lors d'un premier déploiement."),
        ("scripts/add_pgadmin_env_vars.sh", "Ajoute à <font face='Courier'>.env.staging</font> les identifiants pgAdmin par défaut "
         "(email + mot de passe), sans avoir à taper le caractère <font face='Courier'>@</font> à la console "
         "Hetzner. Idempotent (sans effet si déjà fait). <b>Prérequis</b> : être lancé depuis le dossier du "
         "projet, <font face='Courier'>.env.staging</font> doit déjà exister."),
        ("scripts/add_pgadmin_domain.sh", "Ajoute à <font face='Courier'>.env</font> (celui de prod, lu par Caddy) la ligne "
         "<font face='Courier'>PGADMIN_DOMAIN=...</font>, sans taper de <font face='Courier'>_</font>. Idempotent. "
         "<b>Effet dépendant</b> : un <font face='Courier'>docker compose up -d --build</font> est nécessaire "
         "ensuite pour que Caddy relise le <font face='Courier'>.env</font> mis à jour."),
    ]))

    # ------------------------------------------------------------------
    story.append(Paragraph("3. Sauvegarde", h1_style))
    story.append(script_table([
        ("scripts/backup.py", "Sauvegarde la base (SQLite en local, ou PostgreSQL en prod via "
         "<font face='Courier'>docker compose exec db pg_dump</font>) vers un fichier SQL brut horodaté dans "
         "<font face='Courier'>backups/</font>, copie éventuellement hors-site, puis purge les sauvegardes plus "
         "vieilles que <font face='Courier'>BACKUP_RETENTION_DAYS</font>. <b>Format produit</b> : SQL brut "
         "(<font face='Courier'>pg_dump</font> sans <font face='Courier'>-Fc</font>) — <b>consommé par</b> "
         "<font face='Courier'>restore_prod_from_backup.sh</font> uniquement (pas compatible avec les scripts qui "
         "attendent un format <font face='Courier'>-Fc</font>, voir encadré section 5)."),
        ("scripts/register_backup_task.ps1", "Script Windows (PowerShell, à exécuter une fois en administrateur) qui enregistre une tâche "
         "planifiée exécutant <font face='Courier'>backup.py</font> toutes les 4h. <b>Dépend de</b> : un "
         "environnement virtuel Python déjà créé (<font face='Courier'>.venv</font>). Pertinent seulement si "
         "l'application tourne sur un PC local (option non retenue pour ce projet, hébergé sur VPS) — sur le "
         "VPS, l'équivalent serait une tâche cron appelant <font face='Courier'>backup.py</font>."),
    ]))

    # ------------------------------------------------------------------
    story.append(Paragraph("4. Réinitialisation de la production", h1_style))
    story.append(script_table([
        ("scripts/reset_prod_database.sh", "Script <b>pivot</b> à usage ponctuel : sauvegarde la prod actuelle "
         "(<font face='Courier'>pg_dump -Fc</font> → <font face='Courier'>backup_before_reset_&lt;horodatage&gt;."
         "dump</font>), reconstruit l'image app, vide toutes les tables métier (<font face='Courier'>TRUNCATE ... "
         "RESTART IDENTITY CASCADE</font>), puis appelle <font face='Courier'>seed_data.py --users-only</font> "
         "pour ne recréer que les 4 comptes par défaut. <b>Format produit</b> : dump <font face='Courier'>-Fc</font> "
         "(binaire compressé, nécessite <font face='Courier'>pg_restore</font>, pas <font face='Courier'>psql "
         "&lt;</font>). <b>Consommé par</b> : <font face='Courier'>refresh_staging_from_prod.sh</font> (comme "
         "solution de repli si la prod est encore vide) et <font face='Courier'>restore_latest_reset_backup_into_"
         "staging.sh</font> (pour renvoyer ces données de démo vers staging)."),
    ]))
    story.append(Paragraph(
        "<b>Point d'attention</b> (rencontré en pratique le 2026-09-28) : le fichier produit par ce script "
        "(<font face='Courier'>-Fc</font>) n'est <b>pas</b> compatible avec "
        "<font face='Courier'>restore_prod_from_backup.sh</font>, qui attend un dump SQL brut (celui de "
        "<font face='Courier'>backup.py</font>). Pour restaurer un fichier "
        "<font face='Courier'>backup_before_reset_*.dump</font> directement en prod (cas rare, hors staging), il "
        "faut utiliser manuellement <font face='Courier'>pg_restore</font> avec les options "
        "<font face='Courier'>--clean --if-exists</font>, comme le fait déjà "
        "<font face='Courier'>restore_dump_into_staging.sh</font> mais visé sur la base prod plutôt que staging.",
        note_style,
    ))

    # ------------------------------------------------------------------
    story.append(Paragraph("5. Restauration / rollback", h1_style))
    story.append(script_table([
        ("scripts/restore_prod_from_backup.sh &lt;fichier.sql&gt;", "Restaure en <b>production</b> un dump SQL brut (celui produit par "
         "<font face='Courier'>backup.py</font>). Prend automatiquement une sauvegarde de sécurité de l'état "
         "actuel avant toute modification (<font face='Courier'>backups/avant_rollback_&lt;horodatage&gt;.sql</font>), "
         "arrête l'app, recrée la base à vide, charge le dump, redémarre l'app. <b>Dépend de</b> : un fichier "
         "produit par <font face='Courier'>backup.py</font> — n'accepte pas les <font face='Courier'>.dump</font> "
         "de <font face='Courier'>reset_prod_database.sh</font>."),
        ("scripts/restore_dump_into_staging.sh &lt;fichier.dump&gt;", "Restaure dans la base <b>staging</b> (jamais en prod) un dump au format "
         "<font face='Courier'>-Fc</font> via <font face='Courier'>pg_restore --clean --if-exists</font>. "
         "<b>Dépend de</b> : le stack staging doit être démarré. <b>Appelé par</b> : "
         "<font face='Courier'>restore_latest_reset_backup_into_staging.sh</font>."),
        ("scripts/restore_latest_reset_backup_into_staging.sh", "Détecte automatiquement le fichier <font face='Courier'>backup_before_reset_*.dump</font> le "
         "plus récent (évite de taper son nom, risqué à la console Hetzner à cause des underscores) et appelle "
         "<font face='Courier'>restore_dump_into_staging.sh</font> avec ce chemin. <b>Dépend directement de</b> : "
         "un fichier déjà produit par <font face='Courier'>reset_prod_database.sh</font>."),
    ]))

    # ------------------------------------------------------------------
    story.append(Paragraph("6. Environnement staging", h1_style))
    story.append(script_table([
        ("scripts/refresh_staging_from_prod.sh", "Script principal de maintenance de l'environnement de test ISO prod : "
         "<font face='Courier'>git pull</font> puis reconstruction du stack staging "
         "(<font face='Courier'>docker compose -p staging ... up -d --build</font>), puis copie des données. Si "
         "la prod contient déjà de vraies données (produits + ventes &gt; 0), copie normale prod → staging "
         "(<font face='Courier'>pg_dump | pg_restore</font>) ; sinon, si un fichier "
         "<font face='Courier'>backup_before_reset_*.dump</font> existe, restaure celui-ci à la place (pour ne "
         "pas laisser staging vide juste après un <font face='Courier'>reset_prod_database.sh</font>). "
         "<b>Appelé automatiquement</b> chaque mois par une tâche cron. <b>Suivi par</b> : "
         "<font face='Courier'>verify_staging.sh</font>."),
        ("scripts/verify_staging.sh", "Vérifie que le rafraîchissement a fonctionné : affiche les utilisateurs et produits présents "
         "dans <font face='Courier'>staging-db-1</font>. <b>Dépend de</b> : le stack staging démarré et déjà "
         "rafraîchi une fois."),
    ]))

    # ------------------------------------------------------------------
    story.append(Paragraph("7. Génération de documentation PDF", h1_style))
    story.append(Paragraph(
        "Ces cinq scripts sont indépendants les uns des autres et ne dépendent d'aucun autre script de ce "
        "projet — seulement de la présence de <font face='Courier'>reportlab</font> et, pour le premier, du "
        "contenu de <font face='Courier'>FORMATION.md</font>. À relancer manuellement après toute mise à jour "
        "du contenu qu'ils reflètent.",
        body_style,
    ))
    story.append(script_table([
        ("scripts/generate_formation_slides_pdf.py", "Diaporama PDF (une diapo par page, paysage) condensé à partir de "
         "<font face='Courier'>FORMATION.md</font>, pour une présentation en réunion. "
         "<b>Dépend de</b> : le contenu de <font face='Courier'>FORMATION.md</font> (à tenir à jour en amont)."),
        ("scripts/generate_project_overview_pdf.py", "Présentation technique complète du projet (stack, architecture, tests, hébergement, "
         "sécurité), pensée comme support de préparation à un entretien."),
        ("scripts/generate_session_summary_pdf.py", "Récapitulatif figé d'une séance de travail précise (2026-09-15) — mise en place de l'accès "
         "pgAdmin à la vraie base de prod."),
        ("scripts/generate_staging_setup_pdf.py", "Explique, commande par commande, la mise en place de l'environnement staging + pgAdmin."),
        ("scripts/generate_test_scenario_pdf.py", "Scénario de test manuel couvrant crédit client, créances, sessions de caisse."),
    ]))

    # ------------------------------------------------------------------
    story.append(Paragraph("8. Ordre d'exécution selon le scénario", h1_style))

    story.append(Paragraph("8.1 — Déploiement initial sur un nouveau serveur", h2_style))
    story.append(Paragraph(
        "1. Configuration (<font face='Courier'>add_pgadmin_env_vars.sh</font>, "
        "<font face='Courier'>add_pgadmin_domain.sh</font> si pgAdmin voulu) → "
        "2. <font face='Courier'>docker compose up -d --build</font> (le schéma se crée automatiquement, "
        "<font face='Courier'>alembic upgrade head</font> tourne au démarrage du conteneur) → "
        "3. <font face='Courier'>seed_data.py</font> (comptes + démo, ou <font face='Courier'>--users-only</font> "
        "si aucune démo voulue) → 4. (si PC local) <font face='Courier'>register_backup_task.ps1</font> → "
        "5. <font face='Courier'>refresh_staging_from_prod.sh</font> puis <font face='Courier'>verify_staging."
        "sh</font> si un environnement de test est voulu.",
        body_style,
    ))

    story.append(Paragraph("8.2 — Vie courante", h2_style))
    story.append(Paragraph(
        "<font face='Courier'>backup.py</font> s'exécute seul, automatiquement, toutes les 4h. "
        "<font face='Courier'>refresh_staging_from_prod.sh</font> s'exécute seul, automatiquement, une fois par "
        "mois. Aucune action manuelle nécessaire tant que tout fonctionne normalement.",
        body_style,
    ))

    story.append(Paragraph("8.3 — Passage aux données réelles (fait le 2026-09-28)", h2_style))
    story.append(Paragraph(
        "1. <font face='Courier'>reset_prod_database.sh</font> (vide la prod, produit "
        "<font face='Courier'>backup_before_reset_*.dump</font>) → 2. (optionnel) "
        "<font face='Courier'>restore_latest_reset_backup_into_staging.sh</font> si on veut garder les données "
        "de démo consultables dans l'environnement de test plutôt que de les perdre au prochain "
        "rafraîchissement mensuel.",
        body_style,
    ))

    story.append(Paragraph("8.4 — Rollback en cas de problème", h2_style))
    story.append(Paragraph(
        "Selon l'origine du fichier de sauvegarde à restaurer : <font face='Courier'>restore_prod_from_backup."
        "sh</font> pour un fichier produit par <font face='Courier'>backup.py</font> (SQL brut) ; "
        "<font face='Courier'>pg_restore --clean --if-exists</font> manuel pour un fichier "
        "<font face='Courier'>-Fc</font> (produit par <font face='Courier'>reset_prod_database.sh</font>) qu'on "
        "voudrait exceptionnellement renvoyer en prod plutôt qu'en staging.",
        body_style,
    ))

    # ------------------------------------------------------------------
    story.append(Paragraph("9. Schéma des dépendances entre scripts", h1_style))
    story.append(Paragraph(
        "Les flèches indiquent \"produit un fichier consommé par\" ou \"appelle\" :",
        body_style,
    ))
    story.append(
        ListFlowable(
            [
                ListItem(Paragraph("<font face='Courier'>reset_prod_database.sh</font> → produit "
                                    "<font face='Courier'>backup_before_reset_*.dump</font> → consommé par "
                                    "<font face='Courier'>refresh_staging_from_prod.sh</font> (repli) <b>et</b> "
                                    "<font face='Courier'>restore_latest_reset_backup_into_staging.sh</font>.", explain_style)),
                ListItem(Paragraph("<font face='Courier'>restore_latest_reset_backup_into_staging.sh</font> → "
                                    "appelle → <font face='Courier'>restore_dump_into_staging.sh</font>.", explain_style)),
                ListItem(Paragraph("<font face='Courier'>reset_prod_database.sh</font> → appelle → "
                                    "<font face='Courier'>seed_data.py --users-only</font>.", explain_style)),
                ListItem(Paragraph("<font face='Courier'>backup.py</font> → produit un fichier "
                                    "<font face='Courier'>backups/*.sql</font> → seul consommateur : "
                                    "<font face='Courier'>restore_prod_from_backup.sh</font>.", explain_style)),
                ListItem(Paragraph("<font face='Courier'>register_backup_task.ps1</font> → planifie l'exécution "
                                    "récurrente de → <font face='Courier'>backup.py</font>.", explain_style)),
                ListItem(Paragraph("<font face='Courier'>refresh_staging_from_prod.sh</font> → suivi habituellement "
                                    "de → <font face='Courier'>verify_staging.sh</font>.", explain_style)),
                ListItem(Paragraph("Les scripts <font face='Courier'>generate_*_pdf.py</font> et "
                                    "<font face='Courier'>add_pgadmin_*.sh</font> n'ont aucune dépendance vers un "
                                    "autre script de ce projet.", explain_style)),
            ],
            bulletType="bullet",
            leftIndent=12,
        )
    )

    doc.build(story)
    print(f"PDF généré : {OUTPUT_PATH}")


if __name__ == "__main__":
    build()
