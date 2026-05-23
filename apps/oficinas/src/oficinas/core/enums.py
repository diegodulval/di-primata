from enum import StrEnum


class Perfil(StrEnum):
    ADMIN     = "ADMIN"
    ATENDENTE = "ATENDENTE"
    MECANICO  = "MECANICO"


class StatusOS(StrEnum):
    ABERTA          = "ABERTA"
    EM_EXECUCAO     = "EM_EXECUCAO"
    AGUARDANDO_PECA = "AGUARDANDO_PECA"
    FECHADA         = "FECHADA"
    CANCELADA       = "CANCELADA"


class TipoMovimentacao(StrEnum):
    ENTRADA   = "ENTRADA"
    SAIDA     = "SAIDA"
    RESERVA   = "RESERVA"
    LIBERACAO = "LIBERACAO"


class TipoItem(StrEnum):
    PECA    = "PECA"
    SERVICO = "SERVICO"


class OrigemVenda(StrEnum):
    BALCAO = "BALCAO"
    OS     = "OS"


class RegimeTributario(StrEnum):
    SIMPLES         = "simples"
    LUCRO_PRESUMIDO = "lucro_presumido"
    LUCRO_REAL      = "lucro_real"


class TipoVeiculo(StrEnum):
    CARRO    = "carro"
    MOTO     = "moto"
    CAMINHAO = "caminhao"
    VAN      = "van"


class StatusRascunho(StrEnum):
    PENDENTE   = "PENDENTE"
    CONFIRMADA = "CONFIRMADA"
    CANCELADA  = "CANCELADA"


class StatusItem(StrEnum):
    AUTO_VINCULADO = "AUTO_VINCULADO"
    VINCULADO      = "VINCULADO"
    NOVO           = "NOVO"
    PENDENTE       = "PENDENTE"

class StatusEntradaNfe(StrEnum):
    ABERTA     = "ABERTA"
    PROCESSADA = "PROCESSADA"
