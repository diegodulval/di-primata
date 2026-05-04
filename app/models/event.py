from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.models.enums import OrigemCaptura, StatusValidacao, TipoEvento


class EventLocation(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    event_id: UUID
    lat: float
    lng: float
    accuracy: float | None = None
    capturado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EventAttachment(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    event_id: UUID
    tipo: str
    url: str
    filename: str | None = None
    criado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Event(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    ciclo_id: UUID
    etapa_protocolo_id: UUID
    autor_user_id: UUID
    tipo_evento: TipoEvento
    descricao: str
    payload_json: dict[str, Any] = Field(default_factory=dict)
    status_validacao: StatusValidacao = StatusValidacao.PENDENTE
    origem: OrigemCaptura
    capturado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sincronizado_em: datetime | None = None
    aditamento_de_id: UUID | None = None
    visivel_publico: bool = True
    attachments: list[EventAttachment] = Field(default_factory=list)
    location: EventLocation | None = None


class EventCreate(BaseModel):
    etapa_protocolo_id: UUID
    tipo_evento: TipoEvento
    descricao: str
    payload_json: dict[str, Any] = Field(default_factory=dict)
    origem: OrigemCaptura = OrigemCaptura.MANUAL
    capturado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    aditamento_de_id: UUID | None = None
    visivel_publico: bool = True
