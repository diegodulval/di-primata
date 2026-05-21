from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from core.models.enums import EstadoAgente


class DirecaoMensagem(StrEnum):
    INBOUND = "INBOUND"
    OUTBOUND = "OUTBOUND"


class WhatsappSessao(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    phone: str  # E.164 sem prefixo whatsapp: ex. +5511999990000
    profile_name: str | None = None
    account_id: UUID | None = None  # resolvido via Account.whatsapp_phone
    unit_id: UUID | None = None     # talhão padrão vinculado manualmente pelo admin
    estado: EstadoAgente = EstadoAgente.OCIOSO
    contexto_json: dict[str, Any] = Field(default_factory=dict)
    criado_em: datetime = Field(default_factory=lambda: datetime.now(UTC))
    ultima_atividade_em: datetime = Field(default_factory=lambda: datetime.now(UTC))


class WhatsappSessaoUpdate(BaseModel):
    unit_id: UUID | None = None


class WhatsappMensagem(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    sessao_id: UUID
    sid: str  # Twilio MessageSid
    direcao: DirecaoMensagem
    corpo: str
    num_midia: int = 0
    midia_urls: list[str] = Field(default_factory=list)
    criado_em: datetime = Field(default_factory=lambda: datetime.now(UTC))
