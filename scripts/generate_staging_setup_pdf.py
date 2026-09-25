"""Génère un PDF pédagogique expliquant, commande par commande, la mise en
place de l'environnement de test ISO prod (staging) + pgAdmin.
Usage : .venv/Scripts/python.exe scripts/generate_staging_setup_pdf.py
Produit Mise_en_place_environnement_staging.pdf à la racine du projet.
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

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "Mise_en_place_environnement_staging.pdf"

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
    """rows: list of (commande, explication) -> tableau 2 colonnes."""
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

    story.append(Paragraph("La Cave du Coin — Mise en place de l'environnement de test (staging)", title_style))
    story.append(Paragraph(
        "Journal détaillé, commande par commande, de la création d'un environnement ISO prod "
        "et de son accès via pgAdmin — pour comprendre et pouvoir refaire seul à l'avenir.",
        subtitle_style,
    ))

    # ------------------------------------------------------------------
    story.append(Paragraph("1. Objectif : pourquoi cet environnement ?", h1_style))
    story.append(Paragraph(
        "Le besoin de départ : disposer d'un endroit où exécuter des requêtes SQL sur des données "
        "réalistes, sans jamais risquer d'abîmer la base de production. La solution retenue est un "
        "<b>second stack applicatif complet</b> (application + base PostgreSQL), tournant sur le "
        "<b>même serveur (VPS)</b> que la production mais dans des conteneurs Docker totalement "
        "séparés, avec sa propre base de données. Une fois par mois, un script recopie le code et "
        "les données de production dans cet environnement, pour qu'il reste \"ISO prod\" (identique) "
        "dans le temps.",
        body_style,
    ))

    story.append(Paragraph("2. Vue d'ensemble de l'architecture obtenue", h1_style))
    story.append(Paragraph(
        "Un seul serveur (VPS Hetzner) héberge deux \"stacks\" Docker Compose indépendants, identifiés "
        "par un nom de projet différent (<font face='Courier'>-p staging</font> pour le second) :",
        body_style,
    ))
    story.append(
        ListFlowable(
            [
                ListItem(Paragraph(
                    "<b>Stack \"prod\"</b> (celui déjà en place) : conteneurs <font face='Courier'>app</font> "
                    "et <font face='Courier'>db</font>, plus <font face='Courier'>caddy</font> (reverse proxy "
                    "HTTPS) qui reçoit tout le trafic public sur les ports 80/443 et le redirige vers "
                    "<font face='Courier'>app</font>. C'est ce qui sert <font face='Courier'>lacaveducoin.com</font>.",
                    explain_style,
                )),
                ListItem(Paragraph(
                    "<b>Stack \"staging\"</b> (nouveau) : ses propres conteneurs <font face='Courier'>db</font> "
                    "et <font face='Courier'>app</font> (une base et une application indépendantes), plus "
                    "<font face='Courier'>pgadmin</font> (interface web pour interroger la base). Rien n'est "
                    "exposé publiquement par défaut : les ports de la base/app sont liés uniquement à "
                    "<font face='Courier'>127.0.0.1</font> (la boucle locale du serveur), donc injoignables "
                    "depuis internet même en cas d'oubli de pare-feu.",
                    explain_style,
                )),
            ],
            bulletType="bullet",
            leftIndent=12,
        )
    )
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Pour se connecter à la base staging, deux chemins possibles : un <b>tunnel SSH</b> depuis un "
        "PC non bridé (redirige un port du PC vers le port local du VPS), ou <b>pgAdmin en HTTPS</b> "
        "via un sous-domaine dédié (<font face='Courier'>pgadmin.lacaveducoin.com</font>) — utile "
        "quand le poste utilisé bloque les connexions SSH \"brutes\" (cas du PC professionnel Allianz, "
        "protégé par un proxy Zscaler qui laisse passer le HTTPS vers des domaines reconnus mais "
        "bloque le SSH direct).",
        body_style,
    ))

    # ------------------------------------------------------------------
    story.append(Paragraph("3. Nouveaux fichiers ajoutés au projet", h1_style))
    story.append(Paragraph(
        "Chaque commande exécutée sur le serveur s'appuie sur des fichiers ajoutés dans le dépôt Git, "
        "récupérés simplement via <font face='Courier'>git pull</font> — c'est un principe important : "
        "on évite de taper du contenu compliqué directement dans la console (voir section 6), on le "
        "prépare dans des fichiers versionnés à l'avance.",
        body_style,
    ))
    story.append(cmd_table([
        ("docker-compose.staging.yml", "Fichier Docker Compose \"overlay\" (complément) qui ajoute au fichier de base : les ports "
         "127.0.0.1 pour db/app, le service pgadmin, et le rattachement au réseau partagé caddy-net."),
        (".env.staging.example", "Modèle de configuration pour le stack staging (mots de passe, secrets). À copier en "
         ".env.staging puis à personnaliser — jamais commité tel quel dans Git (fichier réel exclu via .gitignore)."),
        ("scripts/refresh_staging_from_prod.sh", "Script principal : synchronise le code (git pull), reconstruit/démarre le stack staging, "
         "puis copie les données de prod vers staging. Utilisé pour le premier lancement ET pour le "
         "rafraîchissement mensuel automatique."),
        ("scripts/verify_staging.sh", "Petit script de vérification : affiche les utilisateurs et produits présents dans la base "
         "staging, pour confirmer que la copie de données a fonctionné."),
        ("deploy/staging-refresh.cron", "Contenu prêt à l'emploi pour /etc/cron.d/ : programme l'exécution automatique du script de "
         "rafraîchissement le 1er de chaque mois à 2h du matin."),
        ("scripts/add_pgadmin_env_vars.sh / add_pgadmin_domain.sh", "Scripts qui ajoutent automatiquement, sans risque de faute de frappe, les lignes de "
         "configuration nécessaires à pgAdmin dans .env.staging et .env (prod)."),
        ("Caddyfile (modifié)", "Ajout d'un second \"site\" géré par Caddy : le sous-domaine pgAdmin, routé vers le conteneur "
         "pgadmin plutôt que vers l'application principale."),
        ("docker-compose.vps.yml (modifié)", "Ajout du rattachement de Caddy au réseau partagé caddy-net, pour qu'il puisse atteindre le "
         "conteneur pgadmin qui vit dans l'autre stack (staging)."),
    ]))

    # ------------------------------------------------------------------
    story.append(Paragraph("4. Déroulé complet, commande par commande", h1_style))

    story.append(Paragraph("4.1 — Récupérer le code et préparer la configuration", h2_style))
    story.append(cmd_table([
        ("git pull", "Télécharge et applique les derniers fichiers du dépôt GitHub sur le serveur — c'est ainsi que "
         "tous les nouveaux fichiers (scripts, Caddyfile, etc.) arrivent sur le VPS, sans jamais les "
         "taper à la main."),
        ("docker network create caddy-net", "Crée un réseau Docker \"nommé\" et partagé. Par défaut, chaque projet Docker Compose crée son "
         "propre réseau isolé (les conteneurs \"prod\" ne voient pas les conteneurs \"staging\"). En "
         "créant ce réseau à part et en y rattachant à la fois Caddy (côté prod) et pgAdmin (côté "
         "staging), les deux peuvent se parler malgré leurs stacks séparés."),
        ("cp .env.staging.example .env.staging", "Copie le modèle de configuration en un vrai fichier de configuration pour le stack staging. "
         "\"cp\" = copy : duplique un fichier."),
        ("nano .env.staging", "Ouvre un éditeur de texte en ligne de commande pour renseigner les vraies valeurs (mot de passe "
         "de la base, secret de sécurité) à la place des valeurs d'exemple."),
    ]))

    story.append(Paragraph("4.2 — Premier démarrage du stack staging", h2_style))
    story.append(cmd_table([
        ("chmod 755 scripts/refresh_staging_from_prod.sh", "\"chmod\" change les permissions d'un fichier. 755 signifie : le propriétaire peut lire/écrire/"
         "exécuter, les autres peuvent seulement lire/exécuter. Sans ce réglage, Linux refuse de lancer "
         "un fichier .sh comme un programme (message \"Permission denied\")."),
        ("./scripts/refresh_staging_from_prod.sh", "Lance le script. En interne, il exécute dans l'ordre : (1) git pull, (2) "
         "\"docker compose ... up -d --build\" pour démarrer/mettre à jour les conteneurs du stack "
         "staging (crée le réseau, le volume, construit l'image de l'app, démarre db/app/pgadmin), "
         "(3) une commande combinant pg_dump (côté prod) et pg_restore (côté staging) pour copier "
         "l'intégralité de la base de production dans la base staging."),
        ("docker exec staging-db-1 psql -U cave_du_coin -c \"select ...\"", "\"docker exec\" lance une commande À L'INTÉRIEUR d'un conteneur déjà démarré (ici "
         "staging-db-1). \"psql\" est le client en ligne de commande de PostgreSQL ; \"-U\" précise "
         "l'utilisateur, \"-c\" fait exécuter une requête SQL ponctuelle sans ouvrir de session "
         "interactive. Utilisé ici pour vérifier que les données sont bien présentes."),
    ]))

    story.append(Paragraph("4.3 — Planifier le rafraîchissement automatique mensuel", h2_style))
    story.append(cmd_table([
        ("cp deploy/staging-refresh.cron /etc/cron.d/staging-refresh", "Place le fichier de planification dans le dossier que le service cron (le planificateur de "
         "tâches de Linux) surveille automatiquement. Chaque fichier dans /etc/cron.d/ contient une ou "
         "plusieurs lignes au format : minute heure jour-du-mois mois jour-semaine utilisateur commande. "
         "Ici : \"0 2 1 * *\" = à 0 minute, 2h, le 1er jour de chaque mois, tous mois, tout jour de la "
         "semaine."),
        ("systemctl status cron", "Affiche l'état du service cron lui-même (démarré ou non). \"systemctl\" est l'outil standard "
         "pour gérer les services système sous Linux moderne (Ubuntu, Debian...). Vérifié \"active "
         "(running)\", donc les tâches planifiées seront bien exécutées."),
        ("cat /etc/cron.d/staging-refresh", "\"cat\" affiche le contenu d'un fichier. Utilisé pour vérifier que la copie n'a pas été déformée "
         "(la console a un bug clavier qui peut altérer certains caractères tapés à la main, cf. "
         "section 6) — une simple copie de fichier via \"cp\", elle, ne risque rien."),
    ]))

    story.append(Paragraph("4.4 — Accès pgAdmin sans tunnel SSH (HTTPS)", h2_style))
    story.append(cmd_table([
        ("Enregistrement DNS de type A", "Ajouté dans l'interface de gestion DNS du domaine (pas sur le serveur) : associe le nom "
         "\"pgadmin.lacaveducoin.com\" à l'adresse IP du VPS. Sans ça, ce nom de domaine ne "
         "\"pointerait\" vers rien."),
        ("./scripts/add_pgadmin_env_vars.sh", "Ajoute automatiquement au fichier .env.staging les identifiants de connexion à l'interface "
         "pgAdmin (email + mot de passe), sans risquer une faute de frappe sur le caractère \"@\"."),
        ("./scripts/add_pgadmin_domain.sh", "Ajoute automatiquement au fichier .env (celui de production, lu par Caddy) la ligne "
         "PGADMIN_DOMAIN=pgadmin.lacaveducoin.com, sans risquer une faute de frappe sur le caractère "
         "\"_\"."),
        ("docker compose up -d --build (à nouveau, pour la prod)", "Relit le .env de production mis à jour et redémarre les conteneurs concernés — ici, "
         "essentiellement Caddy, qui prend en compte la nouvelle route vers pgAdmin. \"-d\" = "
         "detached (en arrière-plan), \"--build\" = reconstruit l'image si le code de l'app a changé "
         "(sans effet ici puisque seul Caddy est concerné)."),
        ("docker compose logs caddy --tail 30", "Affiche les 30 dernières lignes de journal (logs) du conteneur Caddy — utilisé pour confirmer "
         "que Caddy a bien obtenu un certificat HTTPS valide (Let's Encrypt) pour le nouveau sous-"
         "domaine, via le protocole ACME (validation automatique du nom de domaine)."),
    ]))

    story.append(Paragraph("4.5 — Connexion finale dans l'interface pgAdmin", h2_style))
    story.append(Paragraph(
        "Cette dernière étape se fait entièrement dans le navigateur (pas dans la console du serveur) : "
        "ouverture de <font face='Courier'>https://pgadmin.lacaveducoin.com</font>, connexion avec "
        "l'email/mot de passe pgAdmin, puis \"Register → Server\" pour enregistrer la base staging "
        "elle-même comme cible de requêtes (host = <font face='Courier'>db</font> — le nom du service "
        "dans docker-compose.yml, résolu automatiquement par Docker — port 5432, base "
        "<font face='Courier'>cave_du_coin</font>, utilisateur <font face='Courier'>cave_du_coin</font>, "
        "mot de passe = celui de <font face='Courier'>POSTGRES_PASSWORD</font> dans .env.staging).",
        body_style,
    ))

    # ------------------------------------------------------------------
    story.append(Paragraph("5. Le bug clavier de la console Hetzner", h1_style))
    story.append(Paragraph(
        "La console web du VPS (utilisée en l'absence d'un accès SSH direct fonctionnel) déforme "
        "certains caractères nécessitant la touche Shift à la frappe : "
        "<font face='Courier'>+</font> devient <font face='Courier'>=</font>, "
        "<font face='Courier'>_</font> devient <font face='Courier'>-</font>, "
        "<font face='Courier'>( * )</font> se transforment en chiffres, etc. Ce n'est pas systématique "
        "ni prévisible à 100%, donc la parade a été, chaque fois que possible :",
        body_style,
    ))
    story.append(
        ListFlowable(
            [
                ListItem(Paragraph("Préparer le contenu compliqué (scripts, fichiers de configuration, lignes cron) "
                                    "<b>dans des fichiers versionnés sur GitHub</b>, récupérés via "
                                    "<font face='Courier'>git pull</font> ou copiés via <font face='Courier'>cp</font> — "
                                    "aucun caractère n'est alors tapé à la main.", explain_style)),
                ListItem(Paragraph("Utiliser la <b>complétion automatique (touche Tab)</b> pour les noms de fichiers "
                                    "contenant des underscores : le terminal insère lui-même les caractères exacts, "
                                    "sans passer par le clavier physique pour cette partie.", explain_style)),
                ListItem(Paragraph("Préférer des variantes de commandes sans caractère à risque quand elles existent "
                                    "(<font face='Courier'>chmod 755</font> au lieu de <font face='Courier'>chmod +x</font>).", explain_style)),
                ListItem(Paragraph("Toujours <b>vérifier avec <font face='Courier'>cat</font></b> le contenu d'un "
                                    "fichier après une opération sensible, avant de l'utiliser.", explain_style)),
            ],
            bulletType="bullet",
            leftIndent=12,
        )
    )

    # ------------------------------------------------------------------
    story.append(Paragraph("6. Concepts clés à retenir", h1_style))
    story.append(cmd_table([
        ("Docker Compose \"projet\"", "Un ensemble de conteneurs démarrés ensemble depuis un ou plusieurs fichiers "
         "docker-compose*.yml partagent un nom de \"projet\" (par défaut, le nom du dossier ; ici forcé "
         "à \"staging\" via -p staging). Chaque projet a son propre réseau et ses propres volumes par "
         "défaut, isolés des autres projets — d'où la nécessité d'un réseau partagé explicite "
         "(caddy-net) pour relier deux projets."),
        ("Réseau Docker & résolution de noms", "À l'intérieur d'un même réseau Docker, chaque service est joignable par son nom (ex: "
         "\"db\", \"pgadmin\") comme s'il s'agissait d'une adresse — Docker gère cette résolution "
         "automatiquement (DNS interne), pas besoin de connaître d'adresse IP."),
        ("Ports liés à 127.0.0.1", "Une règle \"127.0.0.1:PORT:PORT\" dans docker-compose expose un service uniquement sur "
         "l'interface \"boucle locale\" du serveur (accessible seulement depuis le serveur lui-même), "
         "jamais depuis internet — une protection au niveau réseau, indépendante du pare-feu."),
        ("pg_dump / pg_restore", "Deux outils PostgreSQL complémentaires : pg_dump exporte le contenu d'une base (structure + "
         "données) dans un fichier ; pg_restore le réimporte. L'option --clean --if-exists fait "
         "d'abord table rase de la base de destination avant de tout réimporter, pour garantir une "
         "copie fidèle et non un simple ajout aux données existantes."),
        ("Reverse proxy (Caddy) & Let's Encrypt", "Caddy reçoit tout le trafic HTTPS public et le redirige (\"reverse proxy\") vers le bon "
         "conteneur selon le nom de domaine demandé. Il obtient et renouvelle automatiquement de "
         "vrais certificats HTTPS gratuits auprès de Let's Encrypt, via le protocole ACME, sans "
         "aucune configuration manuelle de certificat."),
        ("Tunnel SSH (port forwarding)", "Une commande \"ssh -L port_local:127.0.0.1:port_distant\" ouvre un tunnel chiffré : tout ce qui "
         "est envoyé sur le port local de votre PC est transporté jusqu'au serveur puis redirigé "
         "vers un port qui, sur le serveur, n'est accessible que localement. Permet d'atteindre un "
         "service \"privé\" du serveur sans jamais l'exposer publiquement."),
    ]))

    story.append(Paragraph("7. Ce qui est désormais automatique vs. ce qui reste manuel", h1_style))
    story.append(Paragraph(
        "<b>Automatique</b> : le rafraîchissement mensuel (code + données) via le cron planifié — "
        "aucune action nécessaire, un journal est conservé dans "
        "<font face='Courier'>staging_refresh.log</font>. Le renouvellement des certificats HTTPS "
        "(Caddy s'en occupe seul, bien avant leur expiration).",
        body_style,
    ))
    story.append(Paragraph(
        "<b>Manuel</b> (rare, seulement si le besoin évolue) : ajouter un nouvel enregistrement DNS "
        "si un nouveau sous-domaine est nécessaire un jour ; relancer "
        "<font face='Courier'>docker compose up -d --build</font> après un <font face='Courier'>git "
        "pull</font> si le code du projet évolue à nouveau (comme pour la production) ; changer les "
        "mots de passe par défaut si ce n'est pas déjà fait.",
        body_style,
    ))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "⚠️ Rappel sécurité : chaque rafraîchissement copie les vraies données clients de production "
        "(noms, téléphones, adresses, soldes) dans l'environnement de test. Comme il n'y a pas de "
        "tiers impliqué (votre propre activité), ce n'est pas un problème de conformité en soi — "
        "gardez simplement le même niveau de vigilance sur les mots de passe de cet environnement "
        "que sur la production.",
        note_style,
    ))

    doc.build(story)
    print(f"PDF généré : {OUTPUT_PATH}")


if __name__ == "__main__":
    build()
