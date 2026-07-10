"""Kafka topic administration for the canonical backbone.

Used by the one-shot kafka-init container at startup and by demo reset.
Auto-creation is disabled on the broker, so topics exist only because this
module created them — the topic list is code, not accident.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Iterable, List

from aiokafka.admin import AIOKafkaAdminClient, NewTopic
from aiokafka.errors import KafkaError, TopicAlreadyExistsError, UnknownTopicOrPartitionError

from core.catalog import CANONICAL_TOPICS
from core.config import KAFKA_BOOTSTRAP_SERVERS

logger = logging.getLogger(__name__)

PARTITIONS = 3
REPLICATION = 1


async def _admin() -> AIOKafkaAdminClient:
    client = AIOKafkaAdminClient(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
    await client.start()
    return client


async def create_canonical_topics() -> List[str]:
    """Idempotently create all lip.* topics. Returns the ones newly created."""
    client = await _admin()
    created: List[str] = []
    try:
        existing = set(await client.list_topics())
        missing = [t for t in CANONICAL_TOPICS if t not in existing]
        for topic in missing:
            try:
                await client.create_topics(
                    [NewTopic(name=topic, num_partitions=PARTITIONS, replication_factor=REPLICATION)]
                )
                created.append(topic)
            except TopicAlreadyExistsError:
                pass
        if created:
            logger.info("created topics: %s", created)
        else:
            logger.info("all %d canonical topics already exist", len(CANONICAL_TOPICS))
    finally:
        await client.close()
    return created


async def delete_topics(topics: Iterable[str]) -> None:
    client = await _admin()
    try:
        existing = set(await client.list_topics())
        doomed = [t for t in topics if t in existing]
        if doomed:
            try:
                await client.delete_topics(doomed)
            except UnknownTopicOrPartitionError:
                pass
            logger.info("deleted topics: %s", doomed)
    finally:
        await client.close()


async def list_canonical_topics() -> List[str]:
    """Every topic currently in the canonical (lip.*) namespace."""
    client = await _admin()
    try:
        all_topics = await client.list_topics()
    finally:
        await client.close()
    return sorted(t for t in all_topics if t.startswith("lip."))


async def reset_canonical_topics() -> None:
    """Delete and recreate the canonical (lip.*) namespace.

    The raw CDC inbox (cdc.raw.*) is deliberately left alone: deleting a live
    Debezium connector's topics wedges its producer. The inbox is source
    material, not canonical state — the canonical backbone is what resets.
    """
    doomed = await list_canonical_topics()
    await delete_topics(doomed)

    # Topic deletion is asynchronous on the broker; poll until the namespace is gone.
    for _ in range(30):
        remaining = await list_canonical_topics()
        if not remaining:
            break
        await asyncio.sleep(1)

    # Give the controller a beat, then recreate. Retries cover the window where
    # a deleted topic name is still being cleaned up.
    for attempt in range(10):
        try:
            await create_canonical_topics()
            return
        except KafkaError as e:
            logger.warning("topic recreate attempt %d failed: %s", attempt + 1, e)
            await asyncio.sleep(2)
    raise RuntimeError("could not recreate canonical topics after reset")
