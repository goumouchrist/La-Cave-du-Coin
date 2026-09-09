# La Cave du Coin — Logiciel Caisse & Stock (Boissons)

Logiciel de gestion de caisse et de stock pour un débit de boissons, développé à
partir du cahier des charges [`Specification_Logiciel_Caisse_Boissons-1.pdf`](Specification_Logiciel_Caisse_Boissons-1.pdf).
Monnaie : **Franc Guinéen (GNF)**.

![La Cave du Coin](logo.png)

## Sommaire

- [Périmètre couvert dans cette version](#périmètre-couvert-dans-cette-version)
- [Hors périmètre (v1)](#hors-périmètre-v1)
- [Stack technique](#stack-technique)
- [Installation & lancement en local](#installation--lancement-en-local)
- [Comptes de démonstration](#comptes-de-démonstration)
- [Tests unitaires](#tests-unitaires)
- [Utilisation](#utilisation)
- [Règles anti-fraude implémentées](#règles-anti-fraude-implémentées)
- [Modèle de données](#modèle-de-données)
- [API REST](#api-rest)
- [Déploiement (MEP)](#déploiement-mep)
- [Migrations de schéma](#migrations-de-schéma)
- [Limites connues](#limites-connues)

## Périmètre couvert dans cette version

- **Utilisateurs & sécurité** : rôles Admin / Manager / Caissier, authentification
  par identifiant + mot de passe (hash bcrypt), jeton JWT, permissions par rôle
  (le caissier ne peut ni modifier les prix, ni valider un inventaire), journal
  `logs` de toutes les actions sensibles (connexion, ventes, annulations,
  mouvements de stock, ouverture/fermeture de caisse).
- **Caisse** : ouverture avec fond de caisse initial, vente avec calcul
  automatique de la monnaie à rendre (arrondi au multiple de 50 GNF), modes de
  paiement Espèces / Mobile Money / Crédit, fermeture avec rapprochement
  théorique/physique et **blocage automatique si l'écart dépasse le seuil**
  (10 000 GNF par défaut).
- **Retours clients & avoir** — **décision actée** : un retour crédite un
  compte client (`customers`, identifié par téléphone) plutôt qu'un
  remboursement en espèces. Une vente peut ensuite être payée avec ce solde
  (mode de paiement `avoir`). Le stock est automatiquement réapprovisionné, et
  le système empêche de retourner plus que la quantité effectivement vendue
  sur un ticket (même en plusieurs fois).
- **TVA** — **décision actée** : non appliquée pour cette version (le champ
  `tva_rate` reste en base par produit pour une activation future si besoin).
- **Stock** : catégories de boissons, unités Pièce/Carton/Pack avec
  **conversion automatique** vers l'unité de base, mouvements
  entrée/sortie-vente/casse/don/ajustement, **workflow de double validation**
  (saisie + supervision) pour tout mouvement hors vente, alertes de seuil bas.
- **Fournisseurs** : fiche fournisseur (nom, téléphone, adresse), rattachée en
  fournisseur habituel sur un produit et/ou à chaque mouvement d'entrée
  (avec n° de facture), avec **historique des livraisons par fournisseur**.
- **Reçus** : génération PDF (format ticket 80mm) avec toutes les mentions
  obligatoires du cahier des charges (magasin, NIF, n° transaction, caissier,
  détail des lignes, mention légale, QR code), marquage **DUPLICATA** en cas de
  réimpression.
- **Statistiques & prédiction** : top 5 des ventes sur 7 jours, prévision de
  rupture de stock (moyenne mobile 30 jours, alerte si rupture < 3 jours),
  prévision du chiffre d'affaires du lendemain (régression linéaire simple),
  tableau de bord avec graphiques (ventes par catégorie, par caissier).
- **Scan / codes-barres** : recherche produit par code-barres (compatible avec
  un lecteur USB/Bluetooth en émulation clavier), détection de double scan en
  moins de 2 secondes, journal `scan_logs`.
- **Règles anti-fraude** : voir [section dédiée](#règles-anti-fraude-implémentées).
- **API REST** complète (FastAPI, documentation interactive sur `/docs`), pensée
  pour être consommée par un futur site web ou une application mobile.

## Hors périmètre (v1)

Ces points du cahier des charges sont documentés mais **non implémentés** dans
cette première version, pour rester sur un produit livrable et testé plutôt
qu'une coquille vide :

- Redis (cache des prédictions) : les calculs sont faits à la demande, sans
  cache dédié — suffisant au volume d'une seule boutique.
- Multi-magasins : **décision actée** — un seul point de vente pour cette
  version, la base est conçue en conséquence.
- Intégration matérielle réelle (driver de douchette, imprimante thermique,
  imprimante d'étiquettes QR) : le scan fonctionne via saisie clavier (ce que
  fait nativement tout lecteur de code-barres USB/Bluetooth en émulation
  clavier), l'impression du ticket se fait en PDF (à imprimer depuis le
  navigateur sur l'imprimante thermique).
- Double authentification (2FA) pour les grosses opérations.
- Envoi du reçu par SMS/email.
- Météo et jours fériés dans le module de prédiction.

## Stack technique

- **Backend** : Python 3.12+, [FastAPI](https://fastapi.tiangolo.com/),
  SQLAlchemy 2.
- **Base de données** : SQLite par défaut (dev/tests, zéro installation) ;
  bascule vers **PostgreSQL** en production via la seule variable d'environnement
  `DATABASE_URL` (aucune modification de code nécessaire).
- **Frontend** : pages HTML servies par FastAPI (Jinja2), JavaScript natif (pas
  de framework), [Chart.js](https://www.chartjs.org/) (CDN) pour les graphiques.
- **Reçus** : `reportlab` (PDF), `qrcode` (QR code).
- **Auth** : `passlib`/`bcrypt` + JWT (`PyJWT`).
- **Tests** : `pytest`, `httpx` (client de test FastAPI).
- **Migrations de schéma** : `Alembic` (voir [Migrations de schéma](#migrations-de-schéma)).

## Installation & lancement en local

Le `python` par défaut de Windows (alias Microsoft Store) ne fonctionne pas sur
ce poste ; utilisez l'interpréteur Anaconda existant ou tout Python 3.11+.

```bash
cd La_Cave_du_Coin

# 1. Environnement virtuel
"C:\Users\MOGOUMOU\AppData\Local\anaconda3\python.exe" -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements.txt

# 2. Configuration (optionnel — les valeurs par défaut fonctionnent en local)
cp .env.example .env

# 3. Créer le schéma de base (tables) via les migrations
./.venv/Scripts/python.exe -m alembic upgrade head

# 4. Créer les utilisateurs par défaut + produits de démonstration
./.venv/Scripts/python.exe scripts/seed_data.py

# 5. Lancer le serveur
./.venv/Scripts/python.exe -m uvicorn app.main:app --reload
```

Puis ouvrir [http://127.0.0.1:8000](http://127.0.0.1:8000) (interface web) ou
[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) (API/Swagger).

## Comptes de démonstration

Créés par `scripts/seed_data.py` :

| Identifiant | Mot de passe   | Rôle      |
|-------------|----------------|-----------|
| `admin`     | `Admin123!`    | Admin     |
| `manager`   | `Manager123!`  | Manager   |
| `caissier`  | `Caissier123!` | Caissier  |

**À changer immédiatement en production.**

## Tests unitaires

```bash
./.venv/Scripts/python.exe -m pytest -q
```

39 tests couvrant : permissions par rôle, conversions d'unités
(carton/pack/unité), ouverture/fermeture de caisse et blocage sur écart,
création de vente (stock, monnaie, règle des >5 articles identiques),
règles anti-fraude (annulation, prix minimum, duplicata, double validation
stock, double scan), et le module de prédiction (top ventes, prévision de
rupture, régression linéaire de CA). Base de données SQLite en mémoire,
aucune dépendance externe requise.

## Utilisation

1. **Sessions caisse** → un caissier ouvre sa session avec le fond de caisse.
2. **Caisse** → scanner/saisir un code-barres (ou cliquer un produit dans la
   liste "recherche rapide"), ajuster les quantités, choisir le mode de
   paiement, saisir le montant remis, valider. Le reçu PDF est accessible
   immédiatement après la vente.
3. **Stock** (Admin/Manager) → créer des produits, enregistrer les mouvements
   (réception fournisseur, casse, don, ajustement), valider les mouvements en
   attente (workflow à deux personnes).
4. **Statistiques** (Admin/Manager) → tableau de bord et prévisions.
5. **Utilisateurs** (Admin) → gestion des comptes.

## Règles anti-fraude implémentées

| Règle (cahier des charges) | Implémentation |
|---|---|
| Annulation réservée au Manager, ou au Caissier dans les 5 min avec motif | `app/services/sales.py::cancel_sale` |
| Prix de vente ≥ prix d'achat − 5 %, sauf promo | `app/services/products.py::validate_price` |
| 2e impression d'un ticket → `DUPLICATA` | `app/services/sales.py::register_print` |
| Modification de stock hors vente → double validation (saisie + supervision) | `app/services/stock.py::create_movement` / `validate_movement` |
| Ajustement d'inventaire → validation Admin uniquement | `app/services/stock.py::validate_movement` |
| Vente de > 5 articles identiques → confirmation de quantité requise | `app/services/sales.py::create_sale` |
| Double scan du même produit en < 2s → alerte | `app/services/scan.py::log_scan` |
| Toute action sensible tracée (utilisateur, IP, horodatage) | table `logs`, `app/services/logs.py` |

## Modèle de données

`users`, `products` (avec `barcode` unique indexé), `stock_movements`,
`cash_sessions`, `sales`, `sale_items`, `logs`, `scan_logs` — voir
[`app/models.py`](app/models.py) pour le détail des colonnes. Le stock courant
d'un produit n'est pas stocké mais **dérivé** des mouvements validés
(`app/services/products.py::get_current_stock_units`), pour garantir que la
traçabilité (§1 du cahier des charges) reste la source de vérité unique.

## API REST

Documentation interactive complète sur `/docs` une fois le serveur lancé.
Routers principaux : `/api/auth`, `/api/users`, `/api/products`,
`/api/stock`, `/api/suppliers`, `/api/cash-sessions`, `/api/sales`, `/api/stats`.

## Déploiement (MEP)

Guide complet : [DEPLOYMENT.md](DEPLOYMENT.md) — deux options documentées :
- **VPS distant** (recommandé si l'admin et la boutique ne sont pas au même
  endroit, ex. admin en France / boutique en Guinée) : app + PostgreSQL +
  HTTPS automatique (Caddy), accessible depuis n'importe où.
- **PC de la boutique en réseau local** : zéro coût d'hébergement, mais
  accessible seulement depuis le Wi-Fi de la boutique.

Un package Docker est fourni pour un déploiement de type production
(PostgreSQL au lieu de SQLite) :

```bash
cp .env.example .env   # renseigner POSTGRES_PASSWORD et JWT_SECRET
docker compose up -d --build
# Le conteneur applique automatiquement les migrations Alembic à chaque démarrage
# (cf. Dockerfile) avant de lancer le serveur — patientez quelques secondes.

# Première initialisation (utilisateurs + produits de démo) :
docker compose exec app python scripts/seed_data.py
```

L'application est alors disponible sur `http://<serveur>:8000`.

### ⚠️ Limite assumée

**Docker n'est pas installé sur la machine utilisée pour développer ce projet**,
je n'ai donc pas pu exécuter réellement `docker compose up` pour valider le
build de bout en bout. Les fichiers (`Dockerfile`, `docker-compose.yml`) suivent
des patterns standards et éprouvés, mais **il faut valider ce déploiement sur
une machine disposant de Docker (ou le serveur cible) avant une mise en
production réelle**. Le lancement en local sans Docker (section
Installation) a lui été entièrement testé et fonctionne.

## Migrations de schéma

Le schéma de base est géré par [Alembic](https://alembic.sqlalchemy.org/)
(`migrations/`), pas par `Base.metadata.create_all` — nécessaire pour faire
évoluer la base **sans perdre les données** une fois de vraies ventes
enregistrées.

- **Appliquer les migrations** (à faire avant tout premier lancement, et après
  chaque mise à jour du code) :
  ```bash
  ./.venv/Scripts/python.exe -m alembic upgrade head
  ```
  En Docker, c'est fait automatiquement à chaque démarrage du conteneur `app`.
- **Après avoir modifié `app/models.py`**, générer la migration correspondante :
  ```bash
  ./.venv/Scripts/python.exe -m alembic revision --autogenerate -m "description du changement"
  ```
  Relire le fichier généré dans `migrations/versions/` avant de l'appliquer
  (Alembic ne détecte pas tout parfaitement, notamment les renommages de
  colonnes), puis `alembic upgrade head` pour l'exécuter.
- **Revenir en arrière** si besoin : `alembic downgrade -1`.

Les tests (`pytest`) n'utilisent pas Alembic : ils recréent un schéma neuf à
chaque test via `Base.metadata.create_all` sur une base SQLite jetable,
indépendamment de l'historique des migrations — c'est volontaire, pour rester
rapides.

## Limites connues

- Le tableau de bord charge Chart.js depuis un CDN (nécessite une connexion
  internet) ; à héberger en local si la boutique n'a pas d'accès internet fiable.
