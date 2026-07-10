"""Stop endpoints — the atomic units of work. Status flows
PENDING -> ARRIVED -> COMPLETED (or FAILED), with cascades to order and route."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from routers.deps import get_events, get_pg, get_trace_id
from services import world
from services.world import WorldError

router = APIRouter(prefix="/stops", tags=["stops"])


class StopStatusRequest(BaseModel):
    status: str


@router.post("/{stop_id}/status")
async def update_stop_status(
    stop_id: str,
    body: StopStatusRequest,
    pg=Depends(get_pg),
    events=Depends(get_events),
    trace_id=Depends(get_trace_id),
):
    try:
        return await world.update_stop_status(pg, events, stop_id, body.status, trace_id)
    except WorldError as e:
        raise HTTPException(e.status_code, str(e))
