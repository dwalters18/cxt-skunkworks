"""One-shot topic creation — runs as the kafka-init container.

Waits for the broker, then idempotently creates every canonical topic.
Auto-creation is disabled on the broker, so this is the only place canonical
topics come from (Debezium creates its own cdc.raw.* via topic.creation.*).
"""
from __future__ import annotations

import asyncio
import logging
import sys

from eventbus.admin import create_canonical_topics

logger = logging.getLogger("create_topics")


async def main() -> int:
    delay = 2.0
    for attempt in range(15):
        try:
            await create_canonical_topics()
            logger.info("canonical topics ready")
            return 0
        except Exception as e:
            logger.warning("kafka not ready (%s); retrying in %.0fs", e, delay)
            await asyncio.sleep(delay)
            delay = min(delay * 1.5, 10)
    logger.error("gave up waiting for kafka")
    return 1


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    sys.exit(asyncio.run(main()))
