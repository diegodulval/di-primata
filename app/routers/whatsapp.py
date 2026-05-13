import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import PlainTextResponse

from app.core.config import Settings
from app.core.config import settings as _default_settings
from app.core.deps import get_debounce_buffer, get_rate_limiter, get_twilio_client
from app.ingestion.normalizer import normalize
from app.models.whatsapp import WhatsappSessaoUpdate
from app.repositories.store import Store, get_store

logger = logging.getLogger(__name__)
router = APIRouter()


def get_settings() -> Settings:
    return _default_settings


async def _validate_twilio_signature(request: Request, cfg: Settings) -> None:
    """Lança 403 se a assinatura Twilio for inválida (quando validação ativada)."""
    if not cfg.twilio_validate_signature:
        return

    from twilio.request_validator import RequestValidator

    signature = request.headers.get("X-Twilio-Signature", "")
    form = await request.form()
    payload = dict(form)

    if not RequestValidator(cfg.twilio_auth_token).validate(str(request.url), payload, signature):
        logger.warning("Assinatura Twilio inválida | url=%s", request.url)
        raise HTTPException(status_code=403, detail="Assinatura Twilio inválida")


# ── Webhook: mensagens inbound ─────────────────────────────────────────────────

@router.post("/webhook", response_class=PlainTextResponse)
async def webhook(
    request: Request,
    cfg: Settings = Depends(get_settings),
    debounce=Depends(get_debounce_buffer),
    rate_limiter=Depends(get_rate_limiter),
):
    """
    Configurar em: Sandbox Settings → "When a message comes in"
    URL: POST /whatsapp/webhook

    Camada 1 — Entrada/Recebimento:
    valida → normaliza → rate limit → debounce buffer → fila PostgreSQL
    """
    await _validate_twilio_signature(request, cfg)

    form = await request.form()
    msg = normalize(dict(form))

    logger.info("Mensagem inbound | from=%s sid=%s body=%r", msg.phone, msg.message_sid, msg.body)

    if msg.num_media > 0:
        logger.debug("Mídia ignorada (Camada 1) | phone=%s num_media=%d", msg.phone, msg.num_media)
        return PlainTextResponse("", status_code=200)

    if rate_limiter and not rate_limiter.is_allowed(msg.phone):
        logger.warning("Rate limit excedido | phone=%s", msg.phone)
        return PlainTextResponse("", status_code=200)

    if debounce:
        await debounce.push(msg)
    else:
        logger.warning("debounce_buffer indisponível, mensagem descartada | phone=%s sid=%s", msg.phone, msg.message_sid)

    return PlainTextResponse("", status_code=200)


# ── Webhook: status de entrega ─────────────────────────────────────────────────

@router.post("/status", response_class=PlainTextResponse)
async def status_callback(request: Request):
    """
    Configurar em: Sandbox Settings → "Status callback URL"
    URL: POST /whatsapp/status
    Recebe atualizações de entrega: queued → sent → delivered → read
    """
    form = await request.form()
    payload = dict(form)
    logger.debug(
        "Status callback | sid=%s to=%s status=%s",
        payload.get("MessageSid"),
        payload.get("To"),
        payload.get("MessageStatus"),
    )
    return PlainTextResponse("", status_code=200)


# ── Diagnóstico (apenas em desenvolvimento) ───────────────────────────────────

@router.get("/debug")
def debug(store: Store = Depends(get_store), cfg: Settings = Depends(get_settings)):
    """Mostra o estado do store para diagnosticar vínculos phone → account."""
    accounts = [
        {"id": str(a.id), "nome": a.nome, "whatsapp_phone": a.whatsapp_phone}
        for a in store.accounts.list_all()
    ]
    sessions = [
        {
            "id": str(s.id),
            "phone": s.phone,
            "account_id": str(s.account_id) if s.account_id else None,
            "unit_id": str(s.unit_id) if s.unit_id else None,
            "estado": s.estado,
        }
        for s in store.whatsapp_sessoes.list_all()
    ]
    return {"accounts": accounts, "sessions": sessions}


# ── Consulta de sessões e mensagens ───────────────────────────────────────────

@router.get("/sessions")
def list_sessions(store: Store = Depends(get_store)):
    """Lista todas as sessões WhatsApp com contagem de mensagens."""
    sessoes = store.whatsapp_sessoes.list_all()
    result = []
    for s in sessoes:
        msgs = store.whatsapp_mensagens.list_by(sessao_id=s.id)
        result.append({
            **s.model_dump(),
            "total_mensagens": len(msgs),
        })
    return result


@router.get("/sessions/{session_id}")
def get_session(session_id: UUID, store: Store = Depends(get_store)):
    """Retorna uma sessão pelo ID."""
    sessao = store.whatsapp_sessoes.get(session_id)
    if not sessao:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    return sessao


@router.patch("/sessions/{session_id}")
def update_session(
    session_id: UUID,
    body: WhatsappSessaoUpdate,
    store: Store = Depends(get_store),
):
    """Atualiza campos editáveis da sessão (ex: vincular talhão)."""
    sessao = store.whatsapp_sessoes.get(session_id)
    if not sessao:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(sessao, field, value)
    store.whatsapp_sessoes.save(sessao)
    return sessao


@router.get("/registros")
def list_registros(store: Store = Depends(get_store)):
    """Lista atividades registradas via WhatsApp, com contexto de quem criou, talhão e propriedade."""
    from app.models.enums import OrigemCaptura
    result = []
    for event in store.events.list_all():
        if event.origem != OrigemCaptura.VOZ:
            continue
        ciclo = store.cycles.get(event.ciclo_id)
        if not ciclo:
            continue
        account = store.accounts.get(ciclo.account_id) if ciclo.account_id else None
        unit = store.units.get(ciclo.unit_id) if ciclo.unit_id else None
        sessoes = store.whatsapp_sessoes.list_by(account_id=ciclo.account_id) if ciclo.account_id else []
        sessao = sessoes[0] if sessoes else None
        result.append({
            "id": str(event.id),
            "phone": sessao.phone if sessao else None,
            "profile_name": sessao.profile_name if sessao else None,
            "propriedade": account.nome if account else None,
            "talhao": unit.nome if unit else None,
            "atividade": event.payload_json.get("tipo_atividade") or event.descricao,
            "valor_gasto": event.payload_json.get("valor_gasto"),
            "capturado_em": event.capturado_em.isoformat(),
            "ciclo_id": str(event.ciclo_id),
        })
    return sorted(result, key=lambda r: r["capturado_em"], reverse=True)


@router.get("/sessions/{session_id}/messages")
def list_session_messages(session_id: UUID, store: Store = Depends(get_store)):
    """Lista todas as mensagens de uma sessão em ordem cronológica."""
    sessao = store.whatsapp_sessoes.get(session_id)
    if not sessao:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    msgs = store.whatsapp_mensagens.list_by(sessao_id=session_id)
    return sorted(msgs, key=lambda m: m.criado_em)
