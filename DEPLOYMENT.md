# Déploiement — PC boutique local ou VPS distant

Deux façons de déployer **La Cave du Coin**, à choisir selon votre situation :

- **Option A — VPS (recommandé dans votre cas)** : l'admin est en France, la
  boutique en Guinée. Un petit serveur cloud toujours allumé, avec une adresse
  fixe, permet à l'admin et aux employés de la boutique de se connecter depuis
  n'importe où via internet — pas de dépendance à un PC physique précis.
- **Option B — PC de la boutique en réseau local** : si vous préférez éviter
  tout hébergement payant, ou si la connexion internet de la boutique n'est pas
  fiable. Dans ce cas seul le réseau Wi-Fi local de la boutique donne accès à
  l'appli ; **l'admin en France ne pourrait pas s'y connecter à distance** sans
  ouvrir en plus un tunnel (moins robuste qu'un VPS).

---

# Option A — VPS (accès admin à distance)

## Vue d'ensemble

```
                    Internet
                        |
        ┌───────────────┴───────────────┐
        |                                |
[Admin, France]                  [Boutique, Guinée]
   navigateur                    navigateur (caissiers, manager)
        |                                |
        └───────────────┬───────────────┘
                         |
              https://<ip>.sslip.io
                         |
                 [VPS : Caddy (HTTPS)
                  → app (FastAPI) → PostgreSQL]
```

Tout le monde (admin comme employés) se connecte à la **même URL publique**,
depuis n'importe quel navigateur, sans VPN ni logiciel particulier.

## Étape 1 — Créer le VPS

Recommandation : **[Hetzner Cloud](https://www.hetzner.com/cloud/)**, offre
`CX22` (2 vCPU, 4 Go RAM) à ~4,5 €/mois — largement suffisant pour un seul
point de vente, facturé à l'heure (annulable à tout moment).

1. Créer un compte, créer un serveur : image **Ubuntu 24.04**, région au choix
   (une région Europe convient aussi bien pour la France que pour la Guinée).
2. Notez l'**adresse IP publique** du serveur (ex: `178.63.45.12`).
3. Connexion en SSH (mot de passe ou clé fournie à la création) :
   ```bash
   ssh root@178.63.45.12
   ```

## Étape 2 — Installer Docker sur le VPS

```bash
apt update && apt install -y docker.io docker-compose-plugin git
systemctl enable --now docker
```

## Étape 3 — Pare-feu (sécurité essentielle sur un serveur public)

```bash
apt install -y ufw
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```
Seuls SSH, HTTP et HTTPS sont exposés — PostgreSQL et l'API interne ne sont
**jamais** accessibles directement depuis internet (déjà garanti aussi par
`docker-compose.yml`, qui ne publie plus ces ports).

## Étape 4 — Copier le projet et configurer

```bash
# Depuis votre PC : copier le projet sur le VPS (adapter le chemin source)
scp -r La_Cave_du_Coin root@178.63.45.12:/opt/

# Sur le VPS :
cd /opt/La_Cave_du_Coin
cp .env.example .env
nano .env
```

Dans `.env`, renseigner :
- `POSTGRES_PASSWORD` : mot de passe fort
- `JWT_SECRET` : `python3 -c "import secrets;print(secrets.token_hex(32))"`
- `PUBLIC_DOMAIN` : votre IP avec des tirets à la place des points, suivi de
  `.sslip.io`. Exemple pour `178.63.45.12` → `178-63-45-12.sslip.io`.
  ([sslip.io](https://sslip.io) est un service DNS public gratuit qui fait
  toujours pointer `X-X-X-X.sslip.io` vers l'IP `X.X.X.X` — cela suffit pour
  que Caddy obtienne un vrai certificat HTTPS Let's Encrypt, sans avoir besoin
  d'acheter un nom de domaine.)
- `COMPOSE_FILE=docker-compose.yml:docker-compose.vps.yml` — active la brique
  Caddy/HTTPS (fichier séparé de `docker-compose.lan.yml`, utilisé pour
  l'Option B) ; une fois réglé, toutes les commandes `docker compose ...`
  suivantes prennent automatiquement les deux fichiers en compte.

## Étape 5 — Démarrer

```bash
docker compose up -d --build
# Patientez ~30s : Caddy doit obtenir son certificat HTTPS, l'app ses migrations.
docker compose exec app python scripts/seed_data.py   # une seule fois
```

L'application est alors accessible, **depuis la France comme depuis la
Guinée**, sur :
```
https://178-63-45-12.sslip.io
```
(remplacer par votre `PUBLIC_DOMAIN`).

⚠️ **Changez immédiatement les mots de passe `admin`/`manager`/`caissier`**
créés par le seed avant de donner l'accès aux employés — le lien est désormais
public sur internet.

## Étape 6 — Sauvegardes sur le VPS

Même script que pour un PC (`scripts/backup.py`), mais planifié via `cron` au
lieu du Planificateur de tâches Windows :

```bash
apt install -y python3-venv
cd /opt/La_Cave_du_Coin
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

crontab -e
# Ajouter la ligne :
0 */4 * * * cd /opt/La_Cave_du_Coin && /opt/La_Cave_du_Coin/.venv/bin/python scripts/backup.py >> backup.log 2>&1
```

Pour la copie hors-site (`OFFSITE_BACKUP_DIR`), utilisez par exemple
[rclone](https://rclone.org/) configuré vers Google Drive/OneDrive, en pointant
`OFFSITE_BACKUP_DIR` vers le dossier monté — plus avancé, dites-moi si vous
voulez que je détaille cette partie.

## Mise à jour de l'application sur le VPS

```bash
cd /opt/La_Cave_du_Coin
git pull   # ou re-scp les fichiers modifiés
docker compose up -d --build   # réapplique aussi les migrations Alembic automatiquement
```

## Environnement de test ISO prod (staging)

Un second stack Docker, sur le **même VPS**, avec sa propre base PostgreSQL et
sa propre application — même code, mais données et base totalement séparées
de la production. Sert à faire des requêtes/tests sans aucun risque pour la
prod. Remis à jour automatiquement **une fois par mois** avec une copie
fraîche des données de production (et du code le plus récent).

**Cas particulier** : si la prod ne contient encore aucun produit ni vente
réelle (juste après un `reset_prod_database.sh`, par exemple), le
rafraîchissement copie automatiquement la dernière sauvegarde de démo
disponible (`backup_before_reset_*.dump`) au lieu d'une prod vide — pratique
pour continuer à s'entraîner sur des données réalistes en attendant la vraie
activité. Dès que la prod contient au moins un produit ou une vente réelle,
le script bascule automatiquement sur la copie normale (la vraie prod) —
aucune action requise de votre part pour ce basculement.

### Vue d'ensemble

```
[VPS]
 ├─ stack "prod"     : app (port interne) + db (port interne) → Caddy → https://...
 └─ stack "staging"  : app (127.0.0.1:8001) + db (127.0.0.1:55432)
                        accessibles uniquement via tunnel SSH depuis votre PC
```

Les ports de staging sont liés à `127.0.0.1` sur le VPS : **jamais exposés sur
internet**, même en cas d'oubli de configuration du pare-feu. Seul un tunnel
SSH permet d'y accéder depuis votre PC.

### Mise en place (une seule fois)

```bash
cd /opt/La_Cave_du_Coin
cp .env.staging.example .env.staging
nano .env.staging
```

Renseigner `POSTGRES_PASSWORD` et `JWT_SECRET` (voir le fichier : préférez des
valeurs **uniquement alphanumériques**, pour éviter les caractères que la
console web Hetzner déforme à la frappe — `:`, `"`, `$`, `(`, `)`, `_`, `@`...).

Premier démarrage + première copie des données de prod (peut prendre 1-2
minutes) :

```bash
chmod +x scripts/refresh_staging_from_prod.sh
./scripts/refresh_staging_from_prod.sh
```

### Planifier la mise à jour mensuelle

Plutôt que de taper une ligne `crontab -e` remplie de caractères spéciaux
(risqué avec le bug de clavier de la console Hetzner), copier directement le
fichier déjà préparé dans le dépôt :

```bash
cp deploy/staging-refresh.cron /etc/cron.d/staging-refresh
```

Cela exécute `scripts/refresh_staging_from_prod.sh` à 2h du matin le 1er de
chaque mois (résultat journalisé dans `staging_refresh.log`). Vérifier après
coup :

```bash
cat staging_refresh.log
```

### Se connecter avec DBeaver (via tunnel SSH)

Depuis votre PC, ouvrir un tunnel SSH vers le VPS :

```bash
ssh -L 55432:127.0.0.1:55432 -L 8001:127.0.0.1:8001 root@<ip-du-vps>
```

Puis dans DBeaver, nouvelle connexion PostgreSQL :
- Host : `localhost`, Port : `55432`
- Base : `cave_du_coin`, Utilisateur : `cave_du_coin`, Mot de passe : celui de
  `POSTGRES_PASSWORD` dans `.env.staging`

Le tunnel doit rester ouvert (terminal SSH connecté) pendant l'utilisation de
DBeaver. Le second port transféré (`8001`) permet aussi d'ouvrir l'application
web de staging elle-même dans un navigateur, sur `http://localhost:8001`, si
besoin de tester une fonctionnalité avec des données réelles sans risque.

### Alternative sans tunnel SSH : pgAdmin en HTTPS

Un poste géré (proxy d'entreprise qui bloque les connexions brutes/SSH) ne
peut pas ouvrir de tunnel SSH. Dans ce cas, **pgAdmin** (interface web pour
PostgreSQL) donne accès aux mêmes requêtes SQL via une simple page HTTPS,
comme l'application elle-même.

**Prérequis DNS** — chez votre registrar/DNS (pas sur le VPS), ajouter un
enregistrement `A` pour un sous-domaine dédié, pointant vers l'IP du VPS,
par exemple `pgadmin.lacaveducoin.com`.

**Une seule fois, sur le VPS** — créer le réseau Docker partagé entre les
deux stacks (prod et staging) qui permettra à Caddy de router vers pgAdmin :
```bash
docker network create caddy-net
```

Dans `.env.staging`, ajouter/vérifier les deux lignes (déjà présentes dans
`.env.staging.example`, avec des valeurs par défaut à changer) :
```
PGADMIN_DEFAULT_EMAIL=admin@lacaveducoin.com
PGADMIN_DEFAULT_PASSWORD=ChangeMePgAdmin123
```
(l'adresse n'a pas besoin d'être réelle ; vous pouvez la laisser telle quelle
pour éviter de taper un `@` dans la console).

Dans le `.env` de **production** (pas `.env.staging`), ajouter la ligne :
```
PGADMIN_DOMAIN=pgadmin.lacaveducoin.com
```

Puis relancer les deux stacks pour qu'ils prennent en compte ces changements :
```bash
./scripts/refresh_staging_from_prod.sh
docker compose up -d --build
```
(la deuxième commande redémarre Caddy avec la nouvelle route ; elle relit le
`.env` de prod, sans toucher au reste de la production déjà en ligne).

**Première connexion** : ouvrir `https://pgadmin.lacaveducoin.com`, se
connecter avec `PGADMIN_DEFAULT_EMAIL` / `PGADMIN_DEFAULT_PASSWORD`, puis
ajouter un nouveau serveur PostgreSQL (clic droit sur "Servers" → "Register
→ Server") :
- Onglet "General" → Name : `Staging` (libre)
- Onglet "Connection" → Host : `db`, Port : `5432`, Maintenance database :
  `cave_du_coin`, Username : `cave_du_coin`, Password : celui de
  `POSTGRES_PASSWORD` dans `.env.staging`

Une fois enregistré, la connexion est mémorisée par pgAdmin (dans son propre
volume) — pas besoin de la ressaisir à chaque visite.

### ⚠️ Point d'attention

Chaque rafraîchissement copie les **vraies données clients** de production
(noms, téléphones, adresses, soldes) dans l'environnement de test. Comme c'est
votre propre activité et qu'il n'y a pas de tiers impliqué, ce n'est pas un
problème de conformité en soi — gardez simplement le même niveau de vigilance
sur l'accès à cet environnement (mots de passe forts, tunnel SSH uniquement)
que sur la prod elle-même.

---

# Option B — PC de la boutique en réseau local

Ce guide décrit comment installer **La Cave du Coin** sur le PC de la boutique
pour qu'il serve de serveur central, accessible depuis les autres appareils
(PC/tablettes des caissiers, manager) connectés au même réseau Wi-Fi/local.
**L'admin à distance (France) n'a pas accès dans cette option**, sauf à
ajouter un tunnel en plus (moins fiable qu'un VPS, cf. Option A).

Contexte : c'est votre propre PC (droits administrateur disponibles), pas un
poste géré par une DSI externe — l'installation de Docker et Python y est donc
possible sans restriction.

## Vue d'ensemble

```
[PC caisse central : Docker (app + PostgreSQL)] <--- réseau Wi-Fi boutique ---> [PC/tablette caissier 1]
        ^ toujours allumé                                                    -> [PC/tablette caissier 2]
                                                                               -> [PC manager]
```

Un seul PC fait tourner le logiciel (serveur). Les autres appareils s'y
connectent juste avec un navigateur, comme un site web — rien à installer
dessus.

## Étape 1 — Installer Docker Desktop sur le PC caisse

1. Télécharger et installer [Docker Desktop](https://www.docker.com/products/docker-desktop/)
   (gratuit pour un usage personnel / petite entreprise).
2. Activer le backend WSL2 si demandé à l'installation (Docker Desktop guide
   l'installation de WSL2 automatiquement).
3. Dans les réglages de Docker Desktop : **Settings → General → "Start Docker
   Desktop when you log in"** → activer.

## Étape 2 — Copier le projet et le configurer

1. Copier tout le dossier `La_Cave_du_Coin/` sur le PC caisse (clé USB, partage
   réseau, ou dépôt git si vous en créez un).
2. Dans le dossier, créer le fichier de configuration :
   ```bash
   cp .env.example .env
   ```
3. Éditer `.env` et changer au minimum :
   - `POSTGRES_PASSWORD` : un mot de passe fort
   - `JWT_SECRET` : une chaîne aléatoire longue (ex: générée avec
     `python -c "import secrets;print(secrets.token_hex(32))"`)
   - `COMPOSE_FILE=docker-compose.yml:docker-compose.lan.yml` — expose l'app
     sur le port 8000 du PC pour l'accès réseau local (pas de Caddy/HTTPS ici,
     inutile sur un simple réseau Wi-Fi de boutique).

## Étape 3 — Démarrer l'application

```bash
docker compose up -d --build
# Le conteneur applique automatiquement les migrations Alembic à chaque
# démarrage (cf. Dockerfile) avant de lancer le serveur — patientez ~10s.
docker compose exec app python scripts/seed_data.py   # une seule fois, à l'installation
```

⚠️ **Changez immédiatement les mots de passe des comptes `admin`/`manager`/
`caissier`** créés par le seed (via la page "Utilisateurs", ou en recréant les
comptes) avant d'ouvrir l'accès aux employés.

Le conteneur redémarre automatiquement avec Docker Desktop grâce à
`restart: unless-stopped` déjà configuré dans `docker-compose.yml`.

Le schéma de base est géré par **Alembic** (voir README § Migrations de
schéma) : toute évolution future du logiciel qui change la structure de la
base s'appliquera avec `docker compose exec app alembic upgrade head`, **sans
perte des ventes/stocks déjà enregistrés**.

## Étape 4 — Démarrage automatique avec le PC (sans intervention)

Pour que tout se relance seul à l'allumage du PC caisse, sans qu'un employé
ait à ouvrir quoi que ce soit :

1. **Ouverture de session automatique** : configurez le compte Windows de ce
   PC pour se connecter automatiquement au démarrage (`netplwiz` → décocher
   "Les utilisateurs doivent entrer un nom et un mot de passe" → choisir le
   compte). Cela permet à Docker Desktop (qui se lance à la connexion) de
   démarrer sans intervention humaine.
2. Docker Desktop relance alors automatiquement les conteneurs `app` et `db`
   (grâce à `restart: unless-stopped`).
3. **Testez** en redémarrant le PC : après ~1-2 minutes, `http://localhost:8000`
   doit répondre sans que personne n'ait rien ouvert.

## Étape 5 — Rendre l'appli accessible depuis les autres appareils

1. **Trouver l'adresse IP locale du PC caisse** :
   ```bash
   ipconfig
   ```
   Notez l'adresse `IPv4` (ex: `192.168.1.50`).

2. **Fixer cette adresse** (pour qu'elle ne change pas) : dans l'interface
   d'administration de votre routeur/box internet, faites une **réservation
   DHCP** pour l'adresse MAC de ce PC (sinon l'IP peut changer et casser
   l'accès des autres appareils après un redémarrage du routeur).

3. **Autoriser le port 8000 dans le pare-feu Windows** du PC caisse :
   ```powershell
   New-NetFirewallRule -DisplayName "La Cave du Coin" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow
   ```
   (à exécuter dans PowerShell **en administrateur**)

4. **Depuis chaque appareil employé** (connecté au même Wi-Fi boutique),
   ouvrir un navigateur sur :
   ```
   http://192.168.1.50:8000
   ```
   (remplacer par l'IP réelle notée à l'étape 1). Vous pouvez créer un
   raccourci/favori sur chaque appareil pour que les caissiers n'aient qu'à
   cliquer une icône.

## Sécurité réseau — points essentiels

- **Ne jamais exposer ce PC sur Internet** (pas de redirection de port sur le
  routeur/box vers le port 8000) : l'accès doit rester strictement limité au
  réseau local de la boutique.
- Le Wi-Fi de la boutique doit être protégé par un mot de passe (WPA2/WPA3),
  distinct du Wi-Fi "client" si vous en proposez un aux visiteurs.
- Changez `JWT_SECRET` et tous les mots de passe par défaut avant la mise en
  service réelle.

## Étape 6 — Sauvegardes automatiques (toutes les 4h)

`scripts/backup.py` sauvegarde la base (PostgreSQL via `pg_dump` dans le
conteneur `db`, ou SQLite en mode sans Docker) vers `backups/`, avec un nom
horodaté, puis supprime automatiquement les sauvegardes de plus de
`BACKUP_RETENTION_DAYS` jours (14 par défaut, réglable dans `.env`).

**Planifier l'exécution toutes les 4h**, dans PowerShell **en administrateur**,
depuis le dossier du projet :

```powershell
.\scripts\register_backup_task.ps1
```

Cela crée une tâche planifiée Windows `LaCaveDuCoin-Backup` visible dans
`taskschd.msc`. Vérifiez après quelques heures que des fichiers apparaissent
dans `backups/`.

**Restaurer une sauvegarde** :
- PostgreSQL : `docker compose exec -T db psql -U cave_du_coin cave_du_coin < backups/cave_du_coin_XXXXXXXX.sql`
- SQLite : remplacer `cave_du_coin.db` par le fichier de `backups/` (appli arrêtée).

### Copie hors-site (protection panne/vol du PC)

Par défaut, les sauvegardes restent sur le même PC — insuffisant en cas de
panne disque, vol ou incendie. Le script peut aussi copier chaque sauvegarde
vers un dossier synchronisé OneDrive ou Google Drive :

1. Installer **OneDrive** (déjà présent sur Windows 11) ou **Google Drive
   Desktop**, et se connecter avec un compte.
2. Créer un dossier dédié, par exemple `OneDrive\SauvegardesCaisse`.
3. Dans `.env`, renseigner :
   ```
   OFFSITE_BACKUP_DIR=C:\Users\VotreNom\OneDrive\SauvegardesCaisse
   ```
4. Relancer `python scripts/backup.py` : chaque sauvegarde est désormais aussi
   copiée dans ce dossier, qui se synchronise seul vers le cloud dès que le PC
   a une connexion internet. La purge des sauvegardes de plus de
   `BACKUP_RETENTION_DAYS` jours s'applique aussi à ce dossier.

Si OneDrive/Google Drive n'est pas encore synchronisé au moment de la
sauvegarde (pas de connexion, dossier non monté), le script continue sans
planter : la sauvegarde locale est conservée et un message d'avertissement est
affiché — la copie se fera au prochain passage.

## Alternative sans Docker

Si vous préférez éviter Docker Desktop, la même chose fonctionne avec Python
directement (SQLite au lieu de PostgreSQL, suffisant pour un seul point de
vente) :

```bash
cd La_Cave_du_Coin
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m alembic upgrade head
.venv\Scripts\python.exe scripts\seed_data.py
```

Puis créez une **tâche planifiée Windows** (`taskschd.msc`) :
- Déclencheur : "Au démarrage" (ou "À la connexion" + ouverture de session auto)
- Action : lancer
  `C:\chemin\La_Cave_du_Coin\.venv\Scripts\pythonw.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000`
- Cocher "Exécuter avec les autorisations maximales"

Les étapes 4 (pare-feu) et 5 (accès réseau) du guide Docker s'appliquent à
l'identique.
