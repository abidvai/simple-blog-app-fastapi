from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Blog API"
    DEBUG: bool = False

    DATABASE_URL: str

    REDIS_URL: str = "redis://localhost:6379"

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

