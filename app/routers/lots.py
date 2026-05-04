from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.auth import TokenData
from app.core.deps import get_token
from app.models.lot import Lot
from app.repositories.store import Store, get_store
from app.services.lot_service import LotService

router = APIRouter()


@router.post("/{cycle_id}/lots", response_model=Lot, status_code=201)
def generate_lot(
    cycle_id: UUID,
    token: TokenData = Depends(get_token),
    store: Store = Depends(get_store),
):
    svc = LotService(store)
    return svc.generate(cycle_id, token.user_id)


@router.post("/lots/{lot_id}/publish", response_model=Lot)
def publish_lot(
    lot_id: UUID,
    token: TokenData = Depends(get_token),
    store: Store = Depends(get_store),
):
    svc = LotService(store)
    return svc.publish(lot_id, token.user_id)


@router.get("/lots", response_model=list[Lot])
def list_lots(token: TokenData = Depends(get_token), store: Store = Depends(get_store)):
    cycles = store.cycles.list_by(account_id=token.account_id)
    cycle_ids = {c.id for c in cycles}
    return [lot for lot in store.lots.list_all() if lot.ciclo_id in cycle_ids]
