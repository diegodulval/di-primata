from uuid import UUID

from fastapi import APIRouter, Depends

from auth.jwt import TokenData
from auth.dependencies import get_token
from core.models.event import Event, EventCreate
from producao.repositories.store import Store, get_store
from producao.services.cycle_service import CycleService

router = APIRouter()


@router.post("/{cycle_id}/events", response_model=Event, status_code=201)
def add_event(
    cycle_id: UUID,
    body: EventCreate,
    token: TokenData = Depends(get_token),
    store: Store = Depends(get_store),
):
    svc = CycleService(store)
    return svc.add_event(cycle_id, body, token.user_id)


@router.get("/{cycle_id}/events", response_model=list[Event])
def list_events(
    cycle_id: UUID,
    token: TokenData = Depends(get_token),
    store: Store = Depends(get_store),
):
    svc = CycleService(store)
    return svc.get_events(cycle_id)
