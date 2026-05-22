import uuid
from datetime import datetime, timezone
from decimal import Decimal

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from oficinas.core.enums import OrigemVenda, TipoMovimentacao
from oficinas.core.exceptions import NaoEncontrado
from oficinas.modules.estoque.service import EstoqueService
from oficinas.modules.vendas.models import ItemVenda, Venda
from oficinas.modules.vendas.schemas import VendaCreate

log = structlog.get_logger()


def _numero_venda() -> str:
    hoje = datetime.now(timezone.utc)
    return f"VDA{hoje.strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}"


class VendasService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def criar(
        self,
        tenant_id: uuid.UUID,
        usuario_id: uuid.UUID,
        payload: VendaCreate,
    ) -> Venda:
        total = sum(i.quantidade * i.preco_unitario for i in payload.itens)

        venda = Venda(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            cliente_id=payload.cliente_id,
            numero_venda=_numero_venda(),
            origem=OrigemVenda.BALCAO,
            total=total,
            status="CONCLUIDA",
        )
        self.db.add(venda)
        await self.db.flush()

        estoque = EstoqueService(self.db)
        for item_in in payload.itens:
            subtotal = item_in.quantidade * item_in.preco_unitario
            self.db.add(ItemVenda(
                venda_id=venda.id,
                produto_id=item_in.produto_id,
                quantidade=item_in.quantidade,
                preco_unitario=item_in.preco_unitario,
                subtotal=subtotal,
            ))
            # RESERVA baixa o estoque; SAIDA é o registro contábil da saída definitiva
            await estoque.registrar_movimentacao(
                item_in.produto_id, tenant_id,
                TipoMovimentacao.RESERVA, item_in.quantidade,
                referencia_id=venda.id, tipo_ref="VENDA",
            )
            await estoque.registrar_movimentacao(
                item_in.produto_id, tenant_id,
                TipoMovimentacao.SAIDA, item_in.quantidade,
                referencia_id=venda.id, tipo_ref="VENDA",
            )

        await self.db.commit()
        await self.db.refresh(venda)
        log.info("venda_criada", venda_id=str(venda.id), total=str(total), itens=len(payload.itens))
        return venda

    async def buscar(self, venda_id: uuid.UUID, tenant_id: uuid.UUID) -> Venda:
        stmt = select(Venda).where(Venda.id == venda_id, Venda.tenant_id == tenant_id)
        v = (await self.db.execute(stmt)).scalar_one_or_none()
        if not v:
            raise NaoEncontrado(f"Venda {venda_id} não encontrada")
        return v

    async def listar(self, tenant_id: uuid.UUID) -> list[Venda]:
        stmt = (
            select(Venda)
            .where(Venda.tenant_id == tenant_id)
            .order_by(Venda.criado_em.desc())
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def listar_itens(self, venda_id: uuid.UUID) -> list[ItemVenda]:
        stmt = select(ItemVenda).where(ItemVenda.venda_id == venda_id)
        return list((await self.db.execute(stmt)).scalars().all())
