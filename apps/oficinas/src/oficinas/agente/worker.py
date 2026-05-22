"""
Orquestrador do agente Claude.

Fluxo por mensagem recebida:
  1. Identifica usuario pelo numero_whatsapp (sem RLS)
  2. Seta app.current_tenant na sessão → ativa RLS
  3. Carrega histórico da sessão
  4. Loop Claude API + tool execution até stop_reason == "end_turn"
  5. Salva histórico atualizado
  6. Retorna texto da resposta final
"""

import structlog
from anthropic import AsyncAnthropic
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from oficinas.core.config import settings
from oficinas.agente import sessao as sessao_mod
from oficinas.agente.prompts import build_system_prompt
from oficinas.agente.tools import TOOLS, executar_tool

log = structlog.get_logger()

_MODEL = "claude-sonnet-4-6"
_MAX_TOKENS = 2048
_MAX_TURNS = 10  # proteção contra loop infinito


def _content_para_json(content) -> list[dict] | str:
    """Converte content blocks do SDK para dicts serializáveis."""
    if isinstance(content, str):
        return content
    result = []
    for blk in content:
        if hasattr(blk, "model_dump"):
            result.append(blk.model_dump())
        else:
            result.append(blk)  # type: ignore[arg-type]
    return result


async def processar(db: AsyncSession, numero: str, texto: str) -> str | None:
    """
    Processa uma mensagem recebida do WhatsApp.
    Retorna o texto da resposta do agente, ou None se o usuário não for encontrado.
    """
    from oficinas.modules.iam.models import Tenant, Usuario

    # 1. Localizar usuário pelo número (usuario não tem RLS)
    stmt = select(Usuario).where(
        Usuario.numero_whatsapp == numero,
        Usuario.ativo.is_(True),
    )
    usuario = (await db.execute(stmt)).scalar_one_or_none()
    if not usuario:
        log.warning("agente_usuario_nao_encontrado", numero=numero)
        return None

    # 2. Ativar RLS para o tenant
    await db.execute(
        text(f"SET LOCAL app.current_tenant = '{usuario.tenant_id}'")
    )

    # 3. Carregar nome do tenant para o system prompt
    tenant = await db.get(Tenant, usuario.tenant_id)
    nome_tenant = tenant.razao_social if tenant else "a oficina"

    # 4. Carregar histórico da sessão
    historico = await sessao_mod.carregar(db, numero)

    # 5. Adicionar mensagem do usuário
    mensagens: list[dict] = list(historico)
    mensagens.append({"role": "user", "content": texto})

    # 6. Loop Claude + tools
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    system_prompt = build_system_prompt(nome_tenant, usuario.nome)
    resposta_final: str = ""

    for _ in range(_MAX_TURNS):
        response = await client.messages.create(
            model=_MODEL,
            max_tokens=_MAX_TOKENS,
            system=system_prompt,
            tools=TOOLS,  # type: ignore[arg-type]
            messages=mensagens,  # type: ignore[arg-type]
        )

        # Registrar resposta do assistente no histórico
        mensagens.append({
            "role": "assistant",
            "content": _content_para_json(response.content),
        })

        if response.stop_reason == "end_turn":
            for blk in response.content:
                if hasattr(blk, "text"):
                    resposta_final = blk.text
                    break
            break

        if response.stop_reason == "tool_use":
            tool_results = []
            for blk in response.content:
                if blk.type == "tool_use":
                    log.info("agente_tool_call", tool=blk.name, input=blk.input)
                    resultado = await executar_tool(
                        blk.name, blk.input, db, usuario
                    )
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": blk.id,
                        "content": resultado,
                    })
            mensagens.append({"role": "user", "content": tool_results})
        else:
            # max_tokens ou outro stop_reason inesperado
            break

    # 7. Salvar sessão com histórico atualizado
    await sessao_mod.salvar(
        db,
        numero=numero,
        tenant_id=str(usuario.tenant_id),
        usuario_id=str(usuario.id),
        msgs=mensagens,
    )

    log.info("agente_resposta", numero=numero, chars=len(resposta_final))
    return resposta_final or "Desculpe, não consegui processar sua mensagem."
