import uuid
from decimal import Decimal

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from oficinas.core.enums import TipoMovimentacao
from oficinas.core.exceptions import EstoqueInsuficiente, NaoEncontrado, NFeJaImportada
from oficinas.modules.estoque.models import (
    EntradaNfe,
    Fornecedor,
    ItemEntrada,
    MovimentacaoEstoque,
    Produto,
)
from oficinas.modules.estoque.parser import NFeParseResult, parse_nfe
from oficinas.modules.estoque.schemas import (
    FornecedorCreate,
    ProdutoCreate,
    ProdutoUpdate,
)

log = structlog.get_logger()

# Movimentações que aumentam o estoque físico disponível
_AUMENTAM = {TipoMovimentacao.ENTRADA, TipoMovimentacao.LIBERACAO}
# SAIDA é apenas registro contábil — o estoque já foi reduzido pela RESERVA
_SEM_EFEITO = {TipoMovimentacao.SAIDA}


class EstoqueService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ─── Fornecedor ───────────────────────────────────────────────────────────

    async def criar_fornecedor(self, tenant_id: uuid.UUID, payload: FornecedorCreate) -> Fornecedor:
        f = Fornecedor(tenant_id=tenant_id, **payload.model_dump())
        self.db.add(f)
        await self.db.commit()
        await self.db.refresh(f)
        log.info("fornecedor_criado", fornecedor_id=str(f.id))
        return f

    async def listar_fornecedores(self, tenant_id: uuid.UUID) -> list[Fornecedor]:
        stmt = select(Fornecedor).where(Fornecedor.tenant_id == tenant_id).order_by(Fornecedor.razao_social)
        return list((await self.db.execute(stmt)).scalars().all())

    async def buscar_fornecedor(self, fornecedor_id: uuid.UUID, tenant_id: uuid.UUID) -> Fornecedor:
        stmt = select(Fornecedor).where(Fornecedor.id == fornecedor_id, Fornecedor.tenant_id == tenant_id)
        f = (await self.db.execute(stmt)).scalar_one_or_none()
        if not f:
            raise NaoEncontrado(f"Fornecedor {fornecedor_id} não encontrado")
        return f

    # ─── Produto ──────────────────────────────────────────────────────────────

    async def criar_produto(self, tenant_id: uuid.UUID, payload: ProdutoCreate) -> Produto:
        p = Produto(tenant_id=tenant_id, estoque_atual=Decimal("0"), **payload.model_dump())
        self.db.add(p)
        await self.db.commit()
        await self.db.refresh(p)
        log.info("produto_criado", produto_id=str(p.id), codigo=p.codigo)
        return p

    async def listar_produtos(self, tenant_id: uuid.UUID, q: str | None = None) -> list[Produto]:
        stmt = select(Produto).where(Produto.tenant_id == tenant_id, Produto.ativo.is_(True))
        if q:
            pattern = f"%{q}%"
            from sqlalchemy import or_
            stmt = stmt.where(or_(Produto.descricao.ilike(pattern), Produto.codigo.ilike(pattern)))
        stmt = stmt.order_by(Produto.descricao)
        return list((await self.db.execute(stmt)).scalars().all())

    async def buscar_produto(self, produto_id: uuid.UUID, tenant_id: uuid.UUID) -> Produto:
        stmt = select(Produto).where(Produto.id == produto_id, Produto.tenant_id == tenant_id)
        p = (await self.db.execute(stmt)).scalar_one_or_none()
        if not p:
            raise NaoEncontrado(f"Produto {produto_id} não encontrado")
        return p

    async def atualizar_produto(
        self, produto_id: uuid.UUID, tenant_id: uuid.UUID, payload: ProdutoUpdate
    ) -> Produto:
        p = await self.buscar_produto(produto_id, tenant_id)
        for campo, valor in payload.model_dump(exclude_none=True).items():
            setattr(p, campo, valor)
        await self.db.commit()
        await self.db.refresh(p)
        return p

    # ─── Movimentação ─────────────────────────────────────────────────────────

    async def registrar_movimentacao(
        self,
        produto_id: uuid.UUID,
        tenant_id: uuid.UUID,
        tipo_mov: TipoMovimentacao,
        quantidade: Decimal,
        referencia_id: uuid.UUID | None = None,
        tipo_ref: str | None = None,
    ) -> MovimentacaoEstoque:
        """
        Registra uma movimentação e atualiza estoque_atual do produto.
        NÃO faz commit — o chamador é responsável pelo commit.

        ENTRADA / LIBERACAO  → estoque sobe
        RESERVA              → estoque desce (levanta EstoqueInsuficiente se saldo < 0)
        SAIDA                → apenas registro contábil; estoque não muda
                               (já foi reduzido pela RESERVA ao abrir o item na OS)
        """
        produto = await self.buscar_produto(produto_id, tenant_id)
        anterior = produto.estoque_atual

        if tipo_mov in _AUMENTAM:
            novo = anterior + quantidade
        elif tipo_mov in _SEM_EFEITO:
            novo = anterior
        else:  # RESERVA
            novo = anterior - quantidade
            if novo < 0:
                raise EstoqueInsuficiente(
                    f"Estoque insuficiente para '{produto.descricao}': "
                    f"disponível={anterior}, solicitado={quantidade}"
                )

        produto.estoque_atual = novo

        mov = MovimentacaoEstoque(
            tenant_id=tenant_id,
            produto_id=produto_id,
            referencia_id=referencia_id,
            tipo_ref=tipo_ref,
            tipo_mov=tipo_mov,
            quantidade=quantidade,
            estoque_anterior=anterior,
            estoque_novo=novo,
        )
        self.db.add(mov)
        log.info(
            "movimentacao_registrada",
            tipo=tipo_mov,
            produto_id=str(produto_id),
            anterior=str(anterior),
            novo=str(novo),
        )
        return mov

    async def listar_movimentacoes(
        self, produto_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> list[MovimentacaoEstoque]:
        stmt = (
            select(MovimentacaoEstoque)
            .where(
                MovimentacaoEstoque.produto_id == produto_id,
                MovimentacaoEstoque.tenant_id == tenant_id,
            )
            .order_by(MovimentacaoEstoque.criado_em.desc())
        )
        return list((await self.db.execute(stmt)).scalars().all())

    # ─── NF-e de entrada ──────────────────────────────────────────────────────

    async def processar_entrada_xml(
        self, xml_bytes: bytes, tenant_id: uuid.UUID
    ) -> EntradaNfe:
        dados = parse_nfe(xml_bytes)  # levanta ValueError se XML inválido

        # Idempotência: chave única garante que a mesma NF-e não entre duas vezes
        if dados.chave:
            stmt = select(EntradaNfe).where(EntradaNfe.chave_nfe == dados.chave)
            if (await self.db.execute(stmt)).scalar_one_or_none():
                raise NFeJaImportada(f"NF-e {dados.chave} já importada")

        fornecedor = await self._upsert_fornecedor(tenant_id, dados)

        entrada = EntradaNfe(
            tenant_id=tenant_id,
            fornecedor_id=fornecedor.id if fornecedor else None,
            chave_nfe=dados.chave or None,
            numero_nf=dados.numero or None,
            data_emissao=dados.data_emissao or None,
            valor_total=dados.valor_total,
        )
        self.db.add(entrada)
        await self.db.flush()  # garante entrada.id antes de criar os itens

        for item_nfe in dados.itens:
            produto = await self._upsert_produto(tenant_id, item_nfe)

            self.db.add(ItemEntrada(
                entrada_id=entrada.id,
                produto_id=produto.id,
                codigo_fornecedor=item_nfe.codigo,
                quantidade=item_nfe.quantidade,
                preco_unitario=item_nfe.preco_unitario,
                icms=item_nfe.icms,
                ipi=item_nfe.ipi,
            ))

            await self.registrar_movimentacao(
                produto.id, tenant_id,
                TipoMovimentacao.ENTRADA, item_nfe.quantidade,
                referencia_id=entrada.id, tipo_ref="ENTRADA",
            )

        await self.db.commit()
        await self.db.refresh(entrada)
        log.info("nfe_importada", chave=dados.chave, tenant_id=str(tenant_id), itens=len(dados.itens))
        return entrada

    # ─── Helpers internos ─────────────────────────────────────────────────────

    async def _upsert_fornecedor(self, tenant_id: uuid.UUID, dados: NFeParseResult) -> Fornecedor | None:
        if not dados.emit_cnpj:
            return None
        stmt = select(Fornecedor).where(
            Fornecedor.cnpj == dados.emit_cnpj,
            Fornecedor.tenant_id == tenant_id,
        )
        f = (await self.db.execute(stmt)).scalar_one_or_none()
        if not f:
            f = Fornecedor(tenant_id=tenant_id, razao_social=dados.emit_nome, cnpj=dados.emit_cnpj)
            self.db.add(f)
            await self.db.flush()
        return f

    async def _upsert_produto(self, tenant_id: uuid.UUID, item) -> Produto:
        stmt = select(Produto).where(
            Produto.codigo == item.codigo,
            Produto.tenant_id == tenant_id,
        )
        p = (await self.db.execute(stmt)).scalar_one_or_none()
        if p:
            p.preco_custo = item.preco_unitario  # atualiza preço de custo
            return p
        p = Produto(
            tenant_id=tenant_id,
            codigo=item.codigo,
            descricao=item.descricao,
            ncm=item.ncm or None,
            preco_custo=item.preco_unitario,
            preco_venda=item.preco_unitario,  # admin ajusta depois
            estoque_atual=Decimal("0"),
            ativo=True,
        )
        self.db.add(p)
        await self.db.flush()
        return p
