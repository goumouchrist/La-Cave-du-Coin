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

Tant qu'une session est ouverte, le menu **"Sessions caisse"** affiche une
**répartition des ventes par mode de paiement** (Espèces, Mobile Money,
Paycard, etc.) — utile pour vérifier ce qui a été vendu avant de compter le
tiroir. **Seul le total Espèces doit se retrouver physiquement dans le
tiroir** : les autres modes (Mobile Money, Paycard, Crédit...) ne mettent pas
d'argent liquide en caisse.

En dessous, un tableau **"Mouvements espèces de la session"** liste chaque
vente payée en espèces au fil de la journée (heure, numéro de transaction,
montant) avec un **total cumulé** qui part du fond de caisse initial et
s'additionne à chaque vente. À tout moment de la journée — pas seulement à la
fermeture — ce total cumulé doit correspondre exactement à ce qu'il y a
physiquement dans le tiroir. La page se rafraîchit automatiquement toutes les
15 secondes, ce qui permet à un Manager de suivre la caisse en temps réel
depuis un autre poste pendant que le caissier vend.

Pour fermer :
1. Compter physiquement l'argent présent dans la caisse.
2. Saisir ce **montant physique compté** dans le champ dédié.
3. Cliquer **"Fermer"**.

Le système compare ce montant au montant théorique (fond de caisse initial +
total des ventes Espèces de la session) et affiche l'écart. **Si l'écart
dépasse 10 000 GNF, la session est automatiquement bloquée** et nécessite une
validation par un Manager — c'est normal, ce n'est pas une erreur du logiciel.

Un tableau **"Historique des sessions"** en bas de la page liste toutes les
sessions passées (fond initial, théorique, physique, écart, statut) pour
pouvoir suivre les écarts dans le temps.

**Résolution d'une session bloquée** *(Manager/Admin/Super Admin uniquement)* :
sur la ligne d'une session au statut "blocked", un bouton **"Résoudre"**
apparaît dans la colonne "Résolution". Cliquer dessus demande un
**commentaire obligatoire** expliquant l'écart (ex: "erreur de comptage
vérifiée avec le caissier"), puis clôture réellement la session (statut
"closed"). Le commentaire, l'auteur et la date restent visibles dans
l'historique — rien n'est perdu, et l'écart initial reste consultable même
après résolution.

### 2.7 Créer un devis pour un client

Un client qui veut connaître le prix avant d'acheter peut se voir remettre un
**devis**, sans qu'il y ait d'encaissement ni de sortie de stock. Sur la page
**"Caisse"**, en dessous du panier :

1. Ajouter les produits souhaités au panier, comme pour une vente normale.
2. Renseigner le **nom et le téléphone** du client — **obligatoires** (c'est ce
   qui permet de retrouver le devis plus tard si le client perd son numéro,
   voir la recherche par client dans [2.8](#28-convertir-un-devis-en-vente)).
3. Cliquer **"Créer un devis"**.
4. Le devis reçoit un numéro unique (ex : `DEV-...`) et une date de validité
   (**15 jours** par défaut). Cliquer **"Imprimer le devis"** pour le remettre
   au client.

**Contrairement à une vente, créer un devis ne nécessite pas de session de
caisse ouverte** — possible même caisse fermée.

**Le prix indiqué sur le devis est figé au moment de sa création** : si le
client revient l'acheter plus tard et que le prix de vente a changé
entre-temps, c'est le prix du devis (celui imprimé) qui sera appliqué à la
conversion, pas le prix courant du produit.

**La confirmation anti-fraude au-delà de 5 articles identiques (voir
[section 6](#6-règles-anti-fraude-à-connaître)) s'applique aussi à la création
d'un devis**, exactement comme pour une vente normale.

> **Cas d'usage fréquent : un client n'a pas de cash sur lui et doit aller
> retirer de l'argent, pendant qu'il y a la file d'attente.** C'est le bon
> réflexe d'utiliser le devis dans ce cas, même s'il ne s'agit pas d'une
> simple demande de prix : créer le devis pour son panier, lui remettre le
> numéro imprimé comme "ticket de rappel", et continuer à servir les clients
> suivants. Quand il revient, on charge son devis (section
> [2.8](#28-convertir-un-devis-en-vente)) pour finaliser la vente.
>
> ⚠️ **Règle à respecter absolument dans ce cas : ne jamais remettre la
> marchandise au client avant l'encaissement réel (la conversion du devis en
> vente).** Le devis n'est qu'une promesse de prix, pas une preuve de
> paiement — les articles restent derrière le comptoir jusqu'à ce que la vente
> soit validée à son retour.

### 2.8 Convertir un devis en vente

Quand le client revient pour acheter ce qui figure sur son devis, dans la
section **"Convertir un devis en vente"** de la page Caisse :

1. Saisir le **numéro du devis** (imprimé sur le document remis au client),
   cliquer **"Charger le devis"**.
2. Le détail s'affiche : articles, total, client, statut, date de validité.
3. Choisir le **mode de paiement** et saisir le **montant remis**, comme pour
   une vente normale.
4. Cliquer **"Convertir en vente"**.

**Cette étape nécessite une session de caisse ouverte**, contrairement à la
création du devis : c'est une vraie vente qui décrémente le stock et encaisse
le paiement, avec son propre reçu imprimable.

Un devis ne peut être converti **qu'une seule fois**. Un devis dont la date de
validité est dépassée ne peut plus être converti (le formulaire est désactivé
au chargement) — il faut alors refaire un nouveau devis pour ce client.

**Client sans son numéro de devis ?** Juste en dessous du champ numéro, un
champ **"Nom ou téléphone du client"** permet de retrouver ses devis en cours
sans connaître le numéro — cliquer "Rechercher", puis "Charger" sur la ligne
correspondante. C'est justement pour que cette recherche fonctionne que le nom
et le téléphone sont obligatoires à la création du devis.

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
  le fournisseur, le numéro de facture, et la **date de péremption du lot**
  (facultative — utile pour les produits alimentaires/périssables). **Pour un
  ajustement uniquement**, la quantité peut être négative (ex : `-12`) pour
  signaler un **manque** constaté ; une valeur positive signale un
  **surplus**. Pour tous les autres types de mouvement, la quantité doit
  rester positive.
- **Suivi des dates de péremption par lot** : chaque entrée avec une date de
  péremption forme un lot distinct — si plusieurs livraisons d'un même
  produit sont en stock en même temps avec des dates différentes, le système
  sait exactement lequel expire le plus tôt et considère qu'il est consommé
  en priorité (méthode FEFO — premier expiré, premier sorti). Les lots dont
  la péremption approche (7 jours par défaut) apparaissent automatiquement
  dans "Alertes de péremption" sur la page **Statistiques** (voir
  [3.6](#36-statistiques-et-prévisions)).
- **Fiche d'inventaire à l'aveugle** : bouton dédié au-dessus du tableau
  "Produits & stock courant" — génère un PDF listant tous les produits actifs
  (catégorie, code-barres, unités par carton/pack) avec des colonnes vides à
  remplir à la main, **sans afficher le stock théorique du système**. Pensé
  pour faire compter physiquement le stock par une tierce personne sans la
  biaiser (voir [3.8](#38-comptages-physiques-réguliers-protection-contre-la-substitution-de-produits)).

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
- **Section "Aujourd'hui"** en haut de la page : CA du jour, nombre de ventes,
  nombre de devis créés/convertis, nombre de mouvements de stock, et nombre
  d'écarts de caisse signalés — ainsi qu'un flux d'activité chronologique de
  la journée (ventes, devis, mouvements de stock, sessions caisse, créances,
  refus anti-fraude...). **Actualisation automatique toutes les 15 secondes**,
  pas besoin de recharger la page.
- Top 5 des ventes des 7 derniers jours.
- Répartition des ventes par catégorie et par caissier.
- Prévision du chiffre d'affaires du lendemain.
- Alertes de rupture de stock (produits qui vont manquer bientôt, avec le
  nombre de jours restants estimé).
- Alertes de péremption (lots dont la date de péremption approche, avec la
  quantité restante de ce lot précis — voir [3.1](#31-gérer-le-stock)).

### 3.7 Annuler une vente

Règle métier : un Manager peut annuler n'importe quel ticket, à tout moment.
Un Caissier ne peut annuler que dans les **5 minutes** suivant la vente, et
doit obligatoirement indiquer un motif. Un ticket annulé n'est jamais
supprimé : il garde une trace ("annulé", avec le motif et l'auteur).

> ⚠️ **Note** : cette action existe côté logiciel mais n'a pas encore de
> bouton dédié sur la page Caisse. Si vous avez besoin d'annuler un ticket au
> quotidien, signalez-le pour qu'on ajoute le bouton correspondant.

### 3.8 Comptages physiques réguliers (protection contre la substitution de produits)

**Le logiciel ne peut pas détecter une vente qui n'a jamais été saisie.** Si un
caissier malhonnête vend ses propres produits à la place de ceux de la
boutique (et empoche l'argent sans jamais toucher au stock ni à la caisse
officiels), aucune trace n'apparaît dans l'application — ni dans les ventes,
ni dans les mouvements de stock, ni dans l'écart de caisse à la fermeture. La
seule protection efficace contre ce type de fraude est un contrôle physique
régulier, en dehors du logiciel :

1. **Interdire tout stock ou objet personnel du caissier à proximité du poste
   de caisse et des rayons.** Une règle simple, affichée, sans exception.
2. **Faire compter physiquement le stock réel** par une personne extérieure
   si possible, à l'aide de la **fiche d'inventaire à l'aveugle** (bouton
   dans "Stock", voir [3.1](#31-gérer-le-stock)) — elle ne montre volontairement
   aucun chiffre du système, pour que le comptage ne soit pas influencé.
   À faire à une fréquence régulière (ex : chaque semaine), plus des
   comptages surprises non annoncés de temps en temps.
3. **Comparer ce comptage au stock théorique affiché** dans "Stock" →
   tableau "Produits & stock courant" (colonne stock courant, calculée à
   partir des mouvements validés), une fois la fiche remplie et signée.
4. **Si un écart est constaté**, l'enregistrer comme un mouvement de stock de
   type **"Ajustement"** (voir [3.1](#31-gérer-le-stock)) — quantité
   **négative** pour un manque, positive pour un surplus — avec un motif
   précis (ex : "comptage du 25/09 par [nom], vérifié par [Manager] : -12
   unités constatées vs stock système, à investiguer"). Ce mouvement
   nécessite une validation **Admin**, ce qui garantit qu'un écart n'est
   jamais discrètement corrigé sans qu'un responsable en soit informé.
5. **Un écart récurrent, toujours dans le même sens, sur les mêmes produits,
   ou concentré sur les sessions d'un même caissier** est le signal à
   surveiller — un comptage isolé prouve peu de choses, une tendance dans le
   temps est plus parlante.

Cette procédure ne remplace pas les règles automatiques de la
[section 6](#6-règles-anti-fraude-à-connaître), elle les complète : celles-ci
protègent contre la fraude *sur des ventes enregistrées*, celle-ci protège
contre les ventes *jamais enregistrées*.

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
| Vente de plusieurs articles identiques | confirmation manuelle requise au-delà de **5** unités du même produit dans le panier (s'applique aussi à la création d'un devis) |
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
10 000 GNF. Un Manager (ou Admin) doit vérifier l'écart avec le caissier puis
cliquer **"Résoudre"** sur la ligne correspondante dans l'historique des
sessions (menu "Sessions caisse"), en indiquant un commentaire expliquant
l'écart.

**"Le prix sur le devis imprimé n'est plus le même qu'en caisse."**
C'est normal : le prix d'un devis est **figé** au moment où il est créé. Si le
produit a changé de prix entre-temps, c'est le prix du devis (pas le prix
courant) qui sera appliqué lors de la conversion en vente (voir
[2.7](#27-créer-un-devis-pour-un-client)).

**"Je n'arrive pas à convertir un devis en vente."**
Deux causes possibles : aucune session de caisse n'est ouverte (contrairement
à la création d'un devis, la conversion en nécessite une), ou le devis a
dépassé sa date de validité (15 jours par défaut) — dans ce cas il faut
refaire un nouveau devis (voir [2.8](#28-convertir-un-devis-en-vente)).

**"Le système refuse ma quantité négative pour un mouvement de stock."**
Une quantité négative n'est acceptée que pour le type **"Ajustement"** (pour
signaler un manque constaté au comptage). Pour tous les autres types (entrée,
casse, don), la quantité doit rester positive.

**"Je veux supprimer un produit ou un fournisseur par erreur créé."**
La "suppression" désactive l'élément sans effacer son historique (ventes,
livraisons). Il n'apparaît plus dans les listes pour de nouvelles saisies,
mais rien n'est perdu.
