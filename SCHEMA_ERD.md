# Diagramme de données — La Cave du Coin

Généré à partir de [`app/models.py`](app/models.py). Le schéma réel de la base
est géré par Alembic (`migrations/`) — ce fichier est purement documentaire.

**Comment le voir en diagramme** :
- **GitHub** : ce bloc Mermaid se rend automatiquement en diagramme quand tu
  ouvres ce fichier sur github.com (aucune action nécessaire).
- **VS Code** : installer l'extension "Markdown Preview Mermaid Support",
  puis ouvrir l'aperçu Markdown (`Ctrl+Shift+V`).
- **N'importe où** : coller le contenu du bloc ci-dessous sur
  [mermaid.live](https://mermaid.live).

```mermaid
erDiagram
    USERS {
        int id PK
        string username UK
        string password_hash
        string full_name
        enum role
        bool is_active
        datetime created_at
    }

    SUPPLIERS {
        int id PK
        string name
        string phone
        string address
        bool is_active
        datetime created_at
    }

    PRODUCTS {
        int id PK
        string barcode UK
        string name
        string category
        int supplier_id FK
        int unit_carton_qty
        int unit_pack_qty
        int prix_achat
        int prix_vente
        float tva_rate
        int stock_min_cartons
        bool is_active
        datetime created_at
    }

    STOCK_MOVEMENTS {
        int id PK
        int product_id FK
        int supplier_id FK
        enum type
        int qty_units
        string invoice_number
        text reason
        enum status
        int created_by FK
        int validated_by FK
        datetime created_at
        datetime validated_at
    }

    CASH_SESSIONS {
        int id PK
        int opened_by FK
        int closed_by FK
        int opening_amount
        int closing_theoretical
        int closing_physical
        int gap_amount
        enum status
        datetime opened_at
        datetime closed_at
        int resolved_by FK
        datetime resolved_at
        text resolution_comment
    }

    CUSTOMERS {
        int id PK
        string name
        string phone UK
        string address
        int credit_balance_gnf
        datetime created_at
    }

    SALES {
        int id PK
        string transaction_number UK
        int cash_session_id FK
        int cashier_id FK
        enum payment_mode
        int customer_id FK
        int total_amount
        int amount_given
        int change_amount
        int remaining_due_gnf
        date due_date
        enum status
        int cancelled_by FK
        text cancel_reason
        datetime cancelled_at
        int print_count
        string customer_email
        datetime receipt_email_sent_at
        datetime created_at
    }

    SALE_ITEMS {
        int id PK
        int sale_id FK
        int product_id FK
        int qty_units
        int unit_price
        bool quantity_confirmed
    }

    QUOTES {
        int id PK
        string quote_number UK
        int created_by FK
        int customer_id FK
        string customer_name
        string customer_phone
        int total_amount
        enum status
        date expires_at
        int converted_sale_id FK
        datetime converted_at
        datetime cancelled_at
        int print_count
        datetime created_at
    }

    QUOTE_ITEMS {
        int id PK
        int quote_id FK
        int product_id FK
        int qty_units
        int unit_price
    }

    CUSTOMER_REPAYMENTS {
        int id PK
        int customer_id FK
        int amount_gnf
        enum payment_mode
        int processed_by FK
        datetime created_at
    }

    RETURNS {
        int id PK
        int sale_id FK
        int customer_id FK
        int processed_by FK
        text reason
        int total_refund_gnf
        datetime created_at
    }

    RETURN_ITEMS {
        int id PK
        int return_id FK
        int sale_item_id FK
        int product_id FK
        int qty_units
        int unit_price
    }

    LOGS {
        int id PK
        int user_id FK
        string action
        text details
        string ip_address
        datetime created_at
    }

    SCAN_LOGS {
        int id PK
        int user_id FK
        int product_id FK
        string action_type
        datetime created_at
    }

    SUPPLIERS ||--o{ PRODUCTS : "supplier_id"
    SUPPLIERS ||--o{ STOCK_MOVEMENTS : "supplier_id"
    PRODUCTS ||--o{ STOCK_MOVEMENTS : "product_id"
    PRODUCTS ||--o{ SALE_ITEMS : "product_id"
    PRODUCTS ||--o{ QUOTE_ITEMS : "product_id"
    PRODUCTS ||--o{ RETURN_ITEMS : "product_id"
    PRODUCTS ||--o{ SCAN_LOGS : "product_id"

    USERS ||--o{ STOCK_MOVEMENTS : "created_by / validated_by"
    USERS ||--o{ CASH_SESSIONS : "opened_by / closed_by / resolved_by"
    USERS ||--o{ SALES : "cashier_id / cancelled_by"
    USERS ||--o{ QUOTES : "created_by"
    USERS ||--o{ CUSTOMER_REPAYMENTS : "processed_by"
    USERS ||--o{ RETURNS : "processed_by"
    USERS ||--o{ LOGS : "user_id"
    USERS ||--o{ SCAN_LOGS : "user_id"

    CASH_SESSIONS ||--o{ SALES : "cash_session_id"
    SALES ||--o{ SALE_ITEMS : "sale_id"
    SALES ||--o{ RETURNS : "sale_id"
    QUOTES ||--o{ QUOTE_ITEMS : "quote_id"
    QUOTES }o--o| SALES : "converted_sale_id"

    CUSTOMERS ||--o{ SALES : "customer_id"
    CUSTOMERS ||--o{ QUOTES : "customer_id"
    CUSTOMERS ||--o{ CUSTOMER_REPAYMENTS : "customer_id"
    CUSTOMERS ||--o{ RETURNS : "customer_id"

    RETURNS ||--o{ RETURN_ITEMS : "return_id"
    SALE_ITEMS ||--o{ RETURN_ITEMS : "sale_item_id"
```

## Notes de lecture

- **Champs `enum`** : `role` (users), `payment_mode` (sales, customer_repayments),
  `type`/`status` (stock_movements), `status` (cash_sessions, sales, quotes) —
  voir les classes `enum.Enum` correspondantes dans `app/models.py` pour les
  valeurs possibles.
- **Stock courant d'un produit** : non stocké directement, **dérivé** des
  `stock_movements` validés (`app/services/products.py::get_current_stock_units`).
- **`quotes.converted_sale_id`** : lien optionnel devis → vente. C'est
  volontairement le devis qui référence la vente (et non l'inverse), pour que
  `sales`/`sale_items` restent inchangés par la fonctionnalité devis.
- Plusieurs tables ont **plusieurs clés étrangères vers `users`** avec des
  rôles différents (ex: `stock_movements.created_by` vs `validated_by`,
  `sales.cashier_id` vs `cancelled_by`) — représentées ici par une seule
  flèche groupée par lisibilité, mais ce sont bien des colonnes distinctes.
