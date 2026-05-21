from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    secret_key: str = "inseguro-trocar-em-producao"
    access_token_expire_minutes: int = 60

    # PostgreSQL para oficinas (pode ser diferente do producao)
    database_url: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
