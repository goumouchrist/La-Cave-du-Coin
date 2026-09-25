"""Génère un PDF récapitulatif de la séance du 2026-09-15 : lancement local,
schéma relationnel, script factures ELABORATED, et surtout la mise en place
de l'accès pgAdmin à la vraie base de prod (contournement du bug clavier de
la console Hetzner).
Usage : .venv/Scripts/python.exe scripts/generate_session_summary_pdf.py
Produit Recapitulatif_session_2026-09-15.pdf à la racine du projet.
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

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "Recapitulatif_session_2026-09-15.pdf"

styles = getSampleStyleSheet()
title_style = ParagraphStyle("TitleFR", parent=styles["Title"], fontSize=18, spaceAfter=4)
subtitle_style = ParagraphStyle("SubtitleFR", parent=styles["Normal"], fontSize=10, textColor="#555555", spaceAfter=16)
h1_style = ParagraphStyle("H1FR", parent=styles["Heading1"], fontSize=14, spaceBefore=16, spaceAfter=8, textColor="#1a1a1a")
h2_style = ParagraphStyle("H2FR", parent=styles["Heading2"], fontSize=11.5, spaceBefore=10, spaceAfter=4, textColor="#1a1a1a")
body_style = ParagraphStyle("BodyFR", parent=styles["Normal"], fontSize=9.7, leading=14, spaceAfter=6)
cmd_style = ParagraphStyle("CmdFR", parent=styles["Normal"], fontName="Courier", fontSize=8.7, leading=12, textColor="#0a3d62")
explain_style = ParagraphStyle("ExplainFR", parent=styles["Normal"], fontSize=9, leading=12.5)
note_style = ParagraphStyle("NoteFR", parent=styles["Normal"], fontSize=9, leading=13, textColor="#7a4a00", spaceBefore=4, spaceAfter=6)


def cmd_table(rows):
    data = [[Paragraph("Commande / action", styles["Heading4"]), Paragraph("Ce que ça fait et pourquoi", styles["Heading4"])]]
    for cmd, explanation in rows:
        data.append([Paragraph(cmd, cmd_style), Paragraph(explanation, explain_style)])
    t = Table(data, colWidths=[70 * mm, 95 * mm])
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

    story.append(Paragraph("La Cave du Coin — Récapitulatif de la séance du 15/09/2026", title_style))
    story.append(Paragraph(
        "Ce qui a été fait aujourd'hui, dans l'ordre, pour pouvoir s'y retrouver plus tard.",
        subtitle_style,
    ))

    # ------------------------------------------------------------------
    story.append(Paragraph("1. Lancement du projet en local", h1_style))
    story.append(Paragraph(
        "Docker n'étant pas installé sur ce PC, l'application a été lancée en mode \"local classique\" "
        "(environnement virtuel Python + base SQLite), le chemin déjà validé dans le README.",
        body_style,
    ))
    story.append(cmd_table([
        ("./.venv/Scripts/python.exe -m alembic upgrade head", "Applique les migrations de schéma (crée/met à jour les tables) sur la base SQLite locale."),
        ("./.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload",
         "Démarre le serveur web local. \"--reload\" relance automatiquement le serveur si le code change. "
         "Accessible ensuite sur http://127.0.0.1:8000 (interface) et /docs (API)."),
    ]))
    story.append(Paragraph(
        "Pour arrêter : Ctrl+C dans le terminal où le serveur tourne.",
        note_style,
    ))

    # ------------------------------------------------------------------
    story.append(Paragraph("2. Schéma relationnel de la base", h1_style))
    story.append(Paragraph(
        "Un schéma relationnel complet (12 tables : users, products, sales, cash_sessions, customers...) "
        "a été extrait du code (<font face='Courier'>app/models.py</font>) et écrit dans "
        "<font face='Courier'>schema.sql</font> à la racine du projet — un DDL PostgreSQL de référence, "
        "purement documentaire (les vraies tables sont créées par Alembic, pas par ce fichier).",
        body_style,
    ))

    # ------------------------------------------------------------------
    story.append(Paragraph("3. Réflexion sur le \"nettoyage\" de la base de prod", h1_style))
    story.append(Paragraph(
        "Un script existant, <font face='Courier'>scripts/reset_prod_database.sh</font>, permettrait de "
        "vider entièrement la prod (sauvegarde automatique avant, puis TRUNCATE de toutes les tables, "
        "puis recréation des seuls comptes par défaut). <b>Décision : ne pas l'exécuter pour l'instant</b> "
        "— une seule ligne \"parasite\" à zéro a été repérée dans l'historique des sessions de caisse du "
        "compte manager, jugée sans conséquence. Elle peut être supprimée plus tard avec un simple "
        "<font face='Courier'>DELETE FROM cash_sessions WHERE id = &lt;id&gt;;</font> ciblé si besoin, "
        "plutôt qu'un reset complet.",
        body_style,
    ))

    # ------------------------------------------------------------------
    story.append(Paragraph("4. Accès pgAdmin à la vraie base de production", h1_style))
    story.append(Paragraph(
        "C'est le morceau principal de la séance. pgAdmin existait déjà (mis en place lors d'une séance "
        "précédente, cf. <font face='Courier'>Mise_en_place_environnement_staging.pdf</font>) mais ne "
        "voyait que la base de <b>staging</b>. Objectif : qu'il puisse aussi interroger la vraie prod, "
        "sans jamais avoir besoin de SSH ou de taper du SQL brut dans la console.",
        body_style,
    ))

    story.append(Paragraph("5.1 — Modification du code (faite ici, sur ce PC)", h2_style))
    story.append(Paragraph(
        "Dans <font face='Courier'>docker-compose.yml</font>, le service <font face='Courier'>db</font> "
        "de la prod a été ajouté au réseau Docker partagé <font face='Courier'>caddy-net</font> (déjà "
        "utilisé par Caddy et pgAdmin), sous l'alias <font face='Courier'>proddb</font> — un nom "
        "différent du <font face='Courier'>db</font> de staging pour éviter toute collision. Il reste "
        "aussi sur son réseau habituel, donc l'application prod continue de le joindre normalement. "
        "Commit <font face='Courier'>f41df95</font>, poussé sur GitHub (branche main).",
        body_style,
    ))

    story.append(Paragraph("5.2 — Application sur le serveur (VPS)", h2_style))
    story.append(cmd_table([
        ("git pull", "Récupère la modification de docker-compose.yml depuis GitHub."),
        ("./scripts/add_pgadmin_domain.sh", "Script déjà présent qui ajoute PGADMIN_DOMAIN au .env de prod sans risquer une faute de "
         "frappe sur le \"_\". Ici, déjà fait lors d'une séance précédente (\"rien à faire\")."),
        ("docker compose up -d --build", "Relance le stack prod (db, app, caddy) en tenant compte du nouveau réseau — db rejoint "
         "caddy-net sous l'alias proddb."),
        ("docker compose -p staging --env-file .env.staging -f docker-compose.yml -f docker-compose.staging.yml up -d",
         "Relance aussi le stack staging par sécurité, pour confirmer que tout communique bien."),
    ]))

    story.append(Paragraph("5.3 — Incident : compte pgAdmin verrouillé", h2_style))
    story.append(Paragraph(
        "En essayant de se connecter à pgAdmin, le compte s'est retrouvé verrouillé (trop de tentatives "
        "avec un mot de passe qui ne correspondait plus). Comme pgAdmin ne crée son compte admin qu'au "
        "tout premier démarrage de son volume de données, la solution a été de repartir d'un volume "
        "neuf :",
        body_style,
    ))
    story.append(cmd_table([
        ("docker volume ls", "Liste tous les volumes Docker pour repérer le nom exact de celui de pgAdmin "
         "(staging_pgadmin_data)."),
        ("docker compose -p staging ... stop pgadmin", "Arrête le conteneur pgAdmin (sans le supprimer, ce qui viendra ensuite)."),
        ("docker compose -p staging ... rm -f pgadmin", "Supprime le conteneur arrêté — nécessaire car Docker refuse de supprimer un volume tant "
         "qu'un conteneur (même arrêté) y fait encore référence."),
        ("docker volume rm staging_pgadmin_data", "Supprime le volume : pgAdmin va tout recréer de zéro (compte admin inclus) au prochain "
         "démarrage, avec les identifiants actuels de .env.staging."),
        ("docker compose -p staging ... up -d pgadmin", "Redémarre pgAdmin sur un volume neuf → nouveau compte admin fonctionnel."),
    ]))

    story.append(Paragraph("5.4 — Enregistrement des deux bases dans pgAdmin", h2_style))
    story.append(Paragraph(
        "Depuis le navigateur (https://pgadmin.lacaveducoin.com), \"Register → Server\" a été fait deux fois :",
        body_style,
    ))
    story.append(
        ListFlowable(
            [
                ListItem(Paragraph(
                    "<b>Serveur \"Prod\"</b> : host <font face='Courier'>proddb</font>, port 5432, base/"
                    "utilisateur <font face='Courier'>cave_du_coin</font>, mot de passe = "
                    "<font face='Courier'>POSTGRES_PASSWORD</font> du <font face='Courier'>.env</font> "
                    "de <b>production</b>.", explain_style)),
                ListItem(Paragraph(
                    "<b>Serveur \"Staging\"</b> : host <font face='Courier'>db</font> (même stack que "
                    "pgAdmin, pas besoin d'alias), même port/base/utilisateur, mot de passe = celui de "
                    "<font face='Courier'>.env.staging</font>.", explain_style)),
            ],
            bulletType="bullet",
            leftIndent=12,
        )
    )
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Résultat : les deux mots de passe générés (<font face='Courier'>POSTGRES_PASSWORD</font>) se "
        "trouvent être des chaînes hexadécimales pures (chiffres et lettres a-f uniquement) — donc "
        "aucun caractère à risque, lisibles et retapables directement à l'écran de la console sans "
        "aucun contournement.",
        body_style,
    ))

    # ------------------------------------------------------------------
    story.append(Paragraph("5. Le bug clavier de la console Hetzner (rappel)", h1_style))
    story.append(Paragraph(
        "La console web du VPS ignore systématiquement la touche <b>Shift</b> à la frappe (et au collage), "
        "quel que soit le clavier physique (AZERTY ou QWERTY) — ce n'est pas une question de touche, "
        "c'est la console elle-même qui ne transmet pas le modificateur Shift. Concrètement : "
        "<font face='Courier'>_</font> devient <font face='Courier'>-</font>, "
        "<font face='Courier'>|</font> devient <font face='Courier'>\\</font>, etc.",
        body_style,
    ))
    story.append(Paragraph(
        "Astuce découverte aujourd'hui pour taper un underscore malgré tout, sans utiliser Shift : "
        "construire le caractère via son code octal (95 = <font face='Courier'>_</font>), avec des "
        "caractères tous confirmés \"sûrs\" (lettres, chiffres, guillemet simple, backtick) :",
        body_style,
    ))
    story.append(cmd_table([
        ("`printf '\\137'`", "S'exécute et produit littéralement un \"_\" à l'endroit où c'est inséré. "
         "Exemple complet : docker compose exec db psql -U cave`printf '\\137'`du`printf '\\137'`coin "
         "-d cave`printf '\\137'`du`printf '\\137'`coin"),
        ("Touche Tab (autocomplétion)", "Une fois dans psql, taper un début de nom (ex: \"cash\") puis Tab complète le reste "
         "(\"cash_sessions\") sans jamais appuyer sur la touche _ — marche aussi pour les noms de "
         "fichiers/dossiers dans le shell."),
        ("echo test_test", "Test rapide à faire avant toute commande importante contenant un \"_\", pour vérifier si le "
         "bug est actif ce jour-là (résultat attendu si bug : test-test ou testtest)."),
    ]))
    story.append(Paragraph(
        "Si la commande à taper reste trop complexe malgré ces astuces (beaucoup de \"_\", \"@\", \"(\"...), "
        "le plus fiable reste un vrai terminal SSH depuis un autre appareil/réseau (téléphone en partage "
        "de connexion, PC personnel) — la console Hetzner n'est qu'un filet de secours quand SSH direct "
        "n'est pas disponible.",
        note_style,
    ))

    # ------------------------------------------------------------------
    story.append(Paragraph("6. Où retrouver les identifiants", h1_style))
    story.append(cmd_table([
        ("grep POSTGRES .env", "Sur le VPS, depuis /opt/La_Cave_du_Coin : mot de passe de la vraie base de prod "
         "(POSTGRES_PASSWORD)."),
        ("grep POSTGRES .env.staging", "Mot de passe de la base de staging."),
        ("grep PGADMIN .env.staging", "Email et mot de passe pour se connecter à l'interface pgAdmin elle-même."),
    ]))
    story.append(Paragraph(
        "Aucun de ces fichiers n'est sur GitHub (exclus via .gitignore) — ils n'existent que sur le VPS.",
        note_style,
    ))

    # ------------------------------------------------------------------
    story.append(Paragraph("7. Ce qui reste à faire", h1_style))
    story.append(
        ListFlowable(
            [
                ListItem(Paragraph("Changer les mots de passe par défaut des comptes de démo "
                                    "(admin/Admin123!, manager/Manager123!, caissier/Caissier123!) avant "
                                    "un vrai usage commercial.", explain_style)),
                ListItem(Paragraph("Vérifier que PGADMIN_DEFAULT_PASSWORD n'est plus la valeur par défaut "
                                    "ChangeMePgAdmin123 — pgAdmin donnant maintenant accès à la vraie prod, "
                                    "un mot de passe faible ici expose directement la production.", explain_style)),
                ListItem(Paragraph("Vérifier/révoquer le jeton GitHub (PAT) créé pour cloner le dépôt privé "
                                    "sur le VPS, s'il n'est plus utile.", explain_style)),
            ],
            bulletType="bullet",
            leftIndent=12,
        )
    )

    doc.build(story)
    print(f"PDF généré : {OUTPUT_PATH}")


if __name__ == "__main__":
    build()
