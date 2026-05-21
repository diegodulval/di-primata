from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from core.models.enums import PlanoAssinatura


class Account(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    nome: str
    documento: str
    email: str
    plano: PlanoAssinatura = PlanoAssinatura.FREE
    setor_primario: str
    whatsapp_phone: str | None = None
    ativo: bool = True
    criado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    meta_json: dict[str, Any] = Field(default_factory=dict)


class AccountCreate(BaseModel):
    nome: str
    documento: str
    email: str
    plano: PlanoAssinatura = PlanoAssinatura.FREE
    setor_primario: str
    whatsapp_phone: str | None = None
    meta_json: dict[str, Any] = Field(default_factory=dict)


class AccountUpdate(BaseModel):
    nome: str | None = None
    whatsapp_phone: str | None = None
