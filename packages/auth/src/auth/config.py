from pydantic_settings import BaseSettings


class AuthSettings(BaseSettings):
    secret_key: str = "inseguro-trocar-em-producao"
    access_token_expire_minutes: int = 60

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = AuthSettings()
