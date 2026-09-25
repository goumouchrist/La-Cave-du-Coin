"""Génère un PDF de présentation technique complète du projet La Cave du Coin,
pensé comme support de préparation à un entretien (stack, architecture, tests,
hébergement, staging, sauvegardes, sécurité, limites connues).
Usage : .venv/Scripts/python.exe scripts/generate_project_overview_pdf.py
Produit La_Cave_du_Coin_Presentation_Technique.pdf à la racine du projet.
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

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "La_Cave_du_Coin_Presentation_Technique.pdf"

styles = getSampleStyleSheet()
title_style = ParagraphStyle("TitleFR", parent=styles["Title"], fontSize=19, spaceAfter=4)
subtitle_style = ParagraphStyle("SubtitleFR", parent=styles["Normal"], fontSize=10, textColor="#555555", spaceAfter=18)
h1_style = ParagraphStyle("H1FR", parent=styles["Heading1"], fontSize=14.5, spaceBefore=18, spaceAfter=8, textColor="#1a1a1a")
h2_style = ParagraphStyle("H2FR", parent=styles["Heading2"], fontSize=11.5, spaceBefore=10, spaceAfter=4, textColor="#1a1a1a")
body_style = ParagraphStyle("BodyFR", parent=styles["Normal"], fontSize=9.7, leading=14, spaceAfter=6)
cmd_style = ParagraphStyle("CmdFR", parent=styles["Normal"], fontName="Courier", fontSize=8.5, leading=12, textColor="#0a3d62")
explain_style = ParagraphStyle("ExplainFR", parent=styles["Normal"], fontSize=9, leading=12.5)
note_style = ParagraphStyle("NoteFR", parent=styles["Normal"], fontSize=9, leading=13, textColor="#7a4a00", spaceBefore=4, spaceAfter=6)
pitch_style = ParagraphStyle("PitchFR", parent=styles["Normal"], fontSize=9.5, leading=13.5, textColor="#1a1a1a", spaceAfter=6, backColor="#f5f0e2", borderPadding=8)


def two_col_table(headers, rows, col_widths):
    data = [[Paragraph(h, styles["Heading4"]) for h in headers]]
    for row in rows:
        data.append([Paragraph(cell, explain_style if i > 0 else cmd_style) for i, cell in enumerate(row)])
    t = Table(data, colWidths=col_widths)
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


def bullets(items):
    return ListFlowable(
        [ListItem(Paragraph(t, explain_style)) for t in items],
        bulletType="bullet",
        leftIndent=12,
    )


def build() -> None:
    doc = SimpleDocTemplate(
        str(OUTPUT_PATH), pagesize=A4,
        topMargin=16 * mm, bottomMargin=16 * mm, leftMargin=16 * mm, rightMargin=16 * mm,
    )
    story = []

    story.append(Paragraph("La Cave du Coin — Présentation technique du projet", title_style))
    story.append(Paragraph(
        "Application de caisse et de gestion de stock pour un commerce de boissons, développée en solo, "
        "de la conception à l'hébergement en production réelle. Document préparé comme support d'entretien "
        "technique (stack, architecture, tests, infrastructure).",
        subtitle_style,
    ))

    # ------------------------------------------------------------------
    story.append(Paragraph("1. Contexte et objectif", h1_style))
    story.append(Paragraph(
        "La Cave du Coin est un commerce de boissons (Conakry, Guinée) qui avait besoin d'un logiciel de "
        "caisse et de suivi de stock adapté à sa réalité : plusieurs modes de paiement locaux (mobile money, "
        "vente à crédit informelle), un besoin fort de traçabilité anti-fraude (personnel non permanent), et "
        "une contrainte de coût (hébergement bon marché, pas de licence logicielle). Le projet couvre "
        "l'ensemble du cycle : conception du schéma de données, API, interface web, tests automatisés, "
        "containerisation, déploiement, environnement de staging et sauvegardes.",
        body_style,
    ))

    # ------------------------------------------------------------------
    story.append(Paragraph("2. Stack technique", h1_style))
    story.append(two_col_table(
        ["Domaine", "Choix", "Rôle"],
        [
            ("Langage / runtime", "Python 3.12", "Backend complet"),
            ("Framework web", "FastAPI 0.115 (+ Uvicorn ASGI)", "API REST + rendu des pages HTML (Jinja2)"),
            ("ORM", "SQLAlchemy 2.0 (style déclaratif Mapped[...])", "Modélisation des tables, requêtes"),
            ("Migrations", "Alembic 1.14", "Versionner le schéma de base sans perte de données"),
            ("Validation / schémas", "Pydantic v2 + pydantic-settings", "Validation des entrées API, config via .env"),
            ("Base de données", "SQLite (dev/tests) -> PostgreSQL 16 (prod)", "Changement via une seule variable DATABASE_URL, zéro changement de code"),
            ("Auth", "PyJWT + passlib/bcrypt", "Jetons de session, hachage des mots de passe"),
            ("PDF", "reportlab + qrcode", "Reçus, devis, étiquettes produits, ce document"),
            ("Email", "smtplib (service mail.py)", "Envoi de reçus par email"),
            ("Frontend", "Jinja2 (templates serveur) + JS natif + Chart.js (CDN)", "Pas de framework JS : simplicité, pas de build step"),
            ("Tests", "pytest + httpx (TestClient FastAPI)", "161 tests, unitaires et intégration HTTP"),
            ("Conteneurisation", "Docker (python:3.12-slim) + Docker Compose", "Packaging et orchestration reproductible"),
            ("Reverse proxy / HTTPS", "Caddy 2", "HTTPS automatique (Let's Encrypt) sans configuration manuelle"),
            ("Hébergement", "VPS Hetzner (CX22, ~4,5 €/mois)", "Production réelle"),
            ("CI/CD", "Aucune (volontairement assumé, voir section 9)", "Tests et déploiement lancés manuellement"),
        ],
        [40 * mm, 68 * mm, 57 * mm],
    ))

    # ------------------------------------------------------------------
    story.append(Paragraph("3. Architecture applicative : séparation en couches", h1_style))
    story.append(Paragraph(
        "Le code applicatif (<font face='Courier'>app/</font>) suit une séparation stricte en quatre couches, "
        "pensée pour que la logique métier ne dépende jamais du framework web — donc testable en pur Python :",
        body_style,
    ))
    story.append(bullets([
        "<font face='Courier'>models.py</font> — les entités ORM (User, Product, Sale/SaleItem, Quote/QuoteItem, "
        "CashSession, Customer, StockMovement, Return, Log...) et les énumérations métier (rôles, modes de "
        "paiement, statuts).",
        "<font face='Courier'>schemas.py</font> — les schémas Pydantic, avec une séparation nette entre schémas "
        "d'entrée (<i>Create</i>) et de sortie (<i>Out</i>, avec <font face='Courier'>from_attributes=True</font> "
        "pour sérialiser directement les objets ORM en JSON).",
        "<font face='Courier'>services/*.py</font> — toute la logique métier (créer une vente, valider un "
        "mouvement de stock, convertir un devis...). Chaque fonction reçoit une session SQLAlchemy en paramètre "
        "et lève des exceptions métier dédiées (ex. <font face='Courier'>InsufficientStockError</font>, "
        "<font face='Courier'>CashSessionClosedError</font>) plutôt que de manipuler des codes HTTP.",
        "<font face='Courier'>routers/*.py</font> — la couche FastAPI, volontairement fine : authentification, "
        "appel du service correspondant, traduction des exceptions métier en codes HTTP (422/403/404/409), "
        "et écriture systématique dans le journal d'audit (<font face='Courier'>logs_service.record(...)</font>).",
    ]))
    story.append(Paragraph(
        "<b>Bénéfice concret :</b> les règles métier (calcul de monnaie, seuils anti-fraude, limite de crédit...) "
        "sont testées directement en appelant les fonctions de <font face='Courier'>services/</font> avec une "
        "base SQLite en mémoire, sans jamais démarrer de serveur HTTP — tests rapides et ciblés.",
        note_style,
    ))

    # ------------------------------------------------------------------
    story.append(Paragraph("4. Fonctionnalités métier principales", h1_style))
    story.append(bullets([
        "<b>Caisse / ventes</b> : panier, scan code-barres, plusieurs modes de paiement (espèces, mobile money, "
        "crédit, avoir, paycard...), calcul automatique de la monnaie, sessions de caisse (fond initial, écart "
        "théorique/physique, blocage automatique si écart &gt; seuil).",
        "<b>Stock</b> : mouvements (entrée, casse, don, ajustement) avec <b>double validation obligatoire</b> "
        "par une personne différente de celle qui saisit, conversions carton/pack/unité automatiques, import "
        "CSV en masse, alertes de rupture prévisionnelle. Un ajustement peut être négatif (manque constaté au "
        "comptage) — tous les autres mouvements restent strictement positifs.",
        "<b>Péremption par lot (FEFO)</b> : chaque entrée de stock peut porter sa propre date de péremption "
        "(plusieurs livraisons du même produit peuvent coexister avec des dates différentes), y compris via "
        "l'import CSV en masse. La quantité restante par lot est <b>dérivée</b>, jamais stockée, en répartissant "
        "la consommation totale sur les lots du plus proche de la péremption au plus lointain — alertes "
        "automatiques sur le tableau de bord.",
        "<b>Fiche d'inventaire à l'aveugle</b> : PDF listant les produits actifs avec des colonnes vides à "
        "remplir à la main, <b>sans afficher le stock théorique</b> — pensé pour un comptage physique fiable "
        "par une tierce personne, sans biais.",
        "<b>Clients</b> : vente à crédit (avec limite de créances simultanées par client), avoir suite à un "
        "retour, règlements partiels avec allocation à la dette la plus ancienne.",
        "<b>Devis</b> : créer un devis sans avoir besoin d'une session de caisse ouverte, prix figé au moment "
        "de la création, conversion en vente réelle en un clic (réutilise toute la logique de vente : stock, "
        "paiement, anti-fraude), PDF dédié. Numéro court et non-ambigu (ex. <font face='Courier'>DEV-A7K9M</font>) "
        "scannable directement via le QR code imprimé ; nom et téléphone du client obligatoires à la création "
        "pour permettre de retrouver un devis par recherche si le client perd son numéro.",
        "<b>Tableau de bord \"Aujourd'hui\"</b> : indicateurs du jour (CA, ventes, devis, mouvements de stock, "
        "écarts de caisse) — tuiles avec accent coloré par métrique et animation de comptage à chaque "
        "rafraîchissement — plus un camembert des produits vendus et un flux d'activité chronologique, "
        "construits à partir du journal d'audit existant, rafraîchis automatiquement toutes les 15 secondes "
        "(voir section 8 sur ce choix).",
        "<b>Statistiques / prévisions</b> : top produits, ventilation par catégorie/caissier, prévision de "
        "chiffre d'affaires par régression linéaire simple, prévision de rupture de stock.",
        "<b>Documents PDF</b> : reçus et devis au format ticket thermique (80 mm) avec QR code, étiquettes "
        "produit, reçus de règlement de créance, fiche d'inventaire.",
    ]))

    # ------------------------------------------------------------------
    story.append(Paragraph("5. Règles anti-fraude (le fil rouge du projet)", h1_style))
    story.append(Paragraph(
        "Un point volontairement mis en avant à chaque évolution du projet : chaque nouvelle fonctionnalité est "
        "systématiquement passée au filtre \"est-ce que ça ouvre une brèche anti-fraude ?\" avant d'être "
        "considérée terminée (voir section 10 pour un exemple concret découvert sur la fonctionnalité devis).",
        body_style,
    ))
    story.append(two_col_table(
        ["Règle", "Seuil / mécanisme"],
        [
            ("Annulation d'un ticket par un caissier", "possible seulement dans les 5 min suivant la vente, motif obligatoire"),
            ("Annulation par un manager/admin", "possible à tout moment"),
            ("Vente/devis de plusieurs articles identiques", "confirmation manuelle au-delà de 5 unités du même produit"),
            ("Double scan du même produit", "alerte si moins de 2 secondes entre deux scans"),
            ("Écart de caisse à la fermeture", "session bloquée si écart &gt; 10 000 GNF, déblocage par un manager avec commentaire obligatoire"),
            ("Mouvement de stock hors vente", "doit être validé par une personne différente de celle qui l'a saisi"),
            ("Ajustement d'inventaire", "validation réservée à un Admin/Super Admin"),
            ("Vente à crédit non réglée", "maximum 2 créances en cours par client, sinon vente refusée"),
            ("Prix de vente d'un produit", "ne peut pas descendre sous le prix d'achat - 5 %, sauf marqué \"promo\""),
            ("Réimpression d'un reçu/devis", "automatiquement marquée DUPLICATA"),
            ("Toute action", "journalisée (qui, quoi, quand, IP) dans un journal d'audit jamais supprimé"),
        ],
        [72 * mm, 93 * mm],
    ))

    # ------------------------------------------------------------------
    story.append(Paragraph("6. Base de données et migrations", h1_style))
    story.append(Paragraph(
        "SQLite en développement/tests, PostgreSQL 16 en production — le changement de moteur ne touche aucune "
        "ligne de code applicatif, uniquement la variable d'environnement <font face='Courier'>DATABASE_URL</font> "
        "(configuration via <font face='Courier'>pydantic-settings</font>).",
        body_style,
    ))
    story.append(Paragraph(
        "Toutes les évolutions de schéma passent par Alembic (jamais de <font face='Courier'>create_all()</font> "
        "en production). Point technique notable : SQLite ne supporte pas nativement <font face='Courier'>ALTER "
        "TABLE</font> pour toutes les opérations, donc les migrations qui modifient une table existante utilisent "
        "le mode <font face='Courier'>batch_alter_table</font> d'Alembic (recréation de table en coulisse), "
        "activé conditionnellement selon le dialecte (SQLite uniquement, pas nécessaire sur PostgreSQL). Les "
        "migrations qui créent des tables neuves (ex. <font face='Courier'>quotes</font>/<font face='Courier'>"
        "quote_items</font>) utilisent directement <font face='Courier'>op.create_table(...)</font>. Les "
        "migrations sont appliquées automatiquement au démarrage du conteneur (<font face='Courier'>alembic "
        "upgrade head &amp;&amp; uvicorn ...</font> dans le Dockerfile).",
        body_style,
    ))

    # ------------------------------------------------------------------
    story.append(Paragraph("7. Stratégie de tests — 161 tests", h1_style))
    story.append(Paragraph(
        "La suite mélange volontairement deux niveaux, souvent dans un même fichier :",
        body_style,
    ))
    story.append(bullets([
        "<b>Tests unitaires (couche service)</b> : appellent directement les fonctions de "
        "<font face='Courier'>services/</font> avec une base SQLite <b>en mémoire</b> (fixture "
        "<font face='Courier'>db_session</font>), sans passer par HTTP — rapides, ciblés sur une règle métier "
        "précise.",
        "<b>Tests d'intégration HTTP</b> : passent par un vrai <font face='Courier'>TestClient</font> FastAPI "
        "(fixture <font face='Courier'>client</font>) avec une authentification JWT réelle obtenue via "
        "<font face='Courier'>/api/auth/login</font> (fixture <font face='Courier'>auth_headers</font>) — "
        "valident le comportement de bout en bout, y compris les codes HTTP retournés.",
    ]))
    story.append(two_col_table(
        ["Domaine testé", "Fichier(s)"],
        [
            ("Règles anti-fraude transverses (annulation, double scan)", "test_antifraude_rules.py"),
            ("Ventes, reçus PDF, emails de reçu", "test_sales_and_receipts.py"),
            ("Sessions de caisse (ouverture/fermeture/écarts/résolution)", "test_cash_sessions.py"),
            ("Retours, avoir, crédit client, créances", "test_returns_and_credit.py, test_customer_credit.py"),
            ("Devis (création, conversion, expiration, recherche client, anti-fraude)", "test_quotes.py (16 tests)"),
            ("Tableau de bord \"Aujourd'hui\"", "test_today_dashboard.py (4 tests)"),
            ("Fiche d'inventaire à l'aveugle", "test_inventory_sheet.py (4 tests)"),
            ("Stock : conversions, marges, double validation, ajustement négatif, lots FEFO", "test_products_stock_conversions.py"),
            ("Import CSV (produits, mouvements de stock)", "test_product_import.py, test_movement_import.py"),
            ("Fournisseurs, étiquettes/codes-barres produits", "test_suppliers.py, test_product_labels.py"),
            ("Authentification, rôles, gestion des mots de passe", "test_auth_permissions.py, test_password_management.py"),
            ("Super Admin (gestion des comptes Admin)", "test_super_admin.py"),
            ("Prévisions (régression linéaire, rupture de stock, alertes de péremption)", "test_predictions.py"),
            ("Sauvegardes (SQLite, rétention, copie offsite)", "test_backup.py"),
            ("Envoi d'emails (SMTP)", "test_mail.py"),
        ],
        [90 * mm, 75 * mm],
    ))
    story.append(Paragraph(
        "Exécution : <font face='Courier'>pytest</font> (configuration minimale via <font face='Courier'>pytest.ini</font>, "
        "aucun marqueur personnalisé). Aucune CI ne les exécute automatiquement — voir section 9.",
        body_style,
    ))

    # ------------------------------------------------------------------
    story.append(Paragraph("8. Hébergement, containerisation et mise en production", h1_style))
    story.append(Paragraph(
        "L'application est packagée dans une image Docker unique (<font face='Courier'>python:3.12-slim</font>) "
        "et orchestrée via Docker Compose, avec des fichiers <b>combinables</b> plutôt qu'un seul fichier "
        "monolithique — le même code sert trois contextes différents :",
        body_style,
    ))
    story.append(two_col_table(
        ["Fichier", "Rôle"],
        [
            ("docker-compose.yml", "Base commune : service db (Postgres 16) + app (build de l'image). Toujours utilisé."),
            ("docker-compose.vps.yml", "Overlay production : ajoute Caddy (reverse proxy + HTTPS automatique via Let's Encrypt)."),
            ("docker-compose.lan.yml", "Overlay alternatif : expose juste le port 8000 sur le réseau local (PC boutique, sans HTTPS)."),
            ("docker-compose.staging.yml", "Overlay staging : ports liés uniquement à 127.0.0.1 (jamais exposés publiquement), ajoute pgAdmin."),
        ],
        [55 * mm, 110 * mm],
    ))
    story.append(Paragraph(
        "Le choix se fait via la variable <font face='Courier'>COMPOSE_FILE</font> dans <font face='Courier'>.env</font> "
        "(prod = <font face='Courier'>docker-compose.yml:docker-compose.vps.yml</font>). Le staging tourne comme un "
        "<b>projet Compose séparé</b> (<font face='Courier'>-p staging</font>), avec sa propre base et ses propres "
        "volumes, isolé de la prod, mais partage le réseau Docker <font face='Courier'>caddy-net</font> avec elle "
        "pour que Caddy puisse router vers son pgAdmin.",
        body_style,
    ))
    story.append(Paragraph(
        "Mise en production : VPS Hetzner (Ubuntu, ~4,5 €/mois), pare-feu UFW n'autorisant que SSH/80/443. "
        "Déploiement d'une mise à jour : <font face='Courier'>git pull &amp;&amp; docker compose up -d --build</font> "
        "(les migrations Alembic s'appliquent automatiquement au démarrage du conteneur). Aucun nom de domaine "
        "acheté n'était nécessaire pour obtenir un certificat HTTPS valide (via sslip.io, qui encode l'IP dans "
        "un sous-domaine) avant l'achat éventuel d'un vrai domaine.",
        body_style,
    ))
    story.append(Paragraph(
        "Choix délibéré sur le tableau de bord \"Aujourd'hui\" (section 4) : rafraîchissement par "
        "<font face='Courier'>setInterval</font> côté JS toutes les 15 secondes plutôt que des websockets. Le "
        "besoin réel (un commerce, quelques mouvements par minute au plus) ne justifiait pas la complexité "
        "d'infrastructure supplémentaire (connexions persistantes, gestion de la reconnexion...) — ce même "
        "pattern de rafraîchissement périodique existait déjà sur la page de suivi de caisse.",
        note_style,
    ))
    story.append(Paragraph(
        "Problème réel rencontré et corrigé : les fichiers CSS/JS étaient référencés par un chemin statique, "
        "donc les navigateurs continuaient de servir une version en cache après chaque déploiement (jusqu'à un "
        "hard refresh manuel). Corrigé avec un <b>cache-busting</b> simple : une variable "
        "<font face='Courier'>static_version</font> (l'heure de démarrage du process) injectée en paramètre "
        "<font face='Courier'>?v=</font> sur chaque <font face='Courier'>&lt;link&gt;</font>/<font face='Courier'>"
        "&lt;script&gt;</font> via un global Jinja2 — change automatiquement à chaque redémarrage de conteneur, "
        "donc à chaque déploiement, sans action manuelle.",
        body_style,
    ))

    # ------------------------------------------------------------------
    story.append(Paragraph("9. Environnement de staging et refresh automatique depuis la prod", h1_style))
    story.append(Paragraph(
        "Un environnement de <b>staging</b> tourne en parallèle de la prod sur le même VPS (même code, base et "
        "ports isolés). Un script (<font face='Courier'>scripts/refresh_staging_from_prod.sh</font>), planifié "
        "par cron le <b>1er de chaque mois à 2h du matin</b>, le resynchronise automatiquement :",
        body_style,
    ))
    story.append(bullets([
        "<font face='Courier'>git pull</font> puis redémarrage du stack staging avec la dernière version du code.",
        "Vérifie si la prod contient de vraies données (<font face='Courier'>COUNT(products)+COUNT(sales)</font>) : "
        "si oui, <font face='Courier'>pg_dump -Fc</font> de la vraie prod, restauré dans staging via "
        "<font face='Courier'>pg_restore --clean --if-exists</font>.",
        "Si la prod est encore vide (avant lancement commercial), restaure un jeu de données de démonstration "
        "à la place — le staging n'est jamais vide, même en phase de pré-lancement.",
    ]))
    story.append(Paragraph(
        "Un <b>pgAdmin</b> dédié (accessible en HTTPS via Caddy sur un sous-domaine séparé) permet d'explorer "
        "visuellement les deux bases — prod <b>et</b> staging — sans jamais avoir besoin de SSH ni de taper de "
        "SQL brut en console. Pour cela, la base de production a été jointe au réseau Docker partagé "
        "<font face='Courier'>caddy-net</font> sous un alias dédié (<font face='Courier'>proddb</font>, distinct "
        "du <font face='Courier'>db</font> de staging pour éviter toute collision de nom) — uniquement pour que "
        "pgAdmin puisse s'y connecter ; l'application de prod continue, elle, de joindre sa base normalement, "
        "sans changement de comportement.",
        body_style,
    ))
    story.append(Paragraph(
        "Point de vigilance identifié et documenté : ce refresh mensuel copie de <b>vraies données clients</b> "
        "(noms, téléphones, adresses, soldes) dans staging. Jugé acceptable dans ce contexte précis (structure "
        "mono-propriétaire, pas de tiers y ayant accès), mais l'accès à l'environnement de staging doit rester "
        "soumis à la même rigueur que la production — bon exemple de compromis pragmatique documenté plutôt "
        "qu'ignoré.",
        note_style,
    ))

    # ------------------------------------------------------------------
    story.append(Paragraph("10. Sauvegardes et sécurité", h1_style))
    story.append(Paragraph(
        "<b>Sauvegardes</b> : <font face='Courier'>scripts/backup.py</font>, exécuté toutes les 4h via cron. "
        "Dump PostgreSQL (<font face='Courier'>pg_dump</font> dans le conteneur) ou copie de fichier pour SQLite "
        "selon l'environnement. Rétention configurable (14 jours par défaut, purge automatique des sauvegardes "
        "plus anciennes), copie optionnelle vers un stockage hors-site (non bloquant si indisponible).",
        body_style,
    ))
    story.append(Paragraph(
        "<b>Sécurité</b> : mots de passe hachés (bcrypt via passlib, jamais stockés en clair), sessions "
        "authentifiées par JWT à durée limitée, quatre rôles hiérarchiques (Caissier &lt; Manager &lt; Admin &lt; "
        "Super Admin) contrôlés par une dépendance FastAPI unique (<font face='Courier'>require_role(*roles)</font>) "
        "réutilisée sur chaque endpoint sensible, séparation des tâches sur les mouvements de stock (voir section "
        "5), et journal d'audit exhaustif pour toute action mutante — la même table de logs qui sert désormais "
        "de base au tableau de bord \"Aujourd'hui\".",
        body_style,
    ))

    # ------------------------------------------------------------------
    story.append(Paragraph("11. Un exemple concret d'itération avec revue anti-fraude", h1_style))
    story.append(Paragraph(
        "Bon exemple à raconter en entretien pour illustrer une hygiène d'ingénierie, pas juste \"livrer une "
        "fonctionnalité qui marche\" : lors de l'ajout des devis, la règle anti-fraude \"confirmation "
        "obligatoire au-delà de 5 articles identiques\" (déjà appliquée aux ventes) avait été <b>oubliée</b> à "
        "la création d'un devis. Comme la conversion d'un devis en vente forçait cette confirmation à "
        "<font face='Courier'>True</font> par construction, un devis de 50 unités identiques pouvait se "
        "convertir en vente sans jamais déclencher le contrôle. Le trou a été identifié en repensant le "
        "flux réel d'usage (\"un client repart chercher du cash, on met sa vente en attente\"), corrigé "
        "(la même vérification s'applique désormais aussi à la création d'un devis), testé, puis documenté "
        "dans le guide de formation de l'équipe.",
        body_style,
    ))
    story.append(Paragraph(
        "<b>Second exemple, découvert en répondant à une question opérationnelle concrète</b> (\"comment "
        "valider un inventaire en cas de manque constaté ?\") plutôt qu'en relisant le code à froid : le champ "
        "<font face='Courier'>qty</font> d'un mouvement de stock exigeait une valeur strictement positive pour "
        "<b>tous</b> les types de mouvement, y compris \"Ajustement\" — alors qu'un ajustement doit justement "
        "pouvoir être négatif pour enregistrer un manque (vol, casse non déclarée). Autrement dit : la règle "
        "métier documentée (\"comparer au stock théorique et ajuster\") n'était en réalité pas réalisable pour "
        "le cas le plus important, un manque. Corrigé en ne relâchant la contrainte que pour ce type précis, "
        "testé, puis documenté. Illustre qu'une user story formulée comme une vraie question d'usage (pas "
        "\"ajoute un champ X\") révèle des trous que la relecture de code seule aurait pu manquer.",
        body_style,
    ))

    # ------------------------------------------------------------------
    story.append(Paragraph("12. Limites connues et axes d'amélioration", h1_style))
    story.append(Paragraph(
        "Assumés et identifiés soi-même — bon signal en entretien de savoir nommer les limites de son propre "
        "travail plutôt que de les laisser découvrir :",
        body_style,
    ))
    story.append(bullets([
        "<b>Pas de CI/CD</b> : tests et déploiement lancés manuellement (<font face='Courier'>pytest</font> en "
        "local avant chaque push, puis <font face='Courier'>git pull &amp;&amp; docker compose up -d --build</font> "
        "sur le VPS). Une GitHub Action lançant la suite de tests sur chaque push serait la prochaine amélioration "
        "naturelle.",
        "<b>Documentation désynchronisée, leçon apprise</b> : le nombre de tests dans le README a traîné "
        "obsolète pendant un moment (39 alors que le code était déjà à 143) avant d'être remarqué. Depuis, "
        "chaque fonctionnalité ajoutée s'accompagne systématiquement d'une mise à jour du README/guide de "
        "formation dans le même lot de changements — discipline plutôt que rattrapage ponctuel.",
        "<b>Pas de vrai temps réel</b> : rafraîchissement par sondage (15s) plutôt que websockets, choix "
        "délibéré de simplicité pour l'échelle actuelle du projet (voir section 8).",
        "<b>Développé sans Docker en local</b> à l'origine (pas installé sur la machine de développement) : les "
        "fichiers Compose ont été écrits selon des patterns standards puis validés directement sur le vrai VPS, "
        "plutôt que testés en local au préalable.",
    ]))

    # ------------------------------------------------------------------
    story.append(Paragraph("13. Pitch en une minute", h1_style))
    story.append(Paragraph(
        "\"J'ai conçu et développé seul, de bout en bout, un logiciel de caisse et de gestion de stock pour un "
        "commerce réel — API FastAPI/SQLAlchemy typée, 161 tests automatisés (unitaires et intégration), "
        "règles anti-fraude explicites dictées par un vrai besoin métier, containerisé avec Docker et déployé "
        "sur un VPS avec HTTPS automatique. J'ai aussi mis en place un environnement de staging synchronisé "
        "automatiquement depuis la prod chaque mois, des sauvegardes régulières avec rétention, et je documente "
        "moi-même les limites de mes choix techniques (pas de CI encore, pas de websockets) plutôt que de les "
        "présenter comme un produit fini sans defaut.\"",
        pitch_style,
    ))

    doc.build(story)
    print(f"PDF généré : {OUTPUT_PATH}")


if __name__ == "__main__":
    build()
