from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "JobShield - Job & Company Verification Platform"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # MySQL connection
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_DATABASE: str = "jobshield"
    MYSQL_USER: str = "jobshield_user"
    MYSQL_PASSWORD: str = "jobshield_pass"

    # JWT
    JWT_SECRET_KEY: str = "dev_secret_key_change_in_production_1234567890"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
