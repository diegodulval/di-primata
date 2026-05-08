import logging
from datetime import UTC, datetime
from typing import Any

from app.models.enums import EstadoAgente
from app.models.whatsapp import DirecaoMensagem, WhatsappMensagem, WhatsappSessao
from app.repositories.store import Store

logger = logging.getLogger(__name__)

_WHATSAPP_PREFIX = "whatsapp:"
_RESET_KEYWORDS = {"menu", "reiniciar", "início", "inicio", "0", "voltar", "cancelar"}


def _strip_prefix(raw: str) -> str:
    """Remove o prefixo 'whatsapp:' retornando apenas o número E.164."""
    return raw.removeprefix(_WHATSAPP_PREFIX)


class WhatsappService:
    def __init__(self, store: Store, twilio_client: Any, from_number: str) -> None:
        self.store = store
        self._from = from_number
        self._client = twilio_client

    # ── Ponto de entrada do webhook ───────────────────────────────────────────

    def processar_webhook(self, payload: dict[str, str]) -> str | None:
        """Processa payload do webhook Twilio e retorna texto de resposta (ou None)."""
        phone = _strip_prefix(payload.get("From", ""))
        body = payload.get("Body", "").strip()
        sid = payload.get("MessageSid", "")
        profile_name = payload.get("ProfileName") or None
        num_midia = int(payload.get("NumMedia", "0"))
        midia_urls = [
            payload[f"MediaUrl{i}"] for i in range(num_midia) if f"MediaUrl{i}" in payload
        ]

        if not phone or not sid:
            logger.warning("Webhook ignorado: From ou MessageSid ausente")
            return None

        sessao = self._obter_ou_criar_sessao(phone, profile_name)
        self._registrar_mensagem(sessao, sid, DirecaoMensagem.INBOUND, body, num_midia, midia_urls)

        if body.lower() in _RESET_KEYWORDS:
            resposta = self._resetar_sessao(sessao)
        else:
            resposta = self._despachar(sessao, body, num_midia, payload)
        if resposta:
            self.enviar(phone, resposta, sessao)

        return resposta

    # ── Envio ─────────────────────────────────────────────────────────────────

    def enviar(self, phone: str, texto: str, sessao: WhatsappSessao | None = None) -> str:
        """Envia mensagem WhatsApp via Twilio REST. Retorna o MessageSid."""
        if not self._client:
            logger.debug("Twilio client não configurado — envio simulado para %s: %s", phone, texto)
            sid = f"SIMULATED-{phone}"
            if sessao:
                self._registrar_mensagem(sessao, sid, DirecaoMensagem.OUTBOUND, texto, 0, [])
            return sid

        try:
            msg = self._client.messages.create(
                from_=f"{_WHATSAPP_PREFIX}{self._from}",
                to=f"{_WHATSAPP_PREFIX}{phone}",
                body=texto,
            )
        except Exception as exc:
            logger.error("Falha ao enviar mensagem para %s: %s", phone, exc)
            return f"ERROR-{phone}"

        logger.info("Mensagem enviada para %s | sid=%s", phone, msg.sid)
        if sessao:
            self._registrar_mensagem(sessao, msg.sid, DirecaoMensagem.OUTBOUND, texto, 0, [])
        return msg.sid

    # ── Sessão ────────────────────────────────────────────────────────────────

    def _obter_ou_criar_sessao(self, phone: str, profile_name: str | None) -> WhatsappSessao:
        existentes = self.store.whatsapp_sessoes.list_by(phone=phone)
        if existentes:
            sessao = existentes[0]
            sessao.ultima_atividade_em = datetime.now(UTC)
            if profile_name and sessao.profile_name != profile_name:
                sessao.profile_name = profile_name
            self.store.whatsapp_sessoes.save(sessao)
            return sessao

        sessao = WhatsappSessao(phone=phone, profile_name=profile_name)
        self.store.whatsapp_sessoes.save(sessao)
        logger.info("Nova sessão WhatsApp criada | phone=%s", phone)
        return sessao

    def _registrar_mensagem(
        self,
        sessao: WhatsappSessao,
        sid: str,
        direcao: DirecaoMensagem,
        corpo: str,
        num_midia: int,
        midia_urls: list[str],
    ) -> WhatsappMensagem:
        msg = WhatsappMensagem(
            sessao_id=sessao.id,
            sid=sid,
            direcao=direcao,
            corpo=corpo,
            num_midia=num_midia,
            midia_urls=midia_urls,
        )
        self.store.whatsapp_mensagens.save(msg)
        return msg

    # ── Reset ─────────────────────────────────────────────────────────────────

    def _resetar_sessao(self, sessao: WhatsappSessao) -> str:
        sessao.estado = EstadoAgente.OCIOSO
        sessao.contexto_json.clear()
        self.store.whatsapp_sessoes.save(sessao)
        logger.info("Sessão reiniciada | phone=%s", sessao.phone)
        return self._handle_ocioso(sessao, "", 0, {})

    # ── Despachante de estado ─────────────────────────────────────────────────

    def _despachar(
        self,
        sessao: WhatsappSessao,
        body: str,
        num_midia: int,
        payload: dict[str, Any],
    ) -> str | None:
        """
        Máquina de estados base. Cada EstadoAgente roteia para um handler.
        Expandir adicionando novos handlers conforme os fluxos agrícolas evoluírem.
        """
        handlers = {
            EstadoAgente.OCIOSO: self._handle_ocioso,
            EstadoAgente.ESCUTANDO: self._handle_escutando,
            EstadoAgente.AGUARD_CONFIRM: self._handle_aguard_confirm,
        }
        handler = handlers.get(sessao.estado, self._handle_fallback)
        return handler(sessao, body, num_midia, payload)

    def _handle_ocioso(
        self,
        sessao: WhatsappSessao,
        body: str,
        num_midia: int,
        payload: dict[str, Any],
    ) -> str:
        sessao.estado = EstadoAgente.ESCUTANDO
        self.store.whatsapp_sessoes.save(sessao)
        nome = sessao.profile_name or "produtor"
        return (
            f"Olá, {nome}! Sou o assistente Di Mata. 🌱\n\n"
            "Como posso ajudar?\n"
            "• *1* — Registrar atividade\n"
            "• *2* — Consultar safra\n"
            "• *3* — Falar com técnico\n\n"
            "Responda com o número da opção."
        )

    def _handle_escutando(
        self,
        sessao: WhatsappSessao,
        body: str,
        num_midia: int,
        payload: dict[str, Any],
    ) -> str:
        opcao = body.strip()
        if opcao == "1":
            sessao.estado = EstadoAgente.PROCESSANDO
            sessao.contexto_json["fluxo"] = "registrar_atividade"
            self.store.whatsapp_sessoes.save(sessao)
            return "Qual atividade foi realizada? (ex: adubação, irrigação, colheita)"
        if opcao == "2":
            return "Funcionalidade de consulta de safra em breve. 🚜"
        if opcao == "3":
            sessao.estado = EstadoAgente.OCIOSO
            self.store.whatsapp_sessoes.save(sessao)
            return "Seu técnico será notificado. Aguarde o contato. 📲"
        return "Opção não reconhecida. Responda com *1*, *2* ou *3*."

    def _handle_aguard_confirm(
        self,
        sessao: WhatsappSessao,
        body: str,
        num_midia: int,
        payload: dict[str, Any],
    ) -> str:
        if body.lower() in ("sim", "s", "yes", "1"):
            sessao.estado = EstadoAgente.OCIOSO
            sessao.contexto_json.clear()
            self.store.whatsapp_sessoes.save(sessao)
            return "Registrado com sucesso! ✅"
        sessao.estado = EstadoAgente.ESCUTANDO
        self.store.whatsapp_sessoes.save(sessao)
        return "Operação cancelada. Digite *1*, *2* ou *3* para continuar."

    def _handle_fallback(
        self,
        sessao: WhatsappSessao,
        body: str,
        num_midia: int,
        payload: dict[str, Any],
    ) -> str:
        sessao.estado = EstadoAgente.OCIOSO
        self.store.whatsapp_sessoes.save(sessao)
        return "Desculpe, não entendi. Digite qualquer mensagem para recomeçar."
