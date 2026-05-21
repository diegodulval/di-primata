import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from oficinas.core.enums import StatusOS, TipoItem, TipoMovimentacao
from oficinas.core.exceptions import NaoEncontrado, OSJaFechada, TransicaoInvalida
from oficinas.modules.estoque.service import EstoqueService
from oficinas.modules.ordens_servico.models import ItemOS, OrdemServico
from oficinas.modules.ordens_servico.schemas import FecharOS, ItemOSAdd, OSCreate
from oficinas.shared.veiculo_global.models import HistoricoVeiculo

log = structlog.get_logger()

_EDITAVEIS = {StatusOS.ABERTA, StatusOS.EM_EXECUCAO, StatusOS.AGUARDANDO_PECA}

_TRANSICOES: dict[StatusOS, set[StatusOS]] = {
    StatusOS.ABERTA:          {StatusOS.EM_EXECUCAO, StatusOS.AGUARDANDO_PECA},
    StatusOS.EM_EXECUCAO:     {StatusOS.AGUARDANDO_PECA},
    StatusOS.AGUARDANDO_PECA: {StatusOS.EM_EXECUCAO},
}


def _numero_os() -> str:
    hoje = datetime.now(timezone.utc)
    return f"OS{hoje.strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}"


class OrdensServicoService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def abrir(
        self,
        tenant_id: uuid.UUID,
        mecanico_id: uuid.UUID,
        payload: OSCreate,
    ) -> OrdemServico:
        os = OrdemServico(
            tenant_id=tenant_id,
            mecanico_id=mecanico_id,
            cliente_id=payload.cliente_id,
            veiculo_id=payload.veiculo_id,
            numero_os=_numero_os(),
            km_entrada=payload.km_entrada,
            descricao_problema=payload.descricao_problema,
            status=StatusOS.ABERTA,
        )
        self.db.add(os)
        await self.db.commit()
        await self.db.refresh(os)
        log.info("os_aberta", os_id=str(os.id), tenant_id=str(tenant_id))
        return os

    async def buscar(self, os_id: uuid.UUID, tenant_id: uuid.UUID) -> OrdemServico:
        stmt = select(OrdemServico).where(
            OrdemServico.id == os_id,
            OrdemServico.tenant_id == tenant_id,
        )
        os = (await self.db.execute(stmt)).scalar_one_or_none()
        if not os:
            raise NaoEncontrado(f"OS {os_id} não encontrada")
        return os

    async def listar(
        self,
        tenant_id: uuid.UUID,
        status: StatusOS | None = None,
        mecanico_id: uuid.UUID | None = None,
    ) -> list[OrdemServico]:
        stmt = select(OrdemServico).where(OrdemServico.tenant_id == tenant_id)
        if status:
            stmt = stmt.where(OrdemServico.status == status)
        if mecanico_id:
            stmt = stmt.where(OrdemServico.mecanico_id == mecanico_id)
        stmt = stmt.order_by(OrdemServico.aberta_em.desc())
        return list((await self.db.execute(stmt)).scalars().all())

    async def adicionar_item(
        self,
        os_id: uuid.UUID,
        tenant_id: uuid.UUID,
        payload: ItemOSAdd,
    ) -> ItemOS:
        os = await self.buscar(os_id, tenant_id)
        if StatusOS(os.status) not in _EDITAVEIS:
            raise OSJaFechada(f"OS {os_id} não pode ser editada no status {os.status}")

        subtotal = payload.quantidade * payload.preco_unitario

        if payload.tipo == TipoItem.PECA:
            if not payload.produto_id:
                raise NaoEncontrado("produto_id obrigatório para item do tipo PECA")
            await EstoqueService(self.db).registrar_movimentacao(
                payload.produto_id, tenant_id,
                TipoMovimentacao.RESERVA, payload.quantidade,
                referencia_id=os_id, tipo_ref="OS",
            )
            os.total_pecas = (os.total_pecas or Decimal("0")) + subtotal
        else:
            os.total_servicos = (os.total_servicos or Decimal("0")) + subtotal

        os.total_final = os.total_pecas + os.total_servicos - (os.desconto or Decimal("0"))

        item = ItemOS(
            os_id=os_id,
            produto_id=payload.produto_id,
            tipo=payload.tipo,
            descricao=payload.descricao,
            quantidade=payload.quantidade,
            preco_unitario=payload.preco_unitario,
            subtotal=subtotal,
        )
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        log.info("item_os_adicionado", item_id=str(item.id), os_id=str(os_id), tipo=payload.tipo)
        return item

    async def remover_item(
        self,
        os_id: uuid.UUID,
        item_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> None:
        os = await self.buscar(os_id, tenant_id)
        if StatusOS(os.status) not in _EDITAVEIS:
            raise OSJaFechada(f"OS {os_id} não pode ser editada no status {os.status}")

        stmt = select(ItemOS).where(ItemOS.id == item_id, ItemOS.os_id == os_id)
        item = (await self.db.execute(stmt)).scalar_one_or_none()
        if not item:
            raise NaoEncontrado(f"Item {item_id} não encontrado na OS {os_id}")

        if TipoItem(item.tipo) == TipoItem.PECA and item.produto_id:
            await EstoqueService(self.db).registrar_movimentacao(
                item.produto_id, tenant_id,
                TipoMovimentacao.LIBERACAO, item.quantidade,
                referencia_id=os_id, tipo_ref="OS",
            )
            os.total_pecas = (os.total_pecas or Decimal("0")) - item.subtotal
        else:
            os.total_servicos = (os.total_servicos or Decimal("0")) - item.subtotal

        os.total_final = os.total_pecas + os.total_servicos - (os.desconto or Decimal("0"))

        self.db.delete(item)
        await self.db.commit()
        log.info("item_os_removido", item_id=str(item_id), os_id=str(os_id))

    async def atualizar_status(
        self,
        os_id: uuid.UUID,
        tenant_id: uuid.UUID,
        novo_status: StatusOS,
    ) -> OrdemServico:
        os = await self.buscar(os_id, tenant_id)
        status_atual = StatusOS(os.status)

        if status_atual not in _TRANSICOES:
            raise OSJaFechada(f"OS no status {os.status} não pode ter o status alterado")

        permitidos = _TRANSICOES[status_atual]
        if novo_status not in permitidos:
            raise TransicaoInvalida(
                f"Transição {os.status} → {novo_status} não permitida. "
                f"Permitidos: {', '.join(s.value for s in permitidos)}"
            )

        os.status = novo_status
        await self.db.commit()
        await self.db.refresh(os)
        log.info("os_status_atualizado", os_id=str(os_id), novo_status=novo_status)
        return os

    async def fechar(
        self,
        os_id: uuid.UUID,
        tenant_id: uuid.UUID,
        payload: FecharOS,
    ) -> OrdemServico:
        os = await self.buscar(os_id, tenant_id)
        if StatusOS(os.status) not in _EDITAVEIS:
            raise OSJaFechada(f"OS {os_id} já está {os.status}")

        itens = await self._carregar_itens(os_id)

        for item in itens:
            if TipoItem(item.tipo) == TipoItem.PECA and item.produto_id:
                await EstoqueService(self.db).registrar_movimentacao(
                    item.produto_id, tenant_id,
                    TipoMovimentacao.SAIDA, item.quantidade,
                    referencia_id=os_id, tipo_ref="OS",
                )

        self.db.add(HistoricoVeiculo(
            veiculo_id=os.veiculo_id,
            tenant_id=tenant_id,
            os_id=os_id,
            data_servico=date.today(),
            km_entrada=os.km_entrada,
            resumo_publico=payload.resumo_publico if payload.compartilhar_historico else None,
            detalhe_privado=os.descricao_problema,
        ))

        os.status = StatusOS.FECHADA
        os.compartilhar_historico = payload.compartilhar_historico
        os.fechada_em = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(os)
        log.info("os_fechada", os_id=str(os_id), tenant_id=str(tenant_id))
        return os

    async def cancelar(
        self,
        os_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> OrdemServico:
        os = await self.buscar(os_id, tenant_id)
        if StatusOS(os.status) not in _EDITAVEIS:
            raise OSJaFechada(f"OS {os_id} já está {os.status}")

        itens = await self._carregar_itens(os_id)

        for item in itens:
            if TipoItem(item.tipo) == TipoItem.PECA and item.produto_id:
                await EstoqueService(self.db).registrar_movimentacao(
                    item.produto_id, tenant_id,
                    TipoMovimentacao.LIBERACAO, item.quantidade,
                    referencia_id=os_id, tipo_ref="OS",
                )

        os.status = StatusOS.CANCELADA
        await self.db.commit()
        await self.db.refresh(os)
        log.info("os_cancelada", os_id=str(os_id))
        return os

    async def listar_itens(self, os_id: uuid.UUID, tenant_id: uuid.UUID) -> list[ItemOS]:
        await self.buscar(os_id, tenant_id)
        return await self._carregar_itens(os_id)

    async def _carregar_itens(self, os_id: uuid.UUID) -> list[ItemOS]:
        stmt = select(ItemOS).where(ItemOS.os_id == os_id)
        return list((await self.db.execute(stmt)).scalars().all())
