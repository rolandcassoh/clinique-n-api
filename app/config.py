from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "Gestion Clinique API"
    app_env: str = "development"
    app_secret_key: str = "dev-secret-key-change-in-production"

    database_url: str = "mysql+asyncmy://root:root@localhost:3306/clinique_dev"
    database_pool_size: int = 20
    database_max_overflow: int = 10

    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"

    jwt_secret_key: str = "dev-jwt-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 30

    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:4200"]

    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_from_email: str = "noreply@clinique.app"
    smtp_user: str = ""
    smtp_password: str = ""

    encryption_key: str = "dev-encryption-key-32-bytes-long!"

    # Stripe
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""

    # Razorpay
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""

    # PayPal
    paypal_client_id: str = ""
    paypal_client_secret: str = ""

    # Paystack
    paystack_secret_key: str = ""
    paystack_webhook_secret: str = ""

    # Flutterwave
    flutterwave_secret_key: str = ""

    # Google OAuth / Calendar
    google_client_id: str = ""
    google_client_secret: str = ""

    # Firebase
    firebase_credentials_path: str = ""

    # OneSignal
    onesignal_app_id: str = ""
    onesignal_rest_api_key: str = ""

    # Meilisearch
    meilisearch_url: str = "http://localhost:7700"
    meilisearch_master_key: str = ""


settings = Settings()
