from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Insumo(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    fornecedor_id: UUID | None = None
    codigo_lote_forn: str | None = None
    nome: str
    tipo_insumo: str
    quantidade: float
    unidade: str
    certificado_url: str | None = None


class CicloInsumo(BaseModel):
    ciclo_id: UUID
    insumo_id: UUID
    quantidade_usada: float
    registrado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    rastreado: bool = False


class InsumoCreate(BaseModel):
    fornecedor_id: UUID | None = None
    codigo_lote_forn: str | None = None
    nome: str
    tipo_insumo: str
    quantidade: float
    unidade: str
    certificado_url: str | None = None
