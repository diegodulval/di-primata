import json
import re
import uuid
from datetime import date

import structlog
from sqlalchemy import func, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from oficinas.core.exceptions import NaoEncontrado
from oficinas.modules.cadastros.models import Cliente, ClienteVeiculo
from oficinas.modules.cadastros.schemas import ClienteCreate, ClienteUpdate, ClienteVeiculoResponse, VeiculoResumo
from oficinas.shared.veiculo_global.models import Veiculo

log = structlog.get_logger()


class CadastroService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ─── Clientes ─────────────────────────────────────────────────────────────

    async def criar_cliente(self, tenant_id: uuid.UUID, payload: ClienteCreate) -> Cliente:
        cliente = Cliente(tenant_id=tenant_id, **payload.model_dump())
        self.db.add(cliente)
        await self.db.commit()
        await self.db.refresh(cliente)
        log.info("cliente_criado", cliente_id=str(cliente.id), tenant_id=str(tenant_id))
        return cliente

    async def listar_clientes(
        self,
        tenant_id: uuid.UUID,
        q: str | None = None,
        tipo_pessoa: str | None = None,
        ativo: bool | None = None,
        uf: str | None = None,
        placa: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Cliente], int]:
        base = select(Cliente).where(Cliente.tenant_id == tenant_id)

        if q:
            safe = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            pattern = f"%{safe}%"
            placa_subq = (
                select(ClienteVeiculo.cliente_id)
                .join(Veiculo, Veiculo.id == ClienteVeiculo.veiculo_id)
                .where(Veiculo.placa.ilike(pattern))
                .scalar_subquery()
            )
            base = base.where(or_(
                Cliente.nome.ilike(pattern),
                Cliente.cpf_cnpj.ilike(pattern),
                Cliente.telefone.ilike(pattern),
                Cliente.celular.ilike(pattern),
                Cliente.apelido.ilike(pattern),
                Cliente.id.in_(placa_subq),
            ))
        if tipo_pessoa:
            base = base.where(Cliente.tipo_pessoa == tipo_pessoa)
        if ativo is not None:
            base = base.where(Cliente.ativo.is_(ativo))
        if uf:
            base = base.where(Cliente.uf == uf.upper())
        if placa:
            base = (
                base
                .join(ClienteVeiculo, ClienteVeiculo.cliente_id == Cliente.id)
                .join(Veiculo, Veiculo.id == ClienteVeiculo.veiculo_id)
                .where(Veiculo.placa.ilike(
                    "%{}%".format(placa.strip().upper().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_"))
                ))
                .distinct()
            )

        total = (await self.db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
        offset = (page - 1) * page_size
        items = list(
            (await self.db.execute(base.order_by(Cliente.nome).offset(offset).limit(page_size)))
            .scalars()
            .all()
        )
        return items, total

    async def buscar_cliente(self, cliente_id: uuid.UUID, tenant_id: uuid.UUID) -> Cliente:
        stmt = select(Cliente).where(
            Cliente.id == cliente_id,
            Cliente.tenant_id == tenant_id,
        )
        cliente = (await self.db.execute(stmt)).scalar_one_or_none()
        if not cliente:
            raise NaoEncontrado(f"Cliente {cliente_id} não encontrado")
        return cliente

    async def atualizar_cliente(
        self, cliente_id: uuid.UUID, tenant_id: uuid.UUID, payload: ClienteUpdate
    ) -> Cliente:
        cliente = await self.buscar_cliente(cliente_id, tenant_id)
        for campo, valor in payload.model_dump(exclude_unset=True).items():
            setattr(cliente, campo, valor)
        await self.db.commit()
        await self.db.refresh(cliente)
        log.info("cliente_atualizado", cliente_id=str(cliente_id))
        return cliente

    async def importar_clientes_xlsx(
        self, tenant_id: uuid.UUID, conteudo: bytes
    ) -> dict:
        import io
        import openpyxl

        if conteudo[:4] == b"\xd0\xcf\x11\xe0":
            raise ValueError(
                "Formato .xls não suportado. Abra o arquivo no Excel e salve como "
                "'Pasta de Trabalho do Excel (.xlsx)' antes de importar."
            )

        try:
            wb = openpyxl.load_workbook(io.BytesIO(conteudo), data_only=True, read_only=True)
            ws = wb.active
            rows = list(ws.iter_rows(values_only=True))
        except Exception as exc:
            raise ValueError(f"Arquivo inválido: {exc}") from exc

        if not rows:
            raise ValueError("Planilha vazia")

        cabecalhos = {str(c).strip().lower() if c else "": i for i, c in enumerate(rows[0])}

        def col(row: tuple, *nomes: str) -> str | None:
            for nome in nomes:
                idx = cabecalhos.get(nome.lower())
                if idx is not None and idx < len(row):
                    val = row[idx]
                    s = str(val).strip() if val is not None else None
                    return s if s else None
            return None

        # Pré-carrega por CPF/CNPJ para upsert eficiente
        stmt = select(Cliente).where(
            Cliente.tenant_id == tenant_id, Cliente.cpf_cnpj.isnot(None)
        )
        existentes: dict[str, Cliente] = {
            c.cpf_cnpj: c
            for c in (await self.db.execute(stmt)).scalars().all()
            if c.cpf_cnpj
        }

        criados = atualizados = ignorados = 0
        erros: list[str] = []

        for num, row in enumerate(rows[1:], start=2):
            try:
                # Colunas do relatório do sistema concorrente
                nome_raw = col(row, "nome/razão social", "nome completo", "nome", "razao social")
                if not nome_raw:
                    ignorados += 1
                    continue

                # Status embutido no nome: "(INATIVO) Nome"
                ativo = True
                nome = nome_raw
                if nome_raw.upper().startswith("(INATIVO)"):
                    ativo = False
                    nome = nome_raw[9:].strip()

                cpf_raw = col(row, "cpf/cnpj", "cpf", "cnpj")
                cpf_cnpj = None
                if cpf_raw:
                    cpf_cnpj = cpf_raw.replace(".", "").replace("/", "").replace("-", "").replace(" ", "")
                    if len(cpf_cnpj) not in (11, 14):
                        cpf_cnpj = cpf_raw

                tipo_str = col(row, "tipo", "tipo de pessoa") or ""
                tipo_pessoa = "Juridica" if "jur" in tipo_str.lower() else "Fisica"

                # RG/IE: para Física é RG, para Jurídica é IE (ignoramos aqui — sem campo dedicado ainda)
                rg_ie = col(row, "rg/ie", "rg", "ie")
                rg = rg_ie if tipo_pessoa == "Fisica" else None
                ie = rg_ie if tipo_pessoa == "Juridica" else None

                # Endereço: junta Endereço + Nº + Bairro
                end_parts = [
                    col(row, "endereço(principal)", "endereço"),
                    col(row, "nº(principal)", "nº"),
                    col(row, "bairro(principal)", "bairro"),
                    col(row, "complemento(principal)", "complemento"),
                ]
                endereco = ", ".join(p for p in end_parts if p) or None

                cep_raw = col(row, "cep(principal)", "cep")
                cep = cep_raw.replace(".", "").replace("-", "").replace(" ", "")[:8] if cep_raw else None

                dados: dict = {
                    "nome":               nome,
                    "tipo_pessoa":        tipo_pessoa,
                    "cpf_cnpj":           cpf_cnpj,
                    "rg":                 rg,
                    "inscricao_estadual": ie,
                    "telefone":           col(row, "telefone comercial", "telefone residencial", "telefone"),
                    "celular":            col(row, "celular"),
                    "email":              col(row, "e-mail", "email"),
                    "cep":                cep,
                    "endereco":           endereco,
                    "cidade":             col(row, "cidade(principal)", "cidade"),
                    "uf":                 col(row, "estado(principal)", "uf", "estado"),
                    "apelido":            col(row, "apelido", "nome fantasia"),
                    "sexo":               col(row, "sexo"),
                    "observacoes":        col(row, "observações", "observacoes", "obs"),
                    "ativo":              ativo,
                }

                existente = existentes.get(cpf_cnpj) if cpf_cnpj else None

                if existente:
                    for campo, valor in dados.items():
                        if valor is not None:
                            setattr(existente, campo, valor)
                    atualizados += 1
                else:
                    novo = Cliente(tenant_id=tenant_id, **{k: v for k, v in dados.items() if v is not None})
                    self.db.add(novo)
                    if cpf_cnpj:
                        existentes[cpf_cnpj] = novo
                    criados += 1

            except Exception as exc:
                erros.append(f"Linha {num}: {exc}")

        await self.db.commit()
        log.info("clientes_importados", criados=criados, atualizados=atualizados, tenant_id=str(tenant_id))
        return {"criados": criados, "atualizados": atualizados, "ignorados": ignorados, "erros": erros}

    async def buscar_por_q(self, q: str, tenant_id: uuid.UUID) -> list[Cliente]:
        items, _ = await self.listar_clientes(tenant_id, q=q, page=1, page_size=20)
        return items

    async def importar_veiculos_json(
        self, tenant_id: uuid.UUID, conteudo: bytes
    ) -> dict:
        """
        Importa placas e vínculos cliente-veículo a partir do JSON exportado
        pelo sistema concorrente (suporta N páginas JSON concatenadas).

        Cadeia de matching (em ordem de prioridade):
          1. CPF/CNPJ — chave primária
          2. Telefone normalizado — só quando único no dataset e no DB
          3. Nome normalizado — só quando único no dataset e no DB

        Enriquece apelido, cidade, uf, telefone/celular quando nulos.
        Cria global.veiculo e cliente_veiculo. Transfere posse se necessário.
        """
        import unicodedata

        _PLACA_RE    = re.compile(r"^[A-Z]{3}[0-9]{4}$|^[A-Z]{3}[0-9][A-Z][0-9]{2}$")
        _ZERO_RE     = re.compile(r"^0+\d*$")
        _FAKE_TEL_RE = re.compile(r"^0+$")

        def _norm_tel(p: str) -> str:
            return re.sub(r"\D", "", p or "")

        def _real_tel(raw: dict) -> str | None:
            t = _norm_tel(raw.get("phone") or "")
            return t if len(t) >= 8 and not _FAKE_TEL_RE.match(t) else None

        def _norm_nome(s: str) -> str:
            s = (s or "").upper().strip()
            s = re.sub(r"^\(INATIVO\)\s*", "", s)
            s = "".join(
                c for c in unicodedata.normalize("NFD", s)
                if unicodedata.category(c) != "Mn"
            )
            s = re.sub(r"[^A-Z0-9 ]", "", s)
            return re.sub(r"\s+", " ", s).strip()

        # ── 1. Parseia N páginas JSON concatenadas ─────────────────────────────
        text = conteudo.decode("utf-8")
        parts = re.split(r"(?<=\})\s*\n(?=\{)", text.strip())

        raw_customers: dict[int, dict] = {}
        for part in parts:
            for c in json.loads(part)["serializedCustomers"]:
                if c["Code"] not in raw_customers:
                    raw_customers[c["Code"]] = c

        # ── 2. Conta colisões no dataset (só matches únicos são seguros) ───────
        json_tel_count:  dict[str, int] = {}
        json_nome_count: dict[str, int] = {}
        for raw in raw_customers.values():
            t = _real_tel(raw)
            if t:
                json_tel_count[t] = json_tel_count.get(t, 0) + 1
            json_nome_count[_norm_nome(raw["Company_Name"])] = (
                json_nome_count.get(_norm_nome(raw["Company_Name"]), 0) + 1
            )

        # ── 3. Pré-carrega todos os clientes do tenant ─────────────────────────
        all_clientes = list(
            (await self.db.execute(
                select(Cliente).where(Cliente.tenant_id == tenant_id)
            )).scalars().all()
        )

        # Índice por CPF/CNPJ
        by_cpf: dict[str, Cliente] = {
            c.cpf_cnpj: c for c in all_clientes if c.cpf_cnpj
        }

        # Índice por telefone normalizado — só quando único no DB também
        tel_db_count: dict[str, int] = {}
        for c in all_clientes:
            for raw_t in (c.telefone, c.celular):
                t = _norm_tel(raw_t or "")
                if len(t) >= 8:
                    tel_db_count[t] = tel_db_count.get(t, 0) + 1

        by_tel: dict[str, Cliente] = {}
        for c in all_clientes:
            for raw_t in (c.telefone, c.celular):
                t = _norm_tel(raw_t or "")
                if len(t) >= 8 and tel_db_count[t] == 1:
                    by_tel[t] = c

        # Índice por nome normalizado — só quando único no DB também
        nome_db_count: dict[str, int] = {}
        for c in all_clientes:
            nome_db_count[_norm_nome(c.nome)] = (
                nome_db_count.get(_norm_nome(c.nome), 0) + 1
            )

        by_nome: dict[str, Cliente] = {}
        for c in all_clientes:
            n = _norm_nome(c.nome)
            if nome_db_count[n] == 1:
                by_nome[n] = c

        # ── 4. Resolve cada cliente e coleta placas ───────────────────────────
        placa_set: set[str] = set()
        cliente_placas: list[tuple[Cliente, str]] = []

        match_cpf = match_tel = match_nome = nao_encontrados = enriquecidos = 0
        placas_ignoradas = 0
        erros: list[str] = []

        for raw in raw_customers.values():
            cliente: Cliente | None = None
            tier = ""

            cpf = (raw.get("Cpf_Cnpj") or "").strip()
            if cpf:
                cliente = by_cpf.get(cpf)
                if cliente:
                    tier = "cpf"

            if not cliente:
                t = _real_tel(raw)
                if t and json_tel_count.get(t, 0) == 1:
                    cliente = by_tel.get(t)
                    if cliente:
                        tier = "tel"

            if not cliente:
                n = _norm_nome(raw["Company_Name"])
                if json_nome_count.get(n, 0) == 1:
                    cliente = by_nome.get(n)
                    if cliente:
                        tier = "nome"

            if not cliente:
                nao_encontrados += 1
            else:
                if tier == "cpf":
                    match_cpf += 1
                elif tier == "tel":
                    match_tel += 1
                else:
                    match_nome += 1

                # Enriquece campos nulos
                enriched = False
                trading = (raw.get("Trading_Name") or "").strip()
                if trading and not cliente.apelido:
                    cliente.apelido = trading
                    enriched = True
                city = raw.get("principalAddressCity")
                if city and not cliente.cidade:
                    cliente.cidade = city
                    enriched = True
                state = raw.get("principalAddressState")
                if state and not cliente.uf:
                    cliente.uf = str(state).upper()[:2]
                    enriched = True
                t = _real_tel(raw)
                if t:
                    if not cliente.telefone:
                        cliente.telefone = t
                        enriched = True
                    elif not cliente.celular and _norm_tel(cliente.telefone) != t:
                        cliente.celular = t
                        enriched = True
                if enriched:
                    enriquecidos += 1

            # Coleta placas (veiculo global existe mesmo sem cliente identificado)
            for v in raw.get("Vehicle", []):
                plate = (v.get("License_Plate") or "").strip().upper()
                if not plate or _ZERO_RE.match(plate) or not _PLACA_RE.match(plate):
                    placas_ignoradas += 1
                    continue
                placa_set.add(plate)
                if cliente:
                    cliente_placas.append((cliente, plate))

        # ── 5. Bulk-upsert global.veiculo ─────────────────────────────────────
        placa_to_id: dict[str, uuid.UUID] = {}
        if placa_set:
            ins = pg_insert(Veiculo).values([{"placa": p} for p in placa_set])
            stmt_v = ins.on_conflict_do_update(
                index_elements=["placa"],
                set_={"placa": ins.excluded.placa},  # no-op: preserva dados existentes
            ).returning(Veiculo.id, Veiculo.placa)
            rows = (await self.db.execute(stmt_v)).all()
            placa_to_id = {row.placa: row.id for row in rows}

        # ── 6. Cria vínculos cliente_veiculo ──────────────────────────────────
        if placa_to_id:
            stmt_links = select(ClienteVeiculo).where(
                ClienteVeiculo.tenant_id == tenant_id,
                ClienteVeiculo.veiculo_id.in_(list(placa_to_id.values())),
            )
            existing_links: dict[uuid.UUID, ClienteVeiculo] = {
                lk.veiculo_id: lk
                for lk in (await self.db.execute(stmt_links)).scalars().all()
            }
        else:
            existing_links = {}

        vinculos_criados = 0
        for cliente, plate in cliente_placas:
            veiculo_id = placa_to_id.get(plate)
            if not veiculo_id:
                continue
            try:
                existing = existing_links.get(veiculo_id)
                if existing:
                    if existing.cliente_id == cliente.id:
                        continue
                    existing.ativo = False
                    existing.data_fim = date.today()
                    log.info(
                        "veiculo_troca_dono_importacao",
                        placa=plate,
                        cliente_anterior=str(existing.cliente_id),
                        novo_cliente=str(cliente.id),
                    )
                novo_link = ClienteVeiculo(
                    tenant_id=tenant_id,
                    cliente_id=cliente.id,
                    veiculo_id=veiculo_id,
                    data_inicio=date.today(),
                    ativo=True,
                )
                self.db.add(novo_link)
                existing_links[veiculo_id] = novo_link
                vinculos_criados += 1
            except Exception as exc:
                erros.append(f"{plate}: {exc}")

        await self.db.commit()
        log.info(
            "veiculos_importados",
            tenant_id=str(tenant_id),
            match_cpf=match_cpf,
            match_tel=match_tel,
            match_nome=match_nome,
            nao_encontrados=nao_encontrados,
            veiculos=len(placa_to_id),
            vinculos=vinculos_criados,
        )
        return {
            "match_cpf":                match_cpf,
            "match_telefone":           match_tel,
            "match_nome":               match_nome,
            "clientes_nao_encontrados": nao_encontrados,
            "clientes_enriquecidos":    enriquecidos,
            "veiculos_upserted":        len(placa_to_id),
            "vinculos_criados":         vinculos_criados,
            "placas_ignoradas":         placas_ignoradas,
            "erros":                    erros,
        }

    # ─── Vínculo cliente-veículo ───────────────────────────────────────────────

    async def vincular_veiculo(
        self,
        cliente_id: uuid.UUID,
        veiculo_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> ClienteVeiculo:
        await self.buscar_cliente(cliente_id, tenant_id)

        stmt = select(ClienteVeiculo).where(
            ClienteVeiculo.veiculo_id == veiculo_id,
            ClienteVeiculo.tenant_id == tenant_id,
            ClienteVeiculo.ativo.is_(True),
        )
        link_ativo = (await self.db.execute(stmt)).scalar_one_or_none()

        if link_ativo:
            if link_ativo.cliente_id == cliente_id:
                return link_ativo
            link_ativo.ativo = False
            link_ativo.data_fim = date.today()
            log.info(
                "veiculo_troca_dono",
                veiculo_id=str(veiculo_id),
                cliente_anterior=str(link_ativo.cliente_id),
                novo_cliente=str(cliente_id),
            )

        novo_link = ClienteVeiculo(
            tenant_id=tenant_id,
            cliente_id=cliente_id,
            veiculo_id=veiculo_id,
            data_inicio=date.today(),
            ativo=True,
        )
        self.db.add(novo_link)
        await self.db.commit()
        await self.db.refresh(novo_link)
        return novo_link

    async def listar_veiculos_cliente(
        self, cliente_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> list[ClienteVeiculoResponse]:
        await self.buscar_cliente(cliente_id, tenant_id)
        stmt = (
            select(ClienteVeiculo, Veiculo)
            .outerjoin(Veiculo, ClienteVeiculo.veiculo_id == Veiculo.id)
            .where(
                ClienteVeiculo.cliente_id == cliente_id,
                ClienteVeiculo.tenant_id == tenant_id,
            )
            .order_by(ClienteVeiculo.ativo.desc(), ClienteVeiculo.data_inicio.desc())
        )
        rows = (await self.db.execute(stmt)).all()
        result = []
        for link, veiculo in rows:
            resp = ClienteVeiculoResponse.model_validate(link)
            if veiculo:
                resp.veiculo = VeiculoResumo.model_validate(veiculo)
            result.append(resp)
        return result

    async def desassociar_veiculo(
        self,
        cliente_id: uuid.UUID,
        veiculo_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> ClienteVeiculo:
        stmt = select(ClienteVeiculo).where(
            ClienteVeiculo.cliente_id == cliente_id,
            ClienteVeiculo.veiculo_id == veiculo_id,
            ClienteVeiculo.tenant_id == tenant_id,
            ClienteVeiculo.ativo.is_(True),
        )
        link = (await self.db.execute(stmt)).scalar_one_or_none()
        if not link:
            raise NaoEncontrado("Vínculo ativo não encontrado para este cliente e veículo")
        link.ativo = False
        link.data_fim = date.today()
        await self.db.commit()
        await self.db.refresh(link)
        log.info("veiculo_desassociado", cliente_id=str(cliente_id), veiculo_id=str(veiculo_id))
        return link
