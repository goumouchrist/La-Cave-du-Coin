-- La Cave du Coin — schéma relationnel PostgreSQL
-- Généré depuis app/models.py — documentaire uniquement, le schéma réel de
-- la base est géré par Alembic (migrations/), jamais par ce fichier.
--
-- Note sur les types ENUM natifs PostgreSQL : SQLAlchemy stocke le NOM du
-- membre Python (ex: SUPER_ADMIN), pas sa valeur (ex: super_admin) — voir
-- migrations/versions/e26325b85a44_fix_enum_label_casing_for_postgresql.py.
-- Les valeurs ci-dessous sont donc en MAJUSCULES, pas les valeurs "métier"
-- (minuscules) qu'on voit côté API/JSON.

-- ============ ENUM TYPES ============

CREATE TYPE role AS ENUM ('ADMIN', 'CAISSIER', 'MANAGER', 'SUPER_ADMIN');
CREATE TYPE payment_mode AS ENUM ('ESPECES', 'MOBILE_MONEY', 'CREDIT', 'AVOIR', 'SOUTRA_MONEY', 'CREDIT_MONEY', 'PAYCARD');
CREATE TYPE movement_type AS ENUM ('ENTREE', 'SORTIE_VENTE', 'RETOUR', 'CASSE', 'DON', 'AJUSTEMENT');
CREATE TYPE movement_status AS ENUM ('PENDING', 'VALIDATED', 'REJECTED');
CREATE TYPE cash_session_status AS ENUM ('OPEN', 'CLOSED', 'BLOCKED');
CREATE TYPE sale_status AS ENUM ('VALIDE', 'ANNULEE');
CREATE TYPE quote_status AS ENUM ('EN_COURS', 'CONVERTI', 'ANNULE', 'EXPIRE');

-- ============ TABLES ============

CREATE TABLE users (
    id              SERIAL PRIMARY KEY,
    username        VARCHAR(50) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    full_name       VARCHAR(120) NOT NULL DEFAULT '',
    role            role NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_users_username ON users (username);

CREATE TABLE suppliers (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(150) NOT NULL,
    phone       VARCHAR(30),
    address     VARCHAR(255),
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE products (
    id                  SERIAL PRIMARY KEY,
    barcode             VARCHAR(20) UNIQUE,
    name                VARCHAR(150) NOT NULL,
    category            VARCHAR(50) NOT NULL,
    supplier_id         INTEGER REFERENCES suppliers(id),
    unit_carton_qty     INTEGER NOT NULL DEFAULT 24,
    unit_pack_qty       INTEGER NOT NULL DEFAULT 6,
    prix_achat          INTEGER NOT NULL,
    prix_vente          INTEGER NOT NULL,
    tva_rate            DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    stock_min_cartons   INTEGER NOT NULL DEFAULT 5,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_products_barcode ON products (barcode);

CREATE TABLE customers (
    id                  SERIAL PRIMARY KEY,
    name                VARCHAR(120) NOT NULL,
    phone               VARCHAR(30) UNIQUE,
    address             VARCHAR(255),
    -- Solde signé : positif = avoir (la boutique doit au client),
    -- négatif = dette (le client doit à la boutique)
    credit_balance_gnf  INTEGER NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_customers_phone ON customers (phone);

CREATE TABLE stock_movements (
    id              SERIAL PRIMARY KEY,
    product_id      INTEGER NOT NULL REFERENCES products(id),
    supplier_id     INTEGER REFERENCES suppliers(id),
    type            movement_type NOT NULL,
    qty_units       INTEGER NOT NULL,
    invoice_number  VARCHAR(50),
    -- Pertinent surtout pour une ENTREE : forme un "lot" pour le suivi FEFO
    -- (voir app/services/products.py::get_batches_remaining).
    expiry_date     DATE,
    reason          TEXT,
    status          movement_status NOT NULL DEFAULT 'VALIDATED',
    created_by      INTEGER NOT NULL REFERENCES users(id),
    validated_by    INTEGER REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    validated_at    TIMESTAMPTZ
);

CREATE TABLE cash_sessions (
    id                  SERIAL PRIMARY KEY,
    opened_by           INTEGER NOT NULL REFERENCES users(id),
    closed_by           INTEGER REFERENCES users(id),
    opening_amount      INTEGER NOT NULL,
    closing_theoretical INTEGER,
    closing_physical    INTEGER,
    gap_amount          INTEGER,
    status              cash_session_status NOT NULL DEFAULT 'OPEN',
    opened_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    closed_at           TIMESTAMPTZ,
    resolved_by         INTEGER REFERENCES users(id),
    resolved_at         TIMESTAMPTZ,
    resolution_comment  TEXT
);

CREATE TABLE sales (
    id                      SERIAL PRIMARY KEY,
    transaction_number      VARCHAR(40) NOT NULL UNIQUE,
    cash_session_id         INTEGER NOT NULL REFERENCES cash_sessions(id),
    cashier_id              INTEGER NOT NULL REFERENCES users(id),
    payment_mode            payment_mode NOT NULL,
    customer_id             INTEGER REFERENCES customers(id),
    total_amount            INTEGER NOT NULL,
    amount_given            INTEGER NOT NULL DEFAULT 0,
    change_amount           INTEGER NOT NULL DEFAULT 0,
    remaining_due_gnf       INTEGER NOT NULL DEFAULT 0,
    due_date                DATE,
    status                  sale_status NOT NULL DEFAULT 'VALIDE',
    cancelled_by            INTEGER REFERENCES users(id),
    cancel_reason           TEXT,
    cancelled_at            TIMESTAMPTZ,
    print_count             INTEGER NOT NULL DEFAULT 0,
    customer_email          VARCHAR(255),
    receipt_email_sent_at   TIMESTAMPTZ,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_sales_transaction_number ON sales (transaction_number);

CREATE TABLE sale_items (
    id                  SERIAL PRIMARY KEY,
    sale_id             INTEGER NOT NULL REFERENCES sales(id),
    product_id          INTEGER NOT NULL REFERENCES products(id),
    qty_units           INTEGER NOT NULL,
    unit_price          INTEGER NOT NULL,
    quantity_confirmed  BOOLEAN NOT NULL DEFAULT FALSE
);

-- Devis : prix figé au moment de la création, aucune sortie de stock ni
-- session de caisse requise. converted_sale_id est volontairement porté par
-- la table quotes (et non l'inverse) pour que sales/sale_items n'aient
-- aucune dépendance envers la fonctionnalité devis.
CREATE TABLE quotes (
    id                  SERIAL PRIMARY KEY,
    quote_number        VARCHAR(40) NOT NULL UNIQUE,
    created_by          INTEGER NOT NULL REFERENCES users(id),
    customer_id         INTEGER REFERENCES customers(id),
    customer_name       VARCHAR(120),
    customer_phone      VARCHAR(30),
    total_amount        INTEGER NOT NULL,
    status              quote_status NOT NULL DEFAULT 'EN_COURS',
    expires_at          DATE,
    converted_sale_id   INTEGER REFERENCES sales(id),
    converted_at        TIMESTAMPTZ,
    cancelled_at        TIMESTAMPTZ,
    print_count         INTEGER NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_quotes_quote_number ON quotes (quote_number);

CREATE TABLE quote_items (
    id          SERIAL PRIMARY KEY,
    quote_id    INTEGER NOT NULL REFERENCES quotes(id),
    product_id  INTEGER NOT NULL REFERENCES products(id),
    qty_units   INTEGER NOT NULL,
    -- Prix figé au moment du devis (snapshot), pas le prix courant du produit
    unit_price  INTEGER NOT NULL
);

CREATE TABLE customer_repayments (
    id              SERIAL PRIMARY KEY,
    customer_id     INTEGER NOT NULL REFERENCES customers(id),
    amount_gnf      INTEGER NOT NULL,
    payment_mode    payment_mode,
    processed_by    INTEGER NOT NULL REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE returns (
    id                  SERIAL PRIMARY KEY,
    sale_id             INTEGER NOT NULL REFERENCES sales(id),
    customer_id         INTEGER NOT NULL REFERENCES customers(id),
    processed_by        INTEGER NOT NULL REFERENCES users(id),
    reason              TEXT,
    total_refund_gnf    INTEGER NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE return_items (
    id              SERIAL PRIMARY KEY,
    return_id       INTEGER NOT NULL REFERENCES returns(id),
    sale_item_id    INTEGER NOT NULL REFERENCES sale_items(id),
    product_id      INTEGER NOT NULL REFERENCES products(id),
    qty_units       INTEGER NOT NULL,
    unit_price      INTEGER NOT NULL
);

CREATE TABLE logs (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER REFERENCES users(id),
    action      VARCHAR(80) NOT NULL,
    details     TEXT,
    ip_address  VARCHAR(64),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE scan_logs (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id),
    product_id  INTEGER NOT NULL REFERENCES products(id),
    action_type VARCHAR(30) NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
