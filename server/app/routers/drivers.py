"""Driver endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from routers.deps import get_events, get_pg, get_trace_id
from services import world
from services.world import WorldError

router = APIRouter(prefix="/drivers", tags=["drivers"])


class DriverStatusRequest(BaseModel):
    status: str


@router.get("")
async def list_drivers(pg=Depends(get_pg)):
    return {"drivers": await world.list_drivers(pg)}


@router.patch("/{driver_id}/status")
async def update_driver_status(
    driver_id: str,
    body: DriverStatusRequest,
    pg=Depends(get_pg),
    events=Depends(get_events),
    trace_id=Depends(get_trace_id),
):
    try:
        return await world.update_driver_status(pg, events, driver_id, body.status, trace_id)
    except WorldError as e:
        raise HTTPException(e.status_code, str(e))
