from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    secret_key: str = "inseguro-trocar-em-producao"
    access_token_expire_minutes: int = 60

    # Conta admin criada automaticamente na primeira inicialização (store em memória)
    bootstrap_admin_email: str = "admin@dimata.dev"
    bootstrap_admin_senha: str = "dev1234"
    bootstrap_admin_nome: str = "Admin Di Mata"

    # Twilio / WhatsApp
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_from: str = ""  # número Twilio sem prefixo, ex: +14155238886
    # Em produção deve ser True; False permite testar sem enviar credenciais reais
    twilio_validate_signature: bool = False

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
