"""Vehicle endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from routers.deps import get_events, get_pg, get_trace_id
from services import world
from services.world import WorldError

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


class VehicleStatusRequest(BaseModel):
    status: str


@router.get("")
async def list_vehicles(pg=Depends(get_pg)):
    return {"vehicles": await world.list_vehicles(pg)}


@router.patch("/{vehicle_id}/status")
async def update_vehicle_status(
    vehicle_id: str,
    body: VehicleStatusRequest,
    pg=Depends(get_pg),
    events=Depends(get_events),
    trace_id=Depends(get_trace_id),
):
    try:
        return await world.update_vehicle_status(pg, events, vehicle_id, body.status, trace_id)
    except WorldError as e:
        raise HTTPException(e.status_code, str(e))
