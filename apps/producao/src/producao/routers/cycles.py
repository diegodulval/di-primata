from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth.jwt import TokenData
from auth.dependencies import get_token
from core.models.cycle import Cycle, CycleCreate
from core.models.enums import StatusCiclo
from producao.repositories.store import Store, get_store
from producao.services.cycle_service import CycleService

router = APIRouter()


class TransitionRequest(BaseModel):
    status: StatusCiclo


@router.post("", response_model=Cycle, status_code=201)
def create_cycle(
    body: CycleCreate,
    token: TokenData = Depends(get_token),
    store: Store = Depends(get_store),
):
    svc = CycleService(store)
    return svc.create(token.account_id, body, token.user_id)


@router.get("", response_model=list[Cycle])
def list_cycles(token: TokenData = Depends(get_token), store: Store = Depends(get_store)):
    return store.cycles.list_by(account_id=token.account_id)


@router.get("/{cycle_id}", response_model=Cycle)
def get_cycle(cycle_id: UUID, token: TokenData = Depends(get_token), store: Store = Depends(get_store)):
    cycle = store.cycles.get(cycle_id)
    if not cycle or cycle.account_id != token.account_id:
        raise HTTPException(status_code=404, detail="Ciclo não encontrado")
    return cycle


@router.patch("/{cycle_id}/status", response_model=Cycle)
def transition_cycle(
    cycle_id: UUID,
    body: TransitionRequest,
    token: TokenData = Depends(get_token),
    store: Store = Depends(get_store),
):
    svc = CycleService(store)
    return svc.transition(cycle_id, body.status, token.user_id)


@router.get("/{cycle_id}/missing-steps")
def missing_steps(
    cycle_id: UUID,
    token: TokenData = Depends(get_token),
    store: Store = Depends(get_store),
):
    svc = CycleService(store)
    return {"missing": svc.missing_steps(cycle_id)}
