from pydantic import PostgresDsn, computed_field
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "FastAPI Google Auth App"
    PROJECT_VERSION: str = "0.1.0"
    
    API_BASE_URL: str

    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str

    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    
    @computed_field
    @property
    def DATABASE_URL(self) -> PostgresDsn:
        """
        Membangun URL database secara dinamis dari komponen di atas.
        """
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    JWT_SECRET_KEY: str
    JWT_REFRESH_SECRET_KEY: str
    JWT_EVENT_SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    MODEL_NAME: str = "Dlib"
    DEEPFACE_VECTOR_DIMENSION: int = 128
    
    SELFIE_STORAGE_PATH: str
    EVENT_STORAGE_PATH: str
    
    TF_ENABLE_ONEDNN_OPTS: int = 0

    # Opsional: Client ID Google untuk Android/iOS jika perlu validasi audience token Google
    # GOOGLE_ANDROID_CLIENT_ID: Optional[str] = None
    # GOOGLE_IOS_CLIENT_ID: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()