import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # On Vercel, /tmp is the only writable dir; locally use ./munai.db
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:////tmp/munai.db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "munai-super-secret-key-change-in-production-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080
    CORS_ORIGINS: str = "*"

    @property
    def cors_origins_list(self) -> list[str]:
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"


settings = Settings()
