from core.models.account import Account
from core.models.audit import AuditLog
from core.models.cycle import Cycle
from core.models.event import Event
from core.models.insumo import CicloInsumo, Insumo
from core.models.kb import KbItem
from core.models.lot import Certification, Lot, LotAsset, QrAccess
from core.models.primata import PrimataSessao
from core.models.protocol import Protocol
from core.models.unit import Unit
from core.models.user import Profile, User
from core.models.whatsapp import WhatsappMensagem, WhatsappSessao
from core.repositories.base import InMemoryRepository


class Store:
    def __init__(self) -> None:
        self.accounts: InMemoryRepository[Account] = InMemoryRepository()
        self.users: InMemoryRepository[User] = InMemoryRepository()
        self.profiles: InMemoryRepository[Profile] = InMemoryRepository()
        self.units: InMemoryRepository[Unit] = InMemoryRepository()
        self.protocols: InMemoryRepository[Protocol] = InMemoryRepository()
        self.cycles: InMemoryRepository[Cycle] = InMemoryRepository()
        self.events: InMemoryRepository[Event] = InMemoryRepository()
        self.lots: InMemoryRepository[Lot] = InMemoryRepository()
        self.lot_assets: InMemoryRepository[LotAsset] = InMemoryRepository()
        self.certifications: InMemoryRepository[Certification] = InMemoryRepository()
        self.qr_accesses: InMemoryRepository[QrAccess] = InMemoryRepository()
        self.insumos: InMemoryRepository[Insumo] = InMemoryRepository()
        self.ciclo_insumos: InMemoryRepository[CicloInsumo] = InMemoryRepository()  # type: ignore
        self.kb_items: InMemoryRepository[KbItem] = InMemoryRepository()
        self.primata_sessoes: InMemoryRepository[PrimataSessao] = InMemoryRepository()
        self.audit_logs: InMemoryRepository[AuditLog] = InMemoryRepository()
        self.whatsapp_sessoes: InMemoryRepository[WhatsappSessao] = InMemoryRepository()
        self.whatsapp_mensagens: InMemoryRepository[WhatsappMensagem] = InMemoryRepository()
        self._lot_seq: dict[str, int] = {}

    def next_lot_seq(self, key: str) -> int:
        self._lot_seq[key] = self._lot_seq.get(key, 0) + 1
        return self._lot_seq[key]


store = Store()


def get_store() -> Store:
    return store
