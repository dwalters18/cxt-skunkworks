"""Route endpoints — a route is a driver's ordered sequence of stops for a day."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from core.config import TENANT_ID
from routers.deps import get_events, get_pg, get_trace_id
from services import world
from services.world import WorldError

router = APIRouter(prefix="/routes", tags=["routes"])


class CreateRouteRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    driver_id: Optional[str] = None
    vehicle_id: Optional[str] = None


@router.get("")
async def list_routes(status: Optional[str] = None, pg=Depends(get_pg)):
    try:
        return {"routes": await world.list_routes(pg, status=status)}
    except WorldError as e:
        raise HTTPException(e.status_code, str(e))


@router.get("/{route_id}")
async def get_route(route_id: str, pg=Depends(get_pg)):
    try:
        return await world.get_route(pg, route_id)
    except WorldError as e:
        raise HTTPException(e.status_code, str(e))


@router.post("", status_code=201)
async def create_route(
    body: CreateRouteRequest,
    pg=Depends(get_pg),
    events=Depends(get_events),
    trace_id=Depends(get_trace_id),
):
    try:
        return await world.create_route(
            pg, events, TENANT_ID, driver_id=body.driver_id, vehicle_id=body.vehicle_id, trace_id=trace_id
        )
    except WorldError as e:
        raise HTTPException(e.status_code, str(e))


@router.post("/{route_id}/start")
async def start_route(
    route_id: str,
    pg=Depends(get_pg),
    events=Depends(get_events),
    trace_id=Depends(get_trace_id),
):
    try:
        return await world.start_route(pg, events, route_id, trace_id)
    except WorldError as e:
        raise HTTPException(e.status_code, str(e))
