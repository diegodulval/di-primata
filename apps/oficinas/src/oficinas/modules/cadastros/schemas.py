import uuid
from datetime import date, datetime

from pydantic import BaseModel


class ClienteCreate(BaseModel):
    nome:               str
    tipo_pessoa:        str | None = "Fisica"
    cpf_cnpj:           str | None = None
    rg:                 str | None = None
    apelido:            str | None = None
    data_nascimento:    date | None = None
    sexo:               str | None = None
    telefone:           str | None = None
    celular:            str | None = None
    email:              str | None = None
    cep:                str | None = None
    endereco:           str | None = None
    cidade:             str | None = None
    uf:                 str | None = None
    inscricao_estadual: str | None = None
    consumidor_final:   bool = True
    indicador_ie:       str = "9"
    observacoes:        str | None = None


class ClienteUpdate(BaseModel):
    nome:               str | None = None
    tipo_pessoa:        str | None = None
    cpf_cnpj:           str | None = None
    rg:                 str | None = None
    apelido:            str | None = None
    data_nascimento:    date | None = None
    sexo:               str | None = None
    telefone:           str | None = None
    celular:            str | None = None
    email:              str | None = None
    cep:                str | None = None
    endereco:           str | None = None
    cidade:             str | None = None
    uf:                 str | None = None
    inscricao_estadual: str | None = None
    consumidor_final:   bool | None = None
    indicador_ie:       str | None = None
    observacoes:        str | None = None
    ativo:              bool | None = None


class ClienteResponse(BaseModel):
    id:                 uuid.UUID
    tenant_id:          uuid.UUID
    nome:               str
    tipo_pessoa:        str | None
    cpf_cnpj:           str | None
    rg:                 str | None
    apelido:            str | None
    data_nascimento:    date | None
    sexo:               str | None
    telefone:           str | None
    celular:            str | None
    email:              str | None
    cep:                str | None
    endereco:           str | None
    cidade:             str | None
    uf:                 str | None
    inscricao_estadual: str | None
    consumidor_final:   bool
    indicador_ie:       str
    observacoes:        str | None
    ativo:              bool
    criado_em:          datetime

    model_config = {"from_attributes": True}


class ClientesPaginados(BaseModel):
    items:     list[ClienteResponse]
    total:     int
    page:      int
    page_size: int
    pages:     int


class ImportacaoClienteResponse(BaseModel):
    criados:     int
    atualizados: int
    ignorados:   int
    erros:       list[str]


class ImportacaoVeiculosResponse(BaseModel):
    match_cpf:                int
    match_telefone:           int
    match_nome:               int
    clientes_nao_encontrados: int
    clientes_enriquecidos:    int
    veiculos_upserted:        int
    vinculos_criados:         int
    placas_ignoradas:         int
    erros:                    list[str]


class ClienteVeiculoCreate(BaseModel):
    veiculo_id: uuid.UUID


class VeiculoResumo(BaseModel):
    placa:   str
    marca:   str | None
    modelo:  str | None
    ano_fab: int | None
    ano_mod: int | None
    cor:     str | None
    tipo:    str | None

    model_config = {"from_attributes": True}


class ClienteVeiculoResponse(BaseModel):
    id:          uuid.UUID
    cliente_id:  uuid.UUID
    veiculo_id:  uuid.UUID
    data_inicio: date
    data_fim:    date | None
    ativo:       bool
    veiculo:     VeiculoResumo | None = None

    model_config = {"from_attributes": True}
