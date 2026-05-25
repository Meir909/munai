import os
from pydantic import BaseModel


class Settings(BaseModel):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:////tmp/munai.db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "munai-super-secret-key-change-in-production-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080
    CORS_ORIGINS: str = "*"


settings = Settings()
