import uuid
from decimal import Decimal

import structlog
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from oficinas.core.enums import StatusEntradaNfe, StatusItem, StatusRascunho, TipoMovimentacao
from oficinas.core.exceptions import (
    NaoEncontrado,
    NFeJaImportada,
    RascunhoJaConfirmado,
    RascunhoPendente,
)
from oficinas.modules.estoque.models import (
    EntradaNfe,
    Fornecedor,
    ItemEntrada,
    ItemRascunhoEntrada,
    MapeamentoFornecedorProduto,
    Produto,
    RascunhoEntrada,
)
from oficinas.modules.estoque.parser import NFeParseResult, parse_nfe
from oficinas.modules.estoque.schemas import VincularItemPayload
from oficinas.modules.estoque.service import EstoqueService

log = structlog.get_logger()

_EDITAVEIS = {StatusRascunho.PENDENTE}


class RascunhoService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ─── Criar rascunho a partir de XML ──────────────────────────────────────

    async def criar_rascunho(
        self, xml_bytes: bytes, tenant_id: uuid.UUID
    ) -> tuple[RascunhoEntrada, list[ItemRascunhoEntrada]]:
        dados = parse_nfe(xml_bytes)

        if dados.chave:
            stmt = select(EntradaNfe).where(EntradaNfe.chave_nfe == dados.chave)
            if (await self.db.execute(stmt)).scalar_one_or_none():
                raise NFeJaImportada(f"NF-e {dados.chave} já importada")

        fornecedor = await self._upsert_fornecedor(tenant_id, dados)

        rascunho = RascunhoEntrada(
            tenant_id=tenant_id,
            fornecedor_id=fornecedor.id if fornecedor else None,
            chave_nfe=dados.chave or None,
            numero_nf=dados.numero or None,
            data_emissao=dados.data_emissao,
            valor_total=dados.valor_total,
            status=StatusRascunho.PENDENTE,
        )
        self.db.add(rascunho)
        await self.db.flush()

        itens: list[ItemRascunhoEntrada] = []
        for item_nfe in dados.itens:
            produto_id, status_item = await self._tentar_match(
                item_nfe.codigo,
                item_nfe.codigo_ref,
                item_nfe.ean,
                tenant_id,
                fornecedor.id if fornecedor else None,
            )
            item = ItemRascunhoEntrada(
                rascunho_id=rascunho.id,
                produto_id=produto_id,
                codigo_fornecedor=item_nfe.codigo,
                codigo_ref=item_nfe.codigo_ref,
                ean=item_nfe.ean,
                descricao_nfe=item_nfe.descricao,
                ncm=item_nfe.ncm or None,
                quantidade=item_nfe.quantidade,
                preco_unitario=item_nfe.preco_unitario,
                icms=item_nfe.icms,
                ipi=item_nfe.ipi,
                cfop=item_nfe.cfop,
                cst=item_nfe.cst,
                status_item=status_item,
            )
            self.db.add(item)
            itens.append(item)

        await self.db.commit()
        await self.db.refresh(rascunho)
        for item in itens:
            await self.db.refresh(item)

        log.info(
            "rascunho_criado",
            rascunho_id=str(rascunho.id),
            itens=len(itens),
            pendentes=sum(1 for i in itens if i.status_item == StatusItem.PENDENTE),
        )
        return rascunho, itens

    # ─── Buscar e listar ──────────────────────────────────────────────────────

    async def buscar(self, rascunho_id: uuid.UUID, tenant_id: uuid.UUID) -> RascunhoEntrada:
        stmt = select(RascunhoEntrada).where(
            RascunhoEntrada.id == rascunho_id,
            RascunhoEntrada.tenant_id == tenant_id,
        )
        r = (await self.db.execute(stmt)).scalar_one_or_none()
        if not r:
            raise NaoEncontrado(f"Rascunho {rascunho_id} não encontrado")
        return r

    async def listar(self, tenant_id: uuid.UUID) -> list[RascunhoEntrada]:
        stmt = (
            select(RascunhoEntrada)
            .where(RascunhoEntrada.tenant_id == tenant_id)
            .order_by(RascunhoEntrada.criado_em.desc())
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def listar_com_fornecedor(
        self, tenant_id: uuid.UUID
    ) -> list[tuple[RascunhoEntrada, Fornecedor | None]]:
        stmt = (
            select(RascunhoEntrada, Fornecedor)
            .outerjoin(Fornecedor, RascunhoEntrada.fornecedor_id == Fornecedor.id)
            .where(RascunhoEntrada.tenant_id == tenant_id)
            .order_by(RascunhoEntrada.criado_em.desc())
        )
        return [(row[0], row[1]) for row in (await self.db.execute(stmt)).all()]

    async def carregar_itens(self, rascunho_id: uuid.UUID) -> list[ItemRascunhoEntrada]:
        stmt = select(ItemRascunhoEntrada).where(ItemRascunhoEntrada.rascunho_id == rascunho_id)
        return list((await self.db.execute(stmt)).scalars().all())

    async def carregar_itens_com_produto(
        self, rascunho_id: uuid.UUID
    ) -> list[tuple[ItemRascunhoEntrada, Produto | None]]:
        stmt = (
            select(ItemRascunhoEntrada, Produto)
            .outerjoin(Produto, ItemRascunhoEntrada.produto_id == Produto.id)
            .where(ItemRascunhoEntrada.rascunho_id == rascunho_id)
        )
        return [(row[0], row[1]) for row in (await self.db.execute(stmt)).all()]

    # ─── Vincular item ────────────────────────────────────────────────────────

    async def vincular_item(
        self,
        rascunho_id: uuid.UUID,
        item_id: uuid.UUID,
        tenant_id: uuid.UUID,
        payload: VincularItemPayload,
    ) -> ItemRascunhoEntrada:
        rascunho = await self.buscar(rascunho_id, tenant_id)
        if StatusRascunho(rascunho.status) not in _EDITAVEIS:
            raise RascunhoJaConfirmado(f"Rascunho {rascunho_id} já está {rascunho.status}")

        stmt = select(ItemRascunhoEntrada).where(
            ItemRascunhoEntrada.id == item_id,
            ItemRascunhoEntrada.rascunho_id == rascunho_id,
        )
        item = (await self.db.execute(stmt)).scalar_one_or_none()
        if not item:
            raise NaoEncontrado(f"Item {item_id} não encontrado no rascunho {rascunho_id}")

        if payload.acao == "vincular":
            if not payload.produto_id:
                raise NaoEncontrado("produto_id obrigatório para acao=vincular")
            stmt_p = select(Produto).where(
                Produto.id == payload.produto_id, Produto.tenant_id == tenant_id
            )
            if not (await self.db.execute(stmt_p)).scalar_one_or_none():
                raise NaoEncontrado(f"Produto {payload.produto_id} não encontrado")
            item.produto_id = payload.produto_id
            item.status_item = StatusItem.VINCULADO

        else:  # criar_novo
            novo = Produto(
                tenant_id=tenant_id,
                codigo=item.codigo_ref or item.codigo_fornecedor,
                descricao=item.descricao_nfe,
                ncm=item.ncm,
                ean=item.ean,
                marca=payload.marca or None,
                preco_custo=item.preco_unitario,
                preco_venda=item.preco_unitario,
                estoque_atual=Decimal("0"),
                ativo=True,
            )
            self.db.add(novo)
            await self.db.flush()
            item.produto_id = novo.id
            item.status_item = StatusItem.NOVO
            log.info("produto_criado_via_nfe", produto_id=str(novo.id), codigo=novo.codigo)

        await self.db.commit()
        await self.db.refresh(item)
        return item

    # ─── Confirmar ───────────────────────────────────────────────────────────

    async def confirmar(
        self, rascunho_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> EntradaNfe:
        rascunho = await self.buscar(rascunho_id, tenant_id)
        if StatusRascunho(rascunho.status) not in _EDITAVEIS:
            raise RascunhoJaConfirmado(f"Rascunho {rascunho_id} já está {rascunho.status}")

        itens = await self.carregar_itens(rascunho_id)
        pendentes = [i for i in itens if i.status_item == StatusItem.PENDENTE]
        if pendentes:
            raise RascunhoPendente(
                f"{len(pendentes)} item(ns) pendente(s) de vinculação"
            )

        entrada = EntradaNfe(
            tenant_id=tenant_id,
            fornecedor_id=rascunho.fornecedor_id,
            chave_nfe=rascunho.chave_nfe,
            numero_nf=rascunho.numero_nf,
            data_emissao=rascunho.data_emissao,
            valor_total=rascunho.valor_total,
            status=StatusEntradaNfe.ABERTA,
        )
        self.db.add(entrada)
        await self.db.flush()

        estoque_svc = EstoqueService(self.db)
        for item in itens:
            self.db.add(ItemEntrada(
                entrada_id=entrada.id,
                produto_id=item.produto_id,
                codigo_fornecedor=item.codigo_fornecedor,
                quantidade=item.quantidade,
                preco_unitario=item.preco_unitario,
                icms=item.icms,
                ipi=item.ipi,
            ))
            await estoque_svc.registrar_movimentacao(
                item.produto_id, tenant_id,
                TipoMovimentacao.ENTRADA, item.quantidade,
                referencia_id=entrada.id, tipo_ref="ENTRADA",
            )
            if rascunho.fornecedor_id:
                await self._upsert_mapeamento(
                    tenant_id, rascunho.fornecedor_id,
                    item.codigo_fornecedor, item.produto_id,
                )

        rascunho.status = StatusRascunho.CONFIRMADA
        await self.db.commit()
        await self.db.refresh(entrada)
        log.info("rascunho_confirmado", rascunho_id=str(rascunho_id), entrada_id=str(entrada.id))
        return entrada

    # ─── Cancelar ────────────────────────────────────────────────────────────

    async def cancelar(
        self, rascunho_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> RascunhoEntrada:
        rascunho = await self.buscar(rascunho_id, tenant_id)
        if StatusRascunho(rascunho.status) not in _EDITAVEIS:
            raise RascunhoJaConfirmado(f"Rascunho {rascunho_id} já está {rascunho.status}")
        rascunho.status = StatusRascunho.CANCELADA
        await self.db.commit()
        await self.db.refresh(rascunho)
        log.info("rascunho_cancelado", rascunho_id=str(rascunho_id))
        return rascunho

    # ─── Helpers internos ─────────────────────────────────────────────────────

    async def _tentar_match(
        self,
        codigo_fornecedor: str,
        codigo_ref: str | None,
        ean: str | None,
        tenant_id: uuid.UUID,
        fornecedor_id: uuid.UUID | None,
    ) -> tuple[uuid.UUID | None, str]:
        # 1. Mapeamento já aprendido
        if fornecedor_id:
            stmt = select(MapeamentoFornecedorProduto).where(
                MapeamentoFornecedorProduto.tenant_id == tenant_id,
                MapeamentoFornecedorProduto.fornecedor_id == fornecedor_id,
                MapeamentoFornecedorProduto.codigo_fornecedor == codigo_fornecedor,
            )
            m = (await self.db.execute(stmt)).scalar_one_or_none()
            if m:
                return m.produto_id, StatusItem.AUTO_VINCULADO

        # 2. Código de referência extraído da descrição
        if codigo_ref:
            stmt = select(Produto).where(
                Produto.codigo == codigo_ref,
                Produto.tenant_id == tenant_id,
                Produto.ativo.is_(True),
            )
            p = (await self.db.execute(stmt)).scalar_one_or_none()
            if p:
                return p.id, StatusItem.AUTO_VINCULADO

        # 3. EAN
        if ean:
            stmt = select(Produto).where(
                Produto.ean == ean,
                Produto.tenant_id == tenant_id,
                Produto.ativo.is_(True),
            )
            p = (await self.db.execute(stmt)).scalar_one_or_none()
            if p:
                return p.id, StatusItem.AUTO_VINCULADO

        return None, StatusItem.PENDENTE

    async def _upsert_fornecedor(
        self, tenant_id: uuid.UUID, dados: NFeParseResult
    ) -> Fornecedor | None:
        if not dados.emit_cnpj:
            return None
        stmt = select(Fornecedor).where(
            Fornecedor.cnpj == dados.emit_cnpj,
            Fornecedor.tenant_id == tenant_id,
        )
        f = (await self.db.execute(stmt)).scalar_one_or_none()
        if not f:
            f = Fornecedor(
                tenant_id=tenant_id,
                razao_social=dados.emit_nome,
                nome_fantasia=dados.emit_nome_fantasia,
                cnpj=dados.emit_cnpj,
                inscricao_estadual=dados.emit_ie,
                telefone=dados.emit_telefone,
            )
            self.db.add(f)
            await self.db.flush()
        return f

    async def _upsert_mapeamento(
        self,
        tenant_id: uuid.UUID,
        fornecedor_id: uuid.UUID,
        codigo_fornecedor: str,
        produto_id: uuid.UUID,
    ) -> None:
        stmt = (
            pg_insert(MapeamentoFornecedorProduto)
            .values(
                tenant_id=tenant_id,
                fornecedor_id=fornecedor_id,
                codigo_fornecedor=codigo_fornecedor,
                produto_id=produto_id,
            )
            .on_conflict_do_update(
                index_elements=["tenant_id", "fornecedor_id", "codigo_fornecedor"],
                set_={"produto_id": produto_id},
            )
        )
        await self.db.execute(stmt)
