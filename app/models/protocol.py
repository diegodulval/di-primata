from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ProtocolStep(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    nome: str
    tipo: str
    obrigatorio: bool = True
    criterios: dict[str, Any] = Field(default_factory=dict)


class Protocol(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    setor_template: str
    nome: str
    versao: str
    etapas: list[ProtocolStep] = Field(default_factory=list)
    etapas_obrig_ids: list[UUID] = Field(default_factory=list)
    ref_normativa: str | None = None
    ativo: bool = True


class ProtocolCreate(BaseModel):
    setor_template: str
    nome: str
    versao: str
    etapas: list[ProtocolStep] = Field(default_factory=list)
    etapas_obrig_ids: list[UUID] = Field(default_factory=list)
    ref_normativa: str | None = None
