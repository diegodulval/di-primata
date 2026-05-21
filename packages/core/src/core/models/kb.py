from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from core.models.enums import CategoriaKb


class KbItem(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    setor: str
    categoria: CategoriaKb
    termo: str
    sinonimos: list[str] = Field(default_factory=list)
    descricao: str
    parametros_json: dict[str, Any] = Field(default_factory=dict)
    confianca: float = 1.0
