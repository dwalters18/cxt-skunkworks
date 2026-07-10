"""Canonical event consumer helper.

Wraps AIOKafkaConsumer so every consumer in the system (projector, websocket
bridge) parses messages the same way: JSON -> EventEnvelope, with poison-pill
protection (a message that fails to parse is logged and skipped, never crashes
the consumer loop).

metadata_max_age_ms is kept low so consumers re-discover topics quickly after a
demo reset deletes and recreates them.
"""
from __future__ import annotations

import json
import logging
from typing import AsyncIterator, List, Optional, Tuple

from aiokafka import AIOKafkaConsumer
from pydantic import ValidationError

from core.config import KAFKA_BOOTSTRAP_SERVERS
from core.envelope import EventEnvelope

logger = logging.getLogger(__name__)


def build_consumer(
    topics: List[str],
    group_id: Optional[str],
    bootstrap_servers: str = KAFKA_BOOTSTRAP_SERVERS,
    from_beginning: bool = False,
) -> AIOKafkaConsumer:
    """group_id=None means no consumer group: read all partitions, never commit —
    used by the projector so every start is a full replay."""
    return AIOKafkaConsumer(
        *topics,
        bootstrap_servers=bootstrap_servers,
        group_id=group_id,
        value_deserializer=lambda m: m,  # raw bytes; parsed in envelopes()
        key_deserializer=lambda k: k.decode("utf-8") if k else None,
        auto_offset_reset="earliest" if from_beginning else "latest",
        enable_auto_commit=group_id is not None,
        metadata_max_age_ms=5000,
    )


def parse_envelope(raw: bytes) -> Optional[EventEnvelope]:
    """Parse one Kafka message value into an EventEnvelope, or None if malformed."""
    try:
        return EventEnvelope.model_validate(json.loads(raw))
    except (json.JSONDecodeError, UnicodeDecodeError, ValidationError) as e:
        logger.warning("skipping non-canonical message: %s", e)
        return None


async def envelopes(
    consumer: AIOKafkaConsumer,
) -> AsyncIterator[Tuple[str, EventEnvelope]]:
    """Yield (topic, envelope) for every parseable message, skipping bad ones."""
    async for message in consumer:
        envelope = parse_envelope(message.value)
        if envelope is not None:
            yield message.topic, envelope
