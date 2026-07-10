"""CDC normalizer — turns raw Debezium change records into canonical events.

Consumes the source-shaped `cdc.raw.public.<table>` topics that Debezium writes
and republishes every row change as a canonical `<entity>.record-created|
updated|deleted` event on `lip.cdc` — through the same validated publisher as
every other producer.

This is the integration-plane pattern in miniature: the raw feed is an inbox,
the canonical envelope is the contract. Even a row edited directly in psql
surfaces on the backbone seconds later as a well-formed event.
"""
from __future__ import annotations

import asyncio
import base64
import json
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, Optional

from aiokafka import AIOKafkaConsumer
from shapely import wkb as shapely_wkb

from core.config import KAFKA_BOOTSTRAP_SERVERS, TENANT_ID
from core.envelope import EntityRef, EntityType, SourceSystem
from eventbus.publisher import EventPublisher, EventValidationError

logger = logging.getLogger(__name__)

CDC_TOPIC_PATTERN = r"^cdc\.raw\.public\..*"

TABLE_TO_ENTITY = {
    "customers": EntityType.CUSTOMER,
    "depots": EntityType.DEPOT,
    "drivers": EntityType.DRIVER,
    "vehicles": EntityType.VEHICLE,
    "routes": EntityType.ROUTE,
    "orders": EntityType.ORDER,
    "stops": EntityType.STOP,
    "parcels": EntityType.PARCEL,
}

OP_TO_ACTION = {"c": "created", "r": "created", "u": "updated", "d": "deleted"}

GEOGRAPHY_COLUMNS = {"location", "current_location"}
EPOCH_DATE_COLUMNS = {"service_date"}  # Debezium encodes DATE as days since epoch


def _decode_geography(value: Any) -> Optional[Dict[str, float]]:
    """Debezium serializes PostGIS geography as {'wkb': base64, 'srid': n}."""
    if value is None:
        return None
    if isinstance(value, dict) and "wkb" in value:
        try:
            point = shapely_wkb.loads(base64.b64decode(value["wkb"]))
            return {"latitude": point.y, "longitude": point.x}
        except Exception as e:
            logger.warning("could not decode geography: %s", e)
            return None
    return value


def _clean_row(row: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if row is None:
        return None
    out: Dict[str, Any] = {}
    for k, v in row.items():
        if k in GEOGRAPHY_COLUMNS:
            out[k] = _decode_geography(v)
        elif k in EPOCH_DATE_COLUMNS and isinstance(v, int):
            out[k] = (date(1970, 1, 1) + timedelta(days=v)).isoformat()
        else:
            out[k] = v
    return out


def _unwrap(value: Dict[str, Any]) -> Dict[str, Any]:
    """Support both converter configs: schemas enabled ({schema, payload}) or plain."""
    if set(value.keys()) == {"schema", "payload"}:
        return value["payload"]
    return value


async def handle_record(publisher: EventPublisher, value: Dict[str, Any]) -> bool:
    change = _unwrap(value)
    op = change.get("op")
    action = OP_TO_ACTION.get(op)
    if action is None:  # heartbeats, truncates, transaction markers
        return False

    source = change.get("source") or {}
    table = source.get("table")
    entity = TABLE_TO_ENTITY.get(table)
    if entity is None:
        logger.debug("ignoring CDC for unmapped table %r", table)
        return False

    before = _clean_row(change.get("before"))
    after = _clean_row(change.get("after"))
    row = after or before
    if not row or "id" not in row:
        return False

    ts_ms = source.get("ts_ms")
    occurred_at = (
        datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
        if ts_ms
        else datetime.now(timezone.utc)
    )
    tenant_id = row.get("tenant_id") or TENANT_ID

    try:
        await publisher.emit(
            f"{entity.value}.record-{action}",
            SourceSystem.CDC_NORMALIZER,
            entity_refs=[EntityRef(type=entity, id=str(row["id"]))],
            payload={
                "table": table,
                "op": action,
                "before": before,
                "after": after,
                "sourceTsMs": ts_ms,
            },
            occurred_at=occurred_at,
        )
        return True
    except EventValidationError as e:
        logger.error("normalizer produced an invalid event (bug): %s %s", e, e.details)
        return False


async def run() -> None:
    publisher = EventPublisher()
    await publisher.start()

    consumer = AIOKafkaConsumer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id="lip-cdc-normalizer",
        value_deserializer=lambda m: m,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        metadata_max_age_ms=5000,
    )
    await consumer.start()
    consumer.subscribe(pattern=CDC_TOPIC_PATTERN)
    logger.info("normalizer consuming %s", CDC_TOPIC_PATTERN)

    emitted = 0
    try:
        async for message in consumer:
            if message.value is None:
                continue
            try:
                value = json.loads(message.value)
            except (json.JSONDecodeError, UnicodeDecodeError):
                logger.warning("skipping undecodable CDC message on %s", message.topic)
                continue
            if not isinstance(value, dict):
                continue
            if await handle_record(publisher, value):
                emitted += 1
                if emitted % 100 == 0:
                    logger.info("normalized %d change records", emitted)
    finally:
        await consumer.stop()
        await publisher.stop()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    while True:
        try:
            asyncio.run(run())
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error("normalizer crashed (%s); restarting in 5s", e)
            import time

            time.sleep(5)


if __name__ == "__main__":
    main()
