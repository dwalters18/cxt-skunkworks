"""Order endpoints — create, list, assign to route, cancel.

An order always has exactly two stops (PICKUP, DELIVERY) and one or more parcels.
Mutations write Postgres and emit canonical events (see services.world).
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from core.config import TENANT_ID
from routers.deps import get_events, get_pg, get_trace_id
from services import world
from services.world import WorldError

router = APIRouter(prefix="/orders", tags=["orders"])


class ApiModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)


class StopInput(ApiModel):
    address: str = Field(min_length=1)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    window_start: Optional[datetime] = None
    window_end: Optional[datetime] = None


class CreateOrderRequest(ApiModel):
    customer_id: str
    pickup: StopInput
    delivery: StopInput
    parcel_count: int = Field(default=1, ge=1, le=20)
    notes: Optional[str] = None


class AssignOrderRequest(ApiModel):
    route_id: str


class CancelOrderRequest(ApiModel):
    reason: Optional[str] = None


def _side(s: StopInput) -> dict:
    return {
        "address": s.address,
        "latitude": s.latitude,
        "longitude": s.longitude,
        "windowStart": s.window_start,
        "windowEnd": s.window_end,
    }


@router.get("")
async def list_orders(
    status: Optional[str] = None,
    unassigned: bool = False,
    limit: int = 100,
    offset: int = 0,
    pg=Depends(get_pg),
):
    try:
        return await world.list_orders(pg, status=status, unassigned=unassigned, limit=limit, offset=offset)
    except WorldError as e:
        raise HTTPException(e.status_code, str(e))


@router.get("/unassigned")
async def unassigned_orders(pg=Depends(get_pg)):
    return await world.list_orders(pg, unassigned=True)


@router.get("/{order_id}")
async def get_order(order_id: str, pg=Depends(get_pg)):
    try:
        return await world.get_order(pg, order_id)
    except WorldError as e:
        raise HTTPException(e.status_code, str(e))


@router.post("", status_code=201)
async def create_order(
    body: CreateOrderRequest,
    pg=Depends(get_pg),
    events=Depends(get_events),
    trace_id=Depends(get_trace_id),
):
    try:
        return await world.create_order(
            pg,
            events,
            tenant_id=TENANT_ID,
            customer_id=body.customer_id,
            pickup=_side(body.pickup),
            delivery=_side(body.delivery),
            parcel_count=body.parcel_count,
            notes=body.notes,
            trace_id=trace_id,
        )
    except WorldError as e:
        raise HTTPException(e.status_code, str(e))


@router.post("/{order_id}/assign")
async def assign_order(
    order_id: str,
    body: AssignOrderRequest,
    pg=Depends(get_pg),
    events=Depends(get_events),
    trace_id=Depends(get_trace_id),
):
    try:
        return await world.assign_order_to_route(pg, events, order_id, body.route_id, trace_id)
    except WorldError as e:
        raise HTTPException(e.status_code, str(e))


@router.post("/{order_id}/cancel")
async def cancel_order(
    order_id: str,
    body: CancelOrderRequest | None = None,
    pg=Depends(get_pg),
    events=Depends(get_events),
    trace_id=Depends(get_trace_id),
):
    try:
        return await world.cancel_order(pg, events, order_id, (body.reason if body else None), trace_id)
    except WorldError as e:
        raise HTTPException(e.status_code, str(e))
