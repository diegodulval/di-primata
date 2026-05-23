import re
import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, field_validator

# Aceita formato antigo (ABC1234) e Mercosul (ABC1D23)
_PLACA_RE = re.compile(r"^[A-Z]{3}[0-9]{4}$|^[A-Z]{3}[0-9][A-Z][0-9]{2}$")

TipoVeiculo = Literal["carro", "moto", "caminhao", "van"]


class VeiculoCreate(BaseModel):
    placa:   str
    chassi:  str | None = None
    marca:   str | None = None
    modelo:  str | None = None
    ano_fab: int | None = None
    ano_mod: int | None = None
    cor:     str | None = None
    tipo:    TipoVeiculo | None = None

    @field_validator("placa", mode="before")
    @classmethod
    def normalizar_placa(cls, v: str) -> str:
        v = v.strip().upper()
        if not _PLACA_RE.match(v):
            raise ValueError(f"Placa '{v}' inválida — use ABC1234 ou ABC1D23")
        return v


class VeiculoResponse(BaseModel):
    id:      uuid.UUID
    placa:   str
    chassi:  str | None
    marca:   str | None
    modelo:  str | None
    ano_fab: int | None
    ano_mod: int | None
    cor:     str | None
    tipo:    str | None
    criado_em: datetime

    model_config = {"from_attributes": True}


class HistoricoCreate(BaseModel):
    veiculo_id:      uuid.UUID
    tenant_id:       uuid.UUID
    os_id:           uuid.UUID | None = None
    data_servico:    date
    km_entrada:      int | None = None
    detalhe_privado: str
    resumo_publico:  str | None = None


class HistoricoPublicoResponse(BaseModel):
    id:             uuid.UUID
    data_servico:   date
    km_entrada:     int | None
    resumo_publico: str
    criado_em:      datetime

    model_config = {"from_attributes": True}


class VeiculoComHistorico(VeiculoResponse):
    historico_publico: list[HistoricoPublicoResponse] = []


class ConsultaVeiculoResponse(BaseModel):
    """
    Resposta do endpoint GET /veiculos/{placa}/consultar.
    Agrega dados da DB local (se existir) com enriquecimento do SINESP.
    """
    fonte: Literal["db", "sinesp", "nao_encontrado"]
    # Campos do veículo (preenchidos de acordo com a fonte)
    placa: str
    chassi: str | None = None
    marca: str | None = None
    modelo: str | None = None
    ano_fab: int | None = None
    ano_mod: int | None = None
    cor: str | None = None
    tipo: str | None = None
    # Campos extras apenas do SINESP (não persistidos no veículo)
    municipio: str | None = None
    uf: str | None = None
    situacao: str | None = None
    # Presente apenas quando fonte == "db"
    id: uuid.UUID | None = None
    criado_em: datetime | None = None
