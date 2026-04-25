# app/config.py
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    APP_NAME: str = "Godfident"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    DATABASE_URL: str = "sqlite+aiosqlite:///./godfident.db"

    SECRET_KEY: str = "change-this-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days

    ANTHROPIC_API_KEY: str = ""

    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173,https://godfident-frontend.onrender.com"

    FIREBASE_SERVER_KEY: str = ""
    
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "change-me-now"
    SESSION_SECRET_KEY: str = "godfident-session-key"

    @property
    def origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

 