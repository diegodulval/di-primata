from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"

    # Banco — obrigatório em produção
    database_url: str = ""

    # JWT
    secret_key: str = "inseguro-trocar-em-producao"
    access_token_expire_minutes: int = 60

    # WhatsApp (Meta Business API)
    whatsapp_token: str = ""
    whatsapp_verify_token: str = ""
    whatsapp_phone_id: str = ""
    # App Secret para validação HMAC-SHA256 do webhook (opcional em dev)
    whatsapp_app_secret: str = ""

    # Claude AI (agente)
    anthropic_api_key: str = ""

    # Fiscal
    cert_a1_path: str = "/secrets/cert.pfx"
    cert_a1_password: str = ""
    ambiente_sefaz: str = "homologacao"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
