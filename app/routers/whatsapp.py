import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import PlainTextResponse

from app.core.config import Settings
from app.core.config import settings as _default_settings
from app.core.deps import get_twilio_client
from app.repositories.store import Store, get_store
from app.services.whatsapp_service import WhatsappService

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
    store: Store = Depends(get_store),
    cfg: Settings = Depends(get_settings),
    twilio_client: Annotated[object, Depends(get_twilio_client)] = None,
):
    """
    Configurar em: Sandbox Settings → "When a message comes in"
    URL: POST /whatsapp/webhook
    """
    await _validate_twilio_signature(request, cfg)

    form = await request.form()
    payload = dict(form)

    from_number = payload.get("From", "")
    sid = payload.get("MessageSid", "")
    logger.info("Mensagem inbound | from=%s sid=%s body=%r", from_number, sid, payload.get("Body"))

    svc = WhatsappService(store, twilio_client, cfg.twilio_whatsapp_from)
    try:
        svc.processar_webhook(payload)
    except Exception:
        # Sempre retorna 200: resposta não-200 faz o Twilio retentar o webhook.
        logger.exception("Erro ao processar mensagem | sid=%s", sid)

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


@router.get("/sessions/{session_id}/messages")
def list_session_messages(session_id: UUID, store: Store = Depends(get_store)):
    """Lista todas as mensagens de uma sessão em ordem cronológica."""
    sessao = store.whatsapp_sessoes.get(session_id)
    if not sessao:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    msgs = store.whatsapp_mensagens.list_by(sessao_id=session_id)
    return sorted(msgs, key=lambda m: m.criado_em)
