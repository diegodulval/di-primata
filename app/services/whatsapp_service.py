import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from app.models.account import Account
from app.models.cycle import Cycle
from app.models.enums import EstadoAgente, OrigemCaptura, StatusCiclo, TipoEvento, TipoUnidade
from app.models.event import Event
from app.models.unit import Unit
from app.models.whatsapp import DirecaoMensagem, WhatsappMensagem, WhatsappSessao
from app.repositories.store import Store

logger = logging.getLogger(__name__)

_WHATSAPP_PREFIX = "whatsapp:"
_RESET_KEYWORDS = {"menu", "reiniciar", "início", "inicio", "0", "voltar", "cancelar"}

_ATIVIDADE_MAP: dict[str, str] = {
    "adubação": "adubacao",
    "adubacao": "adubacao",
    "adubar": "adubacao",
    "fertilização": "adubacao",
    "fertilizacao": "adubacao",
    "irrigação": "irrigacao",
    "irrigacao": "irrigacao",
    "irrigar": "irrigacao",
    "colheita": "colheita",
    "colher": "colheita",
    "poda": "poda",
    "pulverização": "pulverizacao",
    "pulverizacao": "pulverizacao",
    "pulverizar": "pulverizacao",
}

_ATIVIDADE_LABEL: dict[str, str] = {
    "adubacao": "adubação",
    "irrigacao": "irrigação",
    "colheita": "colheita",
    "poda": "poda",
    "pulverizacao": "pulverização",
}


def _strip_prefix(raw: str) -> str:
    return raw.removeprefix(_WHATSAPP_PREFIX)


def _normalizar_atividade(body: str) -> str | None:
    return _ATIVIDADE_MAP.get(body.lower().strip())


def _label_atividade(tipo: str) -> str:
    return _ATIVIDADE_LABEL.get(tipo, tipo)


def _parse_valor(body: str) -> float:
    s = body.strip().lower().replace("r$", "").strip()
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    return float(s)


class WhatsappService:
    def __init__(self, store: Store, twilio_client: Any, from_number: str) -> None:
        self.store = store
        self._from = from_number
        self._client = twilio_client

    # ── Ponto de entrada do webhook ───────────────────────────────────────────

    def processar_webhook(self, payload: dict[str, str]) -> str | None:
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

        # Deduplicação: ignora retentativas do Twilio com o mesmo SID
        if self.store.whatsapp_mensagens.find_one(sid=sid):
            logger.info("SID duplicado ignorado | sid=%s", sid)
            return None

        sessao = self._obter_ou_criar_sessao(phone, profile_name)
        self._registrar_mensagem(sessao, sid, DirecaoMensagem.INBOUND, body, num_midia, midia_urls)

        logger.debug(
            "Processando | phone=%s estado=%s passo=%s body=%r",
            phone, sessao.estado, sessao.contexto_json.get("passo"), body,
        )

        if body.lower() in _RESET_KEYWORDS:
            resposta = self._resetar_sessao(sessao)
        else:
            resposta = self._despachar(sessao, body, num_midia, payload)
        if resposta:
            self.enviar(phone, resposta, sessao)

        return resposta

    # ── Envio ─────────────────────────────────────────────────────────────────

    def enviar(self, phone: str, texto: str, sessao: WhatsappSessao | None = None) -> str:
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
            if not sessao.account_id:
                conta = self.store.accounts.find_one(whatsapp_phone=phone)
                if conta:
                    sessao.account_id = conta.id
                    logger.info("Sessão vinculada a account | phone=%s account_id=%s", phone, conta.id)
                else:
                    phones_cadastrados = [
                        a.whatsapp_phone for a in self.store.accounts.list_all()
                    ]
                    logger.warning(
                        "Nenhuma conta com whatsapp_phone=%r | cadastrados=%s",
                        phone, phones_cadastrados,
                    )
            self.store.whatsapp_sessoes.save(sessao)
            return sessao

        conta = self.store.accounts.find_one(whatsapp_phone=phone)
        if not conta:
            phones_cadastrados = [a.whatsapp_phone for a in self.store.accounts.list_all()]
            logger.warning(
                "Nova sessão SEM conta vinculada | phone=%r | cadastrados=%s",
                phone, phones_cadastrados,
            )
        sessao = WhatsappSessao(
            phone=phone,
            profile_name=profile_name,
            account_id=conta.id if conta else None,
        )
        self.store.whatsapp_sessoes.save(sessao)
        logger.info("Nova sessão WhatsApp | phone=%s account_id=%s", phone, sessao.account_id)
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
        handlers = {
            EstadoAgente.OCIOSO: self._handle_ocioso,
            EstadoAgente.ESCUTANDO: self._handle_escutando,
            EstadoAgente.PROCESSANDO: self._handle_processando,
            EstadoAgente.AGUARD_CONFIRM: self._handle_aguard_confirm,
        }
        handler = handlers.get(sessao.estado, self._handle_fallback)
        return handler(sessao, body, num_midia, payload)

    def _menu(self, sessao: WhatsappSessao, prefixo: str = "") -> str:
        sessao.estado = EstadoAgente.ESCUTANDO
        self.store.whatsapp_sessoes.save(sessao)
        return (
            prefixo
            + "Como posso ajudar?\n"
            "• *1* — Registrar atividade\n"
            "• *2* — Consultar ciclo\n"
            "• *3* — Falar com técnico\n\n"
            "Responda com o número da opção."
        )

    def _montar_pergunta_talhao(self, sessao: WhatsappSessao) -> str:
        """Popula context com opções de talhão e retorna texto da pergunta. Não salva."""
        units = self.store.units.list_by(account_id=sessao.account_id, ativo=True)
        if not units:
            sessao.contexto_json["passo"] = "nome_talhao"
            return "Nenhum talhão cadastrado ainda.\nQual o *nome do talhão* onde você está?"
        opcoes = [{"id": str(u.id), "nome": u.nome} for u in units]
        sessao.contexto_json["talhoes_opcoes"] = opcoes
        sessao.contexto_json["passo"] = "selecionar_talhao"
        lista = "\n".join(f"• *{i + 1}* — {u['nome']}" for i, u in enumerate(opcoes))
        return f"Em qual talhão você está?\n{lista}\n• *novo* — Cadastrar novo talhão"

    def _handle_ocioso(
        self,
        sessao: WhatsappSessao,
        body: str,
        num_midia: int,
        payload: dict[str, Any],
    ) -> str:
        nome = sessao.profile_name or "produtor"
        saudacao = f"Olá, {nome}! Sou o assistente Di Mata. 🌱\n\n"

        if not sessao.account_id:
            sessao.estado = EstadoAgente.PROCESSANDO
            sessao.contexto_json.update({"fluxo": "identificar_contexto", "passo": "propriedade"})
            self.store.whatsapp_sessoes.save(sessao)
            return saudacao + "Qual o *nome da sua propriedade*?"

        if not sessao.unit_id:
            sessao.estado = EstadoAgente.PROCESSANDO
            sessao.contexto_json["fluxo"] = "identificar_contexto"
            pergunta = self._montar_pergunta_talhao(sessao)
            self.store.whatsapp_sessoes.save(sessao)
            return saudacao + pergunta

        return self._menu(sessao, saudacao)

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
            sessao.contexto_json["passo"] = "tipo_atividade"
            self.store.whatsapp_sessoes.save(sessao)
            return "Qual atividade foi realizada?\nEx: *adubação*, *irrigação*, *colheita*, *poda*"
        if opcao == "2":
            return "Funcionalidade de consulta de ciclo em breve. 🚜"
        if opcao == "3":
            sessao.estado = EstadoAgente.OCIOSO
            self.store.whatsapp_sessoes.save(sessao)
            return "Seu técnico será notificado. Aguarde o contato. 📲"
        return "Opção não reconhecida. Responda com *1*, *2* ou *3*."

    # ── Fluxo: registrar atividade ────────────────────────────────────────────

    def _handle_processando(
        self,
        sessao: WhatsappSessao,
        body: str,
        num_midia: int,
        payload: dict[str, Any],
    ) -> str:
        fluxo = sessao.contexto_json.get("fluxo")
        if fluxo == "identificar_contexto":
            return self._passo_identificar_contexto(sessao, body)
        if fluxo == "registrar_atividade":
            return self._passo_registrar_atividade(sessao, body)
        return self._handle_fallback(sessao, body, num_midia, payload)

    # ── Fluxo: identificar propriedade e talhão ───────────────────────────────

    def _passo_identificar_contexto(self, sessao: WhatsappSessao, body: str) -> str:
        passo = sessao.contexto_json.get("passo")

        if passo == "propriedade":
            nome = body.strip()
            if len(nome) < 2:
                return "Digite o nome da sua propriedade."
            todas = self.store.accounts.list_all()
            match = next((a for a in todas if a.nome.lower() == nome.lower()), None)
            if match:
                sessao.account_id = match.id
                pergunta = self._montar_pergunta_talhao(sessao)
                self.store.whatsapp_sessoes.save(sessao)
                return f"Propriedade *{match.nome}* encontrada! ✅\n\n{pergunta}"
            sessao.contexto_json["nome_prop"] = nome
            sessao.contexto_json["passo"] = "confirmar_nova_prop"
            self.store.whatsapp_sessoes.save(sessao)
            return (
                f"Não encontrei a propriedade *{nome}*.\n"
                "Deseja cadastrá-la? (*sim* / *não*)"
            )

        if passo == "confirmar_nova_prop":
            if body.lower().strip() in ("sim", "s", "yes"):
                nome_prop = sessao.contexto_json.pop("nome_prop", "Propriedade")
                phone = sessao.phone
                account = Account(
                    nome=nome_prop,
                    documento=phone,
                    email=f"{phone.lstrip('+')}@whatsapp.dimata.local",
                    setor_primario="agro",
                    whatsapp_phone=phone,
                )
                self.store.accounts.save(account)
                sessao.account_id = account.id
                logger.info("Propriedade criada via WhatsApp | account=%s phone=%s", account.id, phone)
                pergunta = self._montar_pergunta_talhao(sessao)
                self.store.whatsapp_sessoes.save(sessao)
                return f"Propriedade *{nome_prop}* cadastrada! ✅\n\n{pergunta}"
            sessao.contexto_json["passo"] = "propriedade"
            sessao.contexto_json.pop("nome_prop", None)
            self.store.whatsapp_sessoes.save(sessao)
            return "Tudo bem. Qual o *nome da sua propriedade*?"

        if passo == "selecionar_talhao":
            opcoes = sessao.contexto_json.get("talhoes_opcoes") or []
            if body.lower().strip() in ("novo", "n", "outro"):
                sessao.contexto_json["passo"] = "nome_talhao"
                sessao.contexto_json.pop("talhoes_opcoes", None)
                self.store.whatsapp_sessoes.save(sessao)
                return "Qual o *nome do novo talhão*?"
            if not opcoes:
                pergunta = self._montar_pergunta_talhao(sessao)
                self.store.whatsapp_sessoes.save(sessao)
                return pergunta
            try:
                idx = int(body.strip()) - 1
                if idx < 0 or idx >= len(opcoes):
                    raise ValueError
            except ValueError:
                nums = ", ".join(f"*{i + 1}*" for i in range(len(opcoes)))
                return f"Opção inválida. Responda com {nums} ou *novo* para cadastrar."
            sessao.unit_id = UUID(opcoes[idx]["id"])
            unit_nome = opcoes[idx]["nome"]
            sessao.contexto_json.clear()
            self.store.whatsapp_sessoes.save(sessao)
            return self._menu(sessao, f"Talhão *{unit_nome}* selecionado! ✅\n\n")

        if passo == "nome_talhao":
            nome = body.strip()
            if len(nome) < 2:
                return "Digite o nome do talhão."
            unit = Unit(
                account_id=sessao.account_id,
                nome=nome,
                tipo=TipoUnidade.TALHAO,
                setor_template="geral",
            )
            self.store.units.save(unit)
            sessao.unit_id = unit.id
            sessao.contexto_json.clear()
            self.store.whatsapp_sessoes.save(sessao)
            logger.info("Talhão criado via WhatsApp | unit=%s account=%s", unit.id, sessao.account_id)
            return self._menu(sessao, f"Talhão *{nome}* cadastrado! ✅\n\n")

        return self._handle_fallback(sessao, body, 0, {})

    def _passo_registrar_atividade(self, sessao: WhatsappSessao, body: str) -> str:
        passo = sessao.contexto_json.get("passo", "tipo_atividade")

        if passo == "tipo_atividade":
            if not sessao.account_id:
                sessao.estado = EstadoAgente.OCIOSO
                sessao.contexto_json.clear()
                self.store.whatsapp_sessoes.save(sessao)
                return (
                    "Seu número não está vinculado a nenhuma propriedade. "
                    "Fale com seu técnico para fazer o cadastro. 📞"
                )

            tipo = _normalizar_atividade(body)
            if not tipo:
                return (
                    "Atividade não reconhecida. Tente:\n"
                    "*adubação*, *irrigação*, *colheita*, *poda*, *pulverização*"
                )

            sessao.contexto_json["tipo"] = tipo

            # Talhão pré-vinculado pelo admin — pula a etapa de seleção
            if sessao.unit_id:
                sessao.contexto_json["unit_id"] = str(sessao.unit_id)
                sessao.contexto_json["passo"] = "valor_gasto"
                self.store.whatsapp_sessoes.save(sessao)
                return (
                    f"Qual o valor gasto com *{_label_atividade(tipo)}*? (R$)\n"
                    "Ex: *350,00*"
                )

            units = self.store.units.list_by(account_id=sessao.account_id, ativo=True)
            if not units:
                sessao.estado = EstadoAgente.OCIOSO
                sessao.contexto_json.clear()
                self.store.whatsapp_sessoes.save(sessao)
                return (
                    "Nenhuma unidade cadastrada para sua propriedade. "
                    "Fale com seu técnico. 📞"
                )

            if len(units) == 1:
                sessao.contexto_json["unit_id"] = str(units[0].id)
                sessao.contexto_json["passo"] = "valor_gasto"
                self.store.whatsapp_sessoes.save(sessao)
                return (
                    f"Qual o valor gasto com *{_label_atividade(tipo)}*? (R$)\n"
                    "Ex: *350,00*"
                )

            opcoes = [{"id": str(u.id), "nome": u.nome} for u in units]
            sessao.contexto_json["units_opcoes"] = opcoes
            sessao.contexto_json["passo"] = "selecionar_talhao"
            self.store.whatsapp_sessoes.save(sessao)
            lista = "\n".join(f"• *{i + 1}* — {u['nome']}" for i, u in enumerate(opcoes))
            return f"Qual talhão?\n{lista}"

        if passo == "selecionar_talhao":
            opcoes = sessao.contexto_json.get("units_opcoes") or []
            # Contexto perdido (ex: retry do Twilio limpou o estado) — recarrega as opções
            if not opcoes:
                logger.warning("units_opcoes ausente no contexto | sessao=%s", sessao.id)
                units = self.store.units.list_by(account_id=sessao.account_id, ativo=True)
                if not units:
                    sessao.estado = EstadoAgente.OCIOSO
                    sessao.contexto_json.clear()
                    self.store.whatsapp_sessoes.save(sessao)
                    return "Nenhuma unidade cadastrada para sua propriedade. Fale com seu técnico. 📞"
                opcoes = [{"id": str(u.id), "nome": u.nome} for u in units]
                sessao.contexto_json["units_opcoes"] = opcoes
                self.store.whatsapp_sessoes.save(sessao)
                lista = "\n".join(f"• *{i + 1}* — {u['nome']}" for i, u in enumerate(opcoes))
                return f"Qual talhão? (escolha novamente)\n{lista}"

            try:
                idx = int(body.strip()) - 1
                if idx < 0 or idx >= len(opcoes):
                    raise ValueError
            except ValueError:
                nums = ", ".join(f"*{i + 1}*" for i in range(len(opcoes)))
                return f"Opção inválida. Responda com {nums}."

            sessao.contexto_json["unit_id"] = opcoes[idx]["id"]
            del sessao.contexto_json["units_opcoes"]
            sessao.contexto_json["passo"] = "valor_gasto"
            self.store.whatsapp_sessoes.save(sessao)
            tipo = sessao.contexto_json.get("tipo", "atividade")
            return (
                f"Qual o valor gasto com *{_label_atividade(tipo)}*? (R$)\n"
                "Ex: *350,00*"
            )

        if passo == "valor_gasto":
            try:
                valor = _parse_valor(body)
                if valor < 0:
                    raise ValueError
            except ValueError:
                return "Valor inválido. Informe o valor em reais (ex: *350,00* ou *350*)."

            sessao.contexto_json["valor"] = str(valor)
            sessao.estado = EstadoAgente.AGUARD_CONFIRM
            self.store.whatsapp_sessoes.save(sessao)

            tipo = sessao.contexto_json.get("tipo", "atividade")
            unit_id = sessao.contexto_json.get("unit_id")
            unit = self.store.units.get(UUID(unit_id)) if unit_id else None
            unit_nome = unit.nome if unit else "—"

            return (
                "Confirmar registro?\n"
                f"📋 Atividade: {_label_atividade(tipo)}\n"
                f"🌱 Talhão: {unit_nome}\n"
                f"💰 Valor: R$ {valor:,.2f}\n"
                f"📅 Data: {datetime.now(UTC).strftime('%d/%m/%Y')}\n\n"
                "Responda *sim* para confirmar ou *não* para cancelar."
            )

        return self._handle_fallback(sessao, body, 0, {})

    def _handle_aguard_confirm(
        self,
        sessao: WhatsappSessao,
        body: str,
        num_midia: int,
        payload: dict[str, Any],
    ) -> str:
        if body.lower() in ("sim", "s", "yes", "1"):
            if sessao.contexto_json.get("fluxo") == "registrar_atividade":
                try:
                    self._persistir_evento_atividade(sessao)
                except Exception:
                    logger.exception(
                        "Falha ao persistir atividade | sessao=%s ctx=%s",
                        sessao.id, sessao.contexto_json,
                    )
                    sessao.estado = EstadoAgente.OCIOSO
                    sessao.contexto_json.clear()
                    self.store.whatsapp_sessoes.save(sessao)
                    return "Ocorreu um erro ao registrar. Tente novamente ou fale com seu técnico. 📞"
            sessao.estado = EstadoAgente.OCIOSO
            sessao.contexto_json.clear()
            self.store.whatsapp_sessoes.save(sessao)
            return "Registrado com sucesso! ✅"

        sessao.estado = EstadoAgente.ESCUTANDO
        sessao.contexto_json.clear()
        self.store.whatsapp_sessoes.save(sessao)
        return "Operação cancelada. Digite *1*, *2* ou *3* para continuar."

    def _persistir_evento_atividade(self, sessao: WhatsappSessao) -> None:
        account_id = sessao.account_id
        unit_id = UUID(sessao.contexto_json["unit_id"])
        tipo = sessao.contexto_json.get("tipo", "operacao")
        valor = float(sessao.contexto_json.get("valor", "0"))

        ciclos = self.store.cycles.list_by(account_id=account_id, unit_id=unit_id)
        ciclo = next(
            (c for c in ciclos if c.status in (StatusCiclo.ABERTO, StatusCiclo.EM_PRODUCAO)),
            None,
        )
        if not ciclo:
            unit = self.store.units.get(unit_id)
            unit_code = unit.nome[:3].upper() if unit else "UNK"
            year = datetime.now(UTC).year
            ciclo = Cycle(
                account_id=account_id,
                unit_id=unit_id,
                codigo=f"WA-{unit_code}-{year}",
                produto=unit.setor_template if unit else "geral",
            )
            self.store.cycles.save(ciclo)
            logger.info("Ciclo criado via WhatsApp | ciclo=%s unit=%s", ciclo.id, unit_id)

        event = Event(
            ciclo_id=ciclo.id,
            tipo_evento=TipoEvento.OPERACAO,
            descricao=_label_atividade(tipo),
            payload_json={"tipo_atividade": tipo, "valor_gasto": valor},
            origem=OrigemCaptura.VOZ,
        )
        self.store.events.save(event)
        logger.info(
            "Evento registrado via WhatsApp | ciclo=%s tipo=%s valor=%s",
            ciclo.id, tipo, valor,
        )

    def _handle_fallback(
        self,
        sessao: WhatsappSessao,
        body: str,
        num_midia: int,
        payload: dict[str, Any],
    ) -> str:
        sessao.estado = EstadoAgente.OCIOSO
        sessao.contexto_json.clear()
        self.store.whatsapp_sessoes.save(sessao)
        return "Desculpe, não entendi. Digite qualquer mensagem para recomeçar."
