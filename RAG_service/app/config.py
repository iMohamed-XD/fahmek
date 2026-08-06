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
    model_config = SettingsConfigDict(
        env_file="./.env", 
        env_file_encoding="utf-8",
        encase_sensitive=True,
        env_ignore_case=True,
        env_ignore_empty=True,
        extra="ignore",
    )

settings = Settings()