import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "PulsePay Healthcare Reconciliation Engine"
    API_V1_STR: str = ""
    
    # Database URL defaults to local SQLite if POSTGRES DB is not provided
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///./pulsepay.db"
    )
    
    # Webhook signature secret for security simulation
    WEBHOOK_SECRET: str = os.getenv("WEBHOOK_SECRET", "pulsepay_secret_key_998877")
    
    # Environment (development, test, production)
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # API Authentication
    API_KEY: Optional[str] = os.getenv("API_KEY", None)

    # CORS Configuration: comma-separated list of allowed origins
    CORS_ALLOWED_ORIGINS: str = os.getenv("CORS_ALLOWED_ORIGINS", "")

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env", extra="ignore")

settings = Settings()
