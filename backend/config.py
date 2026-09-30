import os
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
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env", extra="ignore")

settings = Settings()
