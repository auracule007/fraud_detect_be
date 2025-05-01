from pydantic import PostgresDsn
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: PostgresDsn
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    
    API_PREFIX: str = "/api"
    PROJECT_NAME: str = "Fraud Detection System"
    VERSION: str = "1.0.0"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()