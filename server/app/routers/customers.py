"""Customer and depot read endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from routers.deps import get_pg
from services import world

router = APIRouter(tags=["customers"])


@router.get("/customers")
async def list_customers(pg=Depends(get_pg)):
    return {"customers": await world.list_customers(pg)}


@router.get("/depots")
async def list_depots(pg=Depends(get_pg)):
    return {"depots": await world.list_depots(pg)}
