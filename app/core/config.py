from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    secret_key: str = "inseguro-trocar-em-producao"
    access_token_expire_minutes: int = 60

    # Conta admin criada automaticamente na primeira inicialização (store em memória)
    bootstrap_admin_email: str = "admin@dimata.dev"
    bootstrap_admin_senha: str = "dev1234"
    bootstrap_admin_nome: str = "Admin Di Mata"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
