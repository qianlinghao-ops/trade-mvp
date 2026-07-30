from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    APP_NAME: str = "貿易業務自動化システム"
    VERSION: str = "1.0.0"
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/trade.db"
    SECRET_KEY: str = "trade-mvp-secret-key-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    GENERATED_DIR: Path = BASE_DIR / "generated"
    MAX_FILE_SIZE: int = 20 * 1024 * 1024

    class Config:
        env_file = ".env"

settings = Settings()
settings.UPLOAD_DIR.mkdir(exist_ok=True)
settings.GENERATED_DIR.mkdir(exist_ok=True)
