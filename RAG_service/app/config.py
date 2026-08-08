from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    GOOGLE_API_KEY: str
    WEATHER_API_KEY: str 
    TAVILY_API_KEY: str 
    POSTGRES_USER: str 
    POSTGRES_DB: str 
    POSTGRES_PASSWORD: str 
    POSTGRES_SERVER: str 
    POSTGRES_PORT: int 
    APP_NAME: str 
    APP_HOST: str 
    APP_PORT: int
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    model_config = SettingsConfigDict(
        env_file="./.env", 
        env_file_encoding="utf-8",
        case_sensitive=True,
        env_ignore_case=True,
        env_ignore_empty=True,
        extra="ignore",
    )
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

settings = Settings()