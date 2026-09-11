# Guide de formation — La Cave du Coin

Ce document explique, étape par étape, comment utiliser le logiciel de caisse
et de stock de La Cave du Coin. Il est organisé **par rôle** : chaque personne
n'a besoin de lire que sa section (+ les sections des rôles "en dessous" du
sien, puisque chaque rôle hérite des droits des rôles plus bas).

## Sommaire

1. [Prise en main (tout le monde)](#1-prise-en-main-tout-le-monde)
2. [Guide du Caissier](#2-guide-du-caissier)
3. [Guide du Manager](#3-guide-du-manager-en-plus-du-caissier)
4. [Guide de l'Admin](#4-guide-de-ladmin-en-plus-du-manager)
5. [Le Super Admin](#5-le-super-admin)
6. [Règles anti-fraude à connaître](#6-règles-anti-fraude-à-connaître)
7. [Questions fréquentes / dépannage](#7-questions-fréquentes--dépannage)

Les 4 rôles, du plus limité au plus large :

| Rôle | Peut faire |
|---|---|
| **Caissier** | Vendre, encaisser, ouvrir/fermer sa caisse, gérer les retours et les créances clients |
| **Manager** | Tout ce que fait le Caissier + gérer le stock, les fournisseurs, les statistiques, annuler une vente sans limite de temps |
| **Admin** | Tout ce que fait le Manager + créer/gérer les comptes utilisateurs (sauf comptes Admin/Super Admin) |
| **Super Admin** | Tout, y compris gérer les comptes Admin (le seul qui le peut) |

---

## 1. Prise en main (tout le monde)

### 1.1 Se connecter

1. Ouvrir l'adresse du site dans un navigateur (ex: `https://lacaveducoin.com`).
2. Saisir son **identifiant** et son **mot de passe**, cliquer sur "Se connecter".
3. On arrive sur la page **Caisse**.

En haut de chaque page, un menu affiche uniquement les pages autorisées pour
votre rôle, votre nom d'utilisateur, et un bouton **Déconnexion**.

### 1.2 Déconnexion automatique après 15 minutes d'inactivité

Si personne ne touche ni la souris ni le clavier pendant **15 minutes**, le
système déconnecte automatiquement l'utilisateur et affiche un message sur la
page de connexion. C'est une mesure de sécurité (éviter qu'une session reste
ouverte sans surveillance sur l'ordinateur de la boutique).

**Important : cela n'affecte jamais les ventes déjà enregistrées ni la session
de caisse en cours.** Il suffit de se reconnecter avec le même compte pour
reprendre exactement là où on s'est arrêté (la caisse reste ouverte).

### 1.3 Changer son mot de passe

Menu **"Mon compte"** → saisir l'ancien mot de passe puis le nouveau (6
caractères minimum) → **Valider**. Chaque utilisateur peut changer son propre
mot de passe à tout moment ; il n'a besoin de personne pour cela.

---

## 2. Guide du Caissier

C'est le rôle qui utilise le plus l'application au quotidien : ouvrir la
caisse, vendre, encaisser, fermer la caisse.

### 2.1 Ouvrir sa session de caisse (obligatoire avant de vendre)

Menu **"Sessions caisse"** :
1. Saisir le **fond de caisse initial** (l'argent déjà présent dans le tiroir
   au démarrage), en GNF.
2. Cliquer **"Ouvrir"**.

Sans session ouverte, la page de vente affiche un message d'erreur et bloque
toute vente.

### 2.2 Enregistrer une vente

Menu **"Caisse"** :

1. **Ajouter des produits au panier** de deux façons :
   - Scanner le code-barres avec la douchette (ou le taper au clavier + Entrée)
     dans le champ en haut de la page.
   - Cliquer directement sur un produit dans la liste "recherche rapide".
2. **Ajuster les quantités** avec les boutons `+` / `-` sur chaque ligne du
   panier, ou retirer une ligne avec le bouton `X`.
3. **Choisir le mode de paiement** dans la liste déroulante :
   - **Espèces**, **Mobile Money**, **Soutra Money**, **Crédit Money**,
     **Paycard** : les plus simples, rien de particulier à faire.
   - **Avoir** *(solde crédité suite à un retour)* : le client a déjà un solde
     avoir (voir [2.4](#24-retour-client-et-avoir)). Saisir son numéro de
     téléphone dans le champ dédié et cliquer "Vérifier le solde" avant de
     valider — le système affiche le solde disponible.
   - **Crédit (client fidèle)** : voir la section suivante, dédiée.
4. **Saisir le montant remis** par le client (GNF). La monnaie à rendre
   s'affiche automatiquement (arrondie à 50 GNF).
5. Cliquer **"Valider la vente"**.
6. Après validation, cliquer **"Imprimer le reçu"** pour générer le ticket PDF.
   Une deuxième impression du même ticket est automatiquement marquée
   **DUPLICATA**.

**Vente de plus de 5 articles identiques** : le système demande une
confirmation explicite (bouton "Confirmer" sur la ligne) avant de valider —
c'est normal, c'est une protection anti-fraude (voir [section 6](#6-règles-anti-fraude-à-connaître)).

### 2.3 Vente à crédit pour un client fidèle

Si un client ne peut payer qu'une partie du montant, choisir le mode de
paiement **"Crédit (client fidèle)"** :

1. Un bloc apparaît. Rechercher le client par téléphone (bouton "Rechercher")
   — s'il existe déjà, son nom et son adresse se remplissent automatiquement.
2. S'il est nouveau, saisir son **nom et prénom**, son **numéro de téléphone**
   et son **adresse**.
3. Renseigner la **date de remboursement prévue** (facultatif mais recommandé).
4. Saisir le montant que le client remet réellement, puis valider la vente.

Le reste à payer est automatiquement enregistré comme une **créance** sur ce
client (visible dans "Créances clients", voir [2.5](#25-créances-clients)). Le
reçu imprimé affiche le montant restant dû et l'échéance.

**Limite importante : un même client ne peut pas avoir plus de 2 créances non
réglées en même temps.** Si vous tentez une 3ᵉ vente à crédit pour un client
qui a déjà 2 créances en cours, le système **refuse la vente** et affiche un
message d'alerte ("a dépassé le nombre de crédits autorisés"). Il faut
d'abord régler au moins une de ses créances en cours (voir [2.5](#25-créances-clients))
avant de pouvoir lui refaire crédit. Le compteur revient automatiquement à
zéro dès que toutes ses créances sont réglées.

### 2.4 Retour client et avoir

Un client qui rapporte un article acheté n'est **jamais remboursé en
espèces** : son montant est crédité sur un compte "avoir" qu'il pourra
utiliser pour un futur achat.

Dans la section **"Retour client (avoir)"** de la page Caisse :
1. Saisir le **numéro de transaction** du ticket d'origine (imprimé sur le
   reçu), cliquer "Rechercher le ticket".
2. Indiquer la **quantité à retourner** sur chaque ligne concernée (on ne peut
   pas retourner plus que ce qui a été vendu, même en plusieurs fois).
3. Saisir le **nom et le téléphone** du client (le téléphone identifie son
   compte avoir : s'il existe déjà, le solde s'additionne).
4. Indiquer un motif, puis cliquer **"Créditer le client (avoir)"**.

Le stock est automatiquement réapprovisionné, et le solde avoir du client
augmente du montant retourné. Le client pourra ensuite l'utiliser via le mode
de paiement "Avoir" (voir [2.2](#22-enregistrer-une-vente)).

### 2.5 Créances clients

Menu **"Créances clients"** : liste de tous les clients ayant une créance en
cours (vente à crédit non intégralement payée), triée du plus urgent au moins
urgent (échéance la plus ancienne en premier).

Pour enregistrer un règlement :
1. Saisir le **montant réglé** par le client dans le champ de la ligne
   correspondante.
2. Cliquer **"Enregistrer"**.
3. Un bouton **"Imprimer le reçu"** apparaît : c'est la preuve de paiement à
   remettre au client.

Si le client règle tout, il disparaît de la liste. S'il ne règle qu'une
partie, le montant restant dû est mis à jour et sa dette la plus ancienne est
réglée en priorité (utile s'il a deux créances en cours). Chaque règlement est
tracé (qui l'a encaissé, quand, combien) — rien n'est perdu.

### 2.6 Fermer sa session de caisse

Menu **"Sessions caisse"** :
1. Compter physiquement l'argent présent dans la caisse.
2. Saisir ce **montant physique compté** dans le champ dédié.
3. Cliquer **"Fermer"**.

Le système compare ce montant au montant théorique (fond de caisse initial +
ventes espèces enregistrées) et affiche l'écart. **Si l'écart dépasse 10 000
GNF, la session est automatiquement bloquée** et nécessite une validation par
un Manager — c'est normal, ce n'est pas une erreur du logiciel.

---

## 3. Guide du Manager (en plus du Caissier)

### 3.1 Gérer le stock

Menu **"Stock"** :

- **Créer un produit** : désignation, catégorie, code-barres (si le fabricant
  en fournit un), unités par carton/pack (pour la conversion automatique),
  prix d'achat, prix de vente, seuil d'alerte (en cartons), taux de TVA
  (facultatif, informatif uniquement — n'est pas ajouté au prix), fournisseur
  habituel.
- **Enregistrer un mouvement de stock** : entrée (réception fournisseur),
  casse, don, ou ajustement d'inventaire. Choisir le produit, la quantité (en
  unité, carton ou pack — la conversion est automatique), et pour une entrée,
  le fournisseur et le numéro de facture.

**Important : tout mouvement hors vente reste "en attente" jusqu'à ce
qu'une deuxième personne le valide** (voir tableau "Mouvements en attente de
validation" en bas de page, boutons "Valider" / "Rejeter"). C'est une
protection anti-fraude : la personne qui saisit un mouvement ne peut pas être
celle qui le valide. **Un ajustement d'inventaire doit obligatoirement être
validé par un Admin** (le Manager ne peut valider que les entrées/casses/dons).

### 3.2 Fournisseurs

Toujours dans la page **"Stock"**, section "Fournisseurs" :
- **Ajouter** un fournisseur (nom, téléphone, adresse).
- **Voir** son historique de livraisons (bouton "Voir").
- **Supprimer** un fournisseur (bouton "Supprimer") : l'historique des
  livraisons déjà enregistrées est conservé, seul le fournisseur devient
  inactif (il n'apparaît plus dans les listes pour de nouvelles saisies).

### 3.3 Codes-barres internes et étiquettes

Pour un produit sans code-barres fournisseur (produit local, vrac, etc.) :
dans le tableau "Produits & stock courant", cliquer **"Générer code interne"**
— le système attribue un code-barres unique. Une fois le produit doté d'un
code-barres (fournisseur ou interne), le bouton devient **"Imprimer
étiquette"** : génère une étiquette PDF à imprimer et coller sur le produit.

### 3.4 Import en masse par CSV

Toujours dans "Stock" :
- **Import du catalogue** : ajouter plusieurs produits d'un coup via un
  fichier CSV (télécharger le modèle avec le bouton dédié pour avoir le bon
  format de colonnes).
- **Import de mouvements de stock** : idem pour des mouvements (chaque ligne
  importée reste en attente de validation, comme une saisie manuelle).

### 3.5 Modifier le taux de TVA d'un produit

Dans le tableau produits, bouton "Modifier" à côté du taux de TVA affiché.
Ce taux est **uniquement informatif** : il apparaît sur le reçu ("Dont TVA :
...") mais n'est pas ajouté au prix affiché/facturé.

### 3.6 Statistiques et prévisions

Menu **"Statistiques"** :
- Top 5 des ventes des 7 derniers jours.
- Répartition des ventes par catégorie et par caissier.
- Prévision du chiffre d'affaires du lendemain.
- Alertes de rupture de stock (produits qui vont manquer bientôt, avec le
  nombre de jours restants estimé).

### 3.7 Annuler une vente

Règle métier : un Manager peut annuler n'importe quel ticket, à tout moment.
Un Caissier ne peut annuler que dans les **5 minutes** suivant la vente, et
doit obligatoirement indiquer un motif. Un ticket annulé n'est jamais
supprimé : il garde une trace ("annulé", avec le motif et l'auteur).

> ⚠️ **Note** : cette action existe côté logiciel mais n'a pas encore de
> bouton dédié sur la page Caisse. Si vous avez besoin d'annuler un ticket au
> quotidien, signalez-le pour qu'on ajoute le bouton correspondant.

---

## 4. Guide de l'Admin (en plus du Manager)

Menu **"Utilisateurs"** :

- **Créer un compte** : identifiant, nom complet, mot de passe initial, rôle
  (Caissier / Manager / Admin — **pas** Super Admin, réservé au Super Admin
  lui-même).
- **Réinitialiser le mot de passe** d'un utilisateur qui l'a oublié (bouton
  "Réinitialiser mot de passe").
- **Désactiver / réactiver** un compte (bouton "Désactiver"/"Réactiver") — un
  compte désactivé ne peut plus se connecter, mais tout son historique
  (ventes, mouvements) reste intact et consultable.

**Un Admin ne peut ni créer, ni modifier le mot de passe, ni désactiver un
compte Admin ou Super Admin** — seul le Super Admin en a le droit (voir
section suivante). C'est volontaire : un Admin ne doit pas pouvoir neutraliser
un autre Admin ou s'accorder plus de droits que prévu.

Un Admin peut également **supprimer** un produit ou un fournisseur (bouton
"Supprimer" dans la page Stock) : comme pour les comptes, il s'agit d'une
désactivation qui conserve tout l'historique lié.

---

## 5. Le Super Admin

Le Super Admin a exactement les mêmes pages et fonctions que l'Admin, avec un
seul pouvoir en plus : **gérer les comptes Admin et Super Admin**
(les créer, réinitialiser leur mot de passe, les désactiver/réactiver).

C'est un rôle de secours à réserver à une seule personne de confiance (par
exemple le propriétaire ou le responsable IT), pas à utiliser au quotidien.
Le compte `superadmin` créé par défaut existe précisément pour garantir qu'il
y ait toujours au moins un compte capable de gérer les Admins, même si tous
les comptes Admin sont un jour bloqués par erreur.

---

## 6. Règles anti-fraude à connaître

Ces règles sont automatiques (impossible de les contourner depuis
l'interface) — bon à savoir pour comprendre pourquoi le système refuse
parfois une action :

| Règle | Seuil actuel |
|---|---|
| Annulation d'un ticket par un Caissier | possible seulement dans les 5 minutes suivant la vente, motif obligatoire |
| Annulation d'un ticket par un Manager/Admin | possible à tout moment |
| Vente de plusieurs articles identiques | confirmation manuelle requise au-delà de **5** unités du même produit dans le panier |
| Double scan du même produit | alerte si moins de **2 secondes** entre les deux scans |
| Écart de caisse à la fermeture | session bloquée si l'écart dépasse **10 000 GNF**, nécessite une validation Manager |
| Mouvement de stock hors vente | doit être validé par une **personne différente** de celle qui l'a saisi |
| Ajustement d'inventaire | validation réservée à un **Admin** (ou Super Admin) |
| Vente à crédit non réglée par client | maximum **2 créances en cours** par client, sinon vente refusée |
| Prix de vente d'un produit | ne peut pas descendre en dessous du prix d'achat − 5 %, sauf si marqué "promo" |
| Réimpression d'un ticket | automatiquement marquée **DUPLICATA** |

Toutes ces actions (ventes, annulations, mouvements de stock, ouverture/
fermeture de caisse, règlements de créances, tentatives refusées...) sont
enregistrées dans un journal interne avec l'auteur, la date/heure, et le
détail — rien n'est jamais supprimé.

---

## 7. Questions fréquentes / dépannage

**"Je viens d'être déconnecté tout seul, j'ai perdu ma vente en cours ?"**
Non. La déconnexion automatique après 15 minutes d'inactivité n'efface
aucune donnée : reconnectez-vous avec le même compte, la session de caisse et
tout l'historique sont intacts. Seul le panier en cours de saisie (non encore
validé) doit être refait, comme un formulaire qu'on n'a jamais envoyé.

**"Je ne peux pas ouvrir de session de caisse / vendre."**
Vérifiez qu'une session de caisse n'est pas déjà ouverte (parfois par un
collègue avant vous) et que votre compte est bien actif.

**"Je n'arrive pas à créer un compte Admin."**
C'est normal, c'est réservé au Super Admin (voir [section 5](#5-le-super-admin)).

**"Le stock ne bouge pas après une réception fournisseur."**
Un mouvement de stock hors vente reste "en attente" jusqu'à ce qu'une
**deuxième personne** le valide dans "Stock" → "Mouvements en attente de
validation". C'est volontaire (double contrôle).

**"Le système refuse ma vente à crédit."**
Le client a probablement déjà 2 créances non réglées en cours (voir
[2.3](#23-vente-à-crédit-pour-un-client-fidèle)). Réglez au moins une de ses
créances existantes dans "Créances clients" avant de lui refaire crédit.

**"La fermeture de caisse affiche 'blocked' / statut bloqué."**
L'écart entre le montant théorique et le montant physique compté dépasse
10 000 GNF. Un Manager doit intervenir pour vérifier et débloquer.

**"Je veux supprimer un produit ou un fournisseur par erreur créé."**
La "suppression" désactive l'élément sans effacer son historique (ventes,
livraisons). Il n'apparaît plus dans les listes pour de nouvelles saisies,
mais rien n'est perdu.
