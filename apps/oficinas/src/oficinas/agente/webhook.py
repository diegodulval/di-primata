"""
Webhook Meta WhatsApp Business Cloud API.

GET  /webhook/whatsapp  — verificação do webhook (challenge Meta)
POST /webhook/whatsapp  — recebe mensagens; chama worker; responde via Graph API
"""

import hashlib
import hmac
import secrets

import httpx
import structlog
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from oficinas.core.config import settings
from oficinas.core.database import get_raw_db
from fastapi import Depends

from oficinas.agente import worker

log = structlog.get_logger()

router = APIRouter(prefix="/webhook", tags=["agente"])

_GRAPH_URL = "https://graph.facebook.com/v19.0"


# ─── Verificação de webhook (handshake Meta) ──────────────────────────────────

@router.get("/whatsapp", response_class=PlainTextResponse)
def verificar_webhook(
    hub_mode: str = Query(alias="hub.mode", default=""),
    hub_challenge: str = Query(alias="hub.challenge", default=""),
    hub_verify_token: str = Query(alias="hub.verify_token", default=""),
) -> str:
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        log.info("whatsapp_webhook_verificado")
        return hub_challenge
    raise HTTPException(status_code=403, detail="Verify token inválido")


# ─── Receber mensagem ─────────────────────────────────────────────────────────

@router.post("/whatsapp")
async def receber_mensagem(
    request: Request,
    db: AsyncSession = Depends(get_raw_db),
):
    body = await request.body()
    _validar_hmac(request, body)

    data = await request.json()

    # Ignorar eventos que não são mensagens de texto
    mensagem = _extrair_mensagem(data)
    if not mensagem:
        return {"status": "ignored"}

    numero = mensagem["from"]
    texto = _extrair_texto(mensagem)
    if not texto:
        return {"status": "tipo_nao_suportado"}

    log.info("whatsapp_mensagem_recebida", numero=numero, chars=len(texto))

    resposta = await worker.processar(db, numero, texto)
    if resposta is None:
        await _enviar_mensagem(
            numero,
            "Número não cadastrado. Fale com seu gestor para registrar seu WhatsApp.",
        )
    else:
        # WhatsApp suporta até 4096 chars por mensagem
        for parte in _dividir(resposta, 4096):
            await _enviar_mensagem(numero, parte)

    return {"status": "ok"}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _validar_hmac(request: Request, body: bytes) -> None:
    """Valida assinatura HMAC-SHA256 da Meta. Pulado se app_secret não configurado."""
    app_secret = settings.whatsapp_app_secret
    if not app_secret:
        return
    sig_header = request.headers.get("X-Hub-Signature-256", "")
    if not sig_header.startswith("sha256="):
        raise HTTPException(status_code=400, detail="Assinatura ausente")
    expected = "sha256=" + hmac.new(
        app_secret.encode(), body, hashlib.sha256
    ).hexdigest()
    if not secrets.compare_digest(sig_header, expected):
        raise HTTPException(status_code=403, detail="Assinatura inválida")


def _extrair_mensagem(data: dict) -> dict | None:
    """Extrai o primeiro objeto de mensagem do payload Meta."""
    try:
        entry = data["entry"][0]
        change = entry["changes"][0]
        value = change["value"]
        msgs = value.get("messages")
        if not msgs:
            return None
        return msgs[0]
    except (KeyError, IndexError):
        return None


def _extrair_texto(mensagem: dict) -> str | None:
    """Extrai texto de mensagens de texto simples."""
    tipo = mensagem.get("type")
    if tipo == "text":
        return mensagem.get("text", {}).get("body", "").strip() or None
    return None


def _dividir(texto: str, tamanho: int) -> list[str]:
    """Divide texto longo em partes menores."""
    return [texto[i : i + tamanho] for i in range(0, len(texto), tamanho)]


async def _enviar_mensagem(numero: str, texto: str) -> None:
    """Envia mensagem de texto via Meta Graph API."""
    if not settings.whatsapp_phone_id or not settings.whatsapp_token:
        log.warning("whatsapp_nao_configurado", numero=numero)
        return
    url = f"{_GRAPH_URL}/{settings.whatsapp_phone_id}/messages"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            url,
            headers={"Authorization": f"Bearer {settings.whatsapp_token}"},
            json={
                "messaging_product": "whatsapp",
                "to": numero,
                "type": "text",
                "text": {"body": texto},
            },
        )
    if resp.status_code not in (200, 201):
        log.error("whatsapp_envio_falhou", status=resp.status_code, body=resp.text)
