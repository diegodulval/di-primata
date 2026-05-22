import json
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy.ext.asyncio import AsyncSession

from oficinas.modules.cadastros.service import CadastroService
from oficinas.modules.ordens_servico.schemas import OSCreate
from oficinas.modules.ordens_servico.service import OrdensServicoService
from oficinas.shared.veiculo_global.schemas import VeiculoCreate
from oficinas.shared.veiculo_global.service import VeiculoService

if TYPE_CHECKING:
    from oficinas.modules.iam.models import Usuario


# ─── Definições das tools para a API do Claude ────────────────────────────────

TOOLS: list[dict] = [
    {
        "name": "buscar_veiculo",
        "description": "Busca veículo pela placa. Retorna dados e histórico público.",
        "input_schema": {
            "type": "object",
            "properties": {
                "placa": {"type": "string", "description": "Formato: ABC1234 ou ABC1D23"},
            },
            "required": ["placa"],
        },
    },
    {
        "name": "criar_veiculo",
        "description": "Cadastra veículo novo. Usar só se buscar_veiculo retornar não encontrado.",
        "input_schema": {
            "type": "object",
            "properties": {
                "placa":  {"type": "string"},
                "marca":  {"type": "string"},
                "modelo": {"type": "string"},
                "cor":    {"type": "string"},
                "tipo":   {"type": "string", "enum": ["carro", "moto", "caminhao", "van"]},
            },
            "required": ["placa"],
        },
    },
    {
        "name": "buscar_cliente",
        "description": "Busca cliente no tenant por nome parcial, CPF ou telefone.",
        "input_schema": {
            "type": "object",
            "properties": {"q": {"type": "string"}},
            "required": ["q"],
        },
    },
    {
        "name": "abrir_os",
        "description": (
            "Abre Ordem de Serviço. "
            "Confirme cliente e veículo com o mecânico antes de chamar."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "cliente_id":             {"type": "string", "description": "UUID do cliente"},
                "veiculo_id":             {"type": "string", "description": "UUID do veículo"},
                "km_entrada":             {"type": "integer"},
                "descricao_problema":     {"type": "string"},
                "compartilhar_historico": {"type": "boolean", "default": False},
            },
            "required": ["cliente_id", "veiculo_id", "descricao_problema"],
        },
    },
    {
        "name": "minhas_os",
        "description": "Lista OSs abertas/em execução do mecânico autenticado.",
        "input_schema": {"type": "object", "properties": {}},
    },
]


# ─── Serializador ─────────────────────────────────────────────────────────────

def _serial(obj: Any) -> Any:
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(type(obj))


def _dump(obj: Any) -> str:
    return json.dumps(obj, default=_serial)


# ─── Executor ─────────────────────────────────────────────────────────────────

async def executar_tool(
    nome: str,
    entrada: dict,
    db: AsyncSession,
    usuario: "Usuario",
) -> str:
    """Executa a tool pelo nome e retorna o resultado como string JSON."""
    tenant_id = uuid.UUID(str(usuario.tenant_id))

    if nome == "buscar_veiculo":
        placa = entrada["placa"]
        try:
            v = await VeiculoService(db).buscar_por_placa(placa)
            return _dump({"id": v.id, "placa": v.placa, "marca": v.marca,
                          "modelo": v.modelo, "cor": v.cor, "tipo": v.tipo,
                          "ano_fab": v.ano_fab, "ano_mod": v.ano_mod})
        except Exception as exc:
            return _dump({"erro": str(exc)})

    if nome == "criar_veiculo":
        payload = VeiculoCreate(
            placa=entrada["placa"],
            marca=entrada.get("marca"),
            modelo=entrada.get("modelo"),
            cor=entrada.get("cor"),
            tipo=entrada.get("tipo"),
        )
        try:
            v = await VeiculoService(db).upsert(payload)
            return _dump({"id": v.id, "placa": v.placa, "marca": v.marca,
                          "modelo": v.modelo, "cor": v.cor, "tipo": v.tipo})
        except Exception as exc:
            return _dump({"erro": str(exc)})

    if nome == "buscar_cliente":
        q = entrada["q"]
        clientes = await CadastroService(db).buscar_por_q(q, tenant_id)
        return _dump([
            {"id": c.id, "nome": c.nome, "telefone": c.telefone, "cpf_cnpj": c.cpf_cnpj}
            for c in clientes
        ])

    if nome == "abrir_os":
        payload = OSCreate(
            cliente_id=uuid.UUID(entrada["cliente_id"]),
            veiculo_id=uuid.UUID(entrada["veiculo_id"]),
            km_entrada=entrada.get("km_entrada"),
            descricao_problema=entrada["descricao_problema"],
        )
        try:
            os = await OrdensServicoService(db).abrir(
                tenant_id=tenant_id,
                mecanico_id=uuid.UUID(str(usuario.id)),
                payload=payload,
            )
            return _dump({"id": os.id, "numero_os": os.numero_os,
                          "status": os.status, "aberta_em": os.aberta_em})
        except Exception as exc:
            return _dump({"erro": str(exc)})

    if nome == "minhas_os":
        lista = await OrdensServicoService(db).listar(
            tenant_id=tenant_id,
            mecanico_id=uuid.UUID(str(usuario.id)),
        )
        return _dump([
            {"id": o.id, "numero_os": o.numero_os, "status": o.status,
             "descricao_problema": o.descricao_problema, "aberta_em": o.aberta_em}
            for o in lista
        ])

    return _dump({"erro": f"tool desconhecida: {nome}"})
