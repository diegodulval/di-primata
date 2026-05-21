import uuid
from datetime import date

import structlog
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from oficinas.core.exceptions import NaoEncontrado
from oficinas.modules.cadastros.models import Cliente, ClienteVeiculo
from oficinas.modules.cadastros.schemas import ClienteCreate, ClienteUpdate

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

    async def listar_clientes(self, tenant_id: uuid.UUID) -> list[Cliente]:
        stmt = (
            select(Cliente)
            .where(Cliente.tenant_id == tenant_id)
            .order_by(Cliente.nome)
        )
        return list((await self.db.execute(stmt)).scalars().all())

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
        for campo, valor in payload.model_dump(exclude_none=True).items():
            setattr(cliente, campo, valor)
        await self.db.commit()
        await self.db.refresh(cliente)
        log.info("cliente_atualizado", cliente_id=str(cliente_id))
        return cliente

    async def buscar_por_q(self, q: str, tenant_id: uuid.UUID) -> list[Cliente]:
        """Busca por nome (case-insensitive), CPF/CNPJ ou telefone. Máx 20 resultados."""
        pattern = f"%{q}%"
        stmt = (
            select(Cliente)
            .where(
                Cliente.tenant_id == tenant_id,
                or_(
                    Cliente.nome.ilike(pattern),
                    Cliente.cpf_cnpj.ilike(pattern),
                    Cliente.telefone.ilike(pattern),
                ),
            )
            .order_by(Cliente.nome)
            .limit(20)
        )
        return list((await self.db.execute(stmt)).scalars().all())

    # ─── Vínculo cliente-veículo ───────────────────────────────────────────────

    async def vincular_veiculo(
        self,
        cliente_id: uuid.UUID,
        veiculo_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> ClienteVeiculo:
        await self.buscar_cliente(cliente_id, tenant_id)

        # Verifica se há link ativo para este veículo no tenant
        stmt = select(ClienteVeiculo).where(
            ClienteVeiculo.veiculo_id == veiculo_id,
            ClienteVeiculo.tenant_id == tenant_id,
            ClienteVeiculo.ativo.is_(True),
        )
        link_ativo = (await self.db.execute(stmt)).scalar_one_or_none()

        if link_ativo:
            if link_ativo.cliente_id == cliente_id:
                return link_ativo  # idempotente — mesmo cliente
            # Troca de dono: fecha link anterior
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
    ) -> list[ClienteVeiculo]:
        await self.buscar_cliente(cliente_id, tenant_id)
        stmt = (
            select(ClienteVeiculo)
            .where(
                ClienteVeiculo.cliente_id == cliente_id,
                ClienteVeiculo.tenant_id == tenant_id,
            )
            .order_by(ClienteVeiculo.data_inicio.desc())
        )
        return list((await self.db.execute(stmt)).scalars().all())

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
