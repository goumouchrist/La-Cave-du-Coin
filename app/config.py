from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "sqlite:///./cave_du_coin.db"
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 480

    CASH_GAP_ALERT_THRESHOLD_GNF: int = 10000
    STOCK_ALERT_DEFAULT_CARTONS: int = 5
    ROUNDING_STEP_GNF: int = 50
    CANCEL_WINDOW_MINUTES: int = 5
    MIN_MARGIN_RATIO: float = 0.95
    IDENTICAL_ITEMS_CONFIRM_THRESHOLD: int = 5
    DOUBLE_SCAN_WINDOW_SECONDS: int = 2
    CREDIT_LIMIT_PER_CUSTOMER: int = 2

    STORE_NAME: str = "La Cave du Coin"
    STORE_ADDRESS: str = "Conakry, Guinée"
    STORE_NIF: str = "NIF-000000000"

    BACKUP_DIR: str = "backups"
    BACKUP_RETENTION_DAYS: int = 14
    OFFSITE_BACKUP_DIR: str = ""

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USE_TLS: bool = True
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""


settings = Settings()
