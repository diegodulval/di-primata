import uuid
from datetime import date, datetime

from pydantic import BaseModel


class ClienteCreate(BaseModel):
    nome:     str
    cpf_cnpj: str | None = None
    telefone: str | None = None
    email:    str | None = None
    endereco: str | None = None


class ClienteUpdate(BaseModel):
    nome:     str | None = None
    cpf_cnpj: str | None = None
    telefone: str | None = None
    email:    str | None = None
    endereco: str | None = None


class ClienteResponse(BaseModel):
    id:        uuid.UUID
    tenant_id: uuid.UUID
    nome:      str
    cpf_cnpj:  str | None
    telefone:  str | None
    email:     str | None
    endereco:  str | None
    criado_em: datetime

    model_config = {"from_attributes": True}


class ClienteListResponse(BaseModel):
    total: int
    items: list[ClienteResponse]


class ClienteVeiculoCreate(BaseModel):
    veiculo_id: uuid.UUID


class ClienteVeiculoResponse(BaseModel):
    id:          uuid.UUID
    cliente_id:  uuid.UUID
    veiculo_id:  uuid.UUID
    data_inicio: date
    data_fim:    date | None
    ativo:       bool

    model_config = {"from_attributes": True}
