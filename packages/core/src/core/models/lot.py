from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from core.models.enums import StatusLote, TipoAsset


class LotAsset(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    lot_id: UUID
    tipo: TipoAsset
    url: str
    gerado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Certification(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    lot_id: UUID
    cert_user_id: UUID
    notas: str | None = None
    assinado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    assinatura_digital: str | None = None


class Lot(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    ciclo_id: UUID
    codigo_lote: str
    qr_hash: str
    status: StatusLote = StatusLote.GERADO
    gerado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    snapshot_json: dict[str, Any] = Field(default_factory=dict)
    publico: bool = False
    cert_user_id: UUID | None = None
    assets: list[LotAsset] = Field(default_factory=list)
    certifications: list[Certification] = Field(default_factory=list)


class QrAccess(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    lot_id: UUID
    ip_origem: str | None = None
    user_agent: str | None = None
    geo_json: dict[str, Any] | None = None
    acessado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    patrocinador_id: UUID | None = None
