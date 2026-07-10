"""Topic audit — prove every event on the canonical backbone conforms to envelope v1.

    make audit            (wraps: docker compose exec api python -m tools.topic_audit)

What it does:
  1. Lists every topic on the broker and classifies it:
       canonical   lip.*                 -> audited, must be 100% envelope v1
       raw CDC     cdc.raw.*, heartbeats -> documented input namespace, not canonical
       infra       __consumer_offsets, debezium bookkeeping, connect internals
       UNEXPECTED  anything else         -> audit FAILS (a producer is off-contract)
  2. Reads every canonical topic from the beginning and validates every single
     message: JSON -> EventEnvelope -> eventType registered in the catalog ->
     payload matches that type's schema.
  3. Prints a per-topic report and exits non-zero on any violation.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import sys
from dataclasses import dataclass, field
from typing import Dict, List

from aiokafka import AIOKafkaConsumer, TopicPartition
from pydantic import ValidationError

from core import catalog
from core.config import KAFKA_BOOTSTRAP_SERVERS
from core.envelope import EventEnvelope

logger = logging.getLogger("topic_audit")

RAW_CDC_PATTERNS = [r"^cdc\.raw\.", r"^__debezium-heartbeat"]
INFRA_PATTERNS = [
    r"^__consumer_offsets$",
    r"^__transaction_state$",
    r"^debezium_(configs|offsets|status(es)?)$",
    r"^connect-",
    r"^_schemas$",
]


@dataclass
class TopicReport:
    topic: str
    messages: int = 0
    valid: int = 0
    errors: List[str] = field(default_factory=list)

    @property
    def invalid(self) -> int:
        return self.messages - self.valid


def classify(topic: str) -> str:
    if topic.startswith("lip."):
        return "canonical"
    if any(re.match(p, topic) for p in RAW_CDC_PATTERNS):
        return "raw-cdc"
    if any(re.match(p, topic) for p in INFRA_PATTERNS):
        return "infra"
    return "unexpected"


def validate_message(raw: bytes, report: TopicReport) -> None:
    report.messages += 1

    def fail(msg: str) -> None:
        if len(report.errors) < 5:
            report.errors.append(msg)

    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        fail(f"not JSON: {e}")
        return
    try:
        envelope = EventEnvelope.model_validate(data)
    except ValidationError as e:
        fail(f"envelope invalid: {e.errors()[:2]}")
        return
    try:
        spec = catalog.spec_for(envelope.event_type)
    except KeyError:
        fail(f"eventType not in catalog: {envelope.event_type}")
        return
    try:
        spec.payload_model.model_validate(envelope.payload)
    except ValidationError as e:
        fail(f"payload invalid for {envelope.event_type}: {e.errors()[:2]}")
        return
    report.valid += 1


async def audit() -> int:
    consumer = AIOKafkaConsumer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=None,
        enable_auto_commit=False,
        auto_offset_reset="earliest",
    )
    await consumer.start()
    try:
        all_topics = sorted(await consumer.topics())
        buckets: Dict[str, List[str]] = {"canonical": [], "raw-cdc": [], "infra": [], "unexpected": []}
        for t in all_topics:
            buckets[classify(t)].append(t)

        print("\n=== TOPIC AUDIT — canonical envelope v1 ===\n")
        print(f"broker topics: {len(all_topics)}")
        print(f"  canonical (audited): {len(buckets['canonical'])}")
        print(f"  raw CDC inbox (envelope-exempt by design): {len(buckets['raw-cdc'])}")
        print(f"  infrastructure: {len(buckets['infra'])}")
        if buckets["unexpected"]:
            print(f"  UNEXPECTED: {buckets['unexpected']}")
        print()

        # One assignment over every canonical partition, read from the beginning
        # to a snapshot of the end offsets, attributing messages per topic.
        reports_by_topic: Dict[str, TopicReport] = {t: TopicReport(t) for t in buckets["canonical"]}
        tps: List[TopicPartition] = []
        for topic in buckets["canonical"]:
            partitions = consumer.partitions_for_topic(topic) or set()
            tps.extend(TopicPartition(topic, p) for p in partitions)
        if tps:
            consumer.assign(tps)
            await consumer.seek_to_beginning(*tps)
            end_offsets = await consumer.end_offsets(tps)
            remaining = {tp: off for tp, off in end_offsets.items() if off > 0}
            idle_rounds = 0
            while remaining and idle_rounds < 3:
                batches = await consumer.getmany(*remaining.keys(), timeout_ms=2000, max_records=1000)
                if not batches:
                    idle_rounds += 1
                    continue
                idle_rounds = 0
                for tp, messages in batches.items():
                    for m in messages:
                        validate_message(m.value, reports_by_topic[tp.topic])
                        if m.offset + 1 >= remaining.get(tp, 0):
                            remaining.pop(tp, None)
        reports: List[TopicReport] = [reports_by_topic[t] for t in buckets["canonical"]]

        width = max((len(r.topic) for r in reports), default=20) + 2
        print(f"{'topic':<{width}} {'messages':>9} {'valid':>7} {'invalid':>8}")
        print("-" * (width + 28))
        for r in reports:
            print(f"{r.topic:<{width}} {r.messages:>9} {r.valid:>7} {r.invalid:>8}")
        total = sum(r.messages for r in reports)
        invalid = sum(r.invalid for r in reports)
        print("-" * (width + 28))
        print(f"{'TOTAL':<{width}} {total:>9} {total - invalid:>7} {invalid:>8}\n")

        failed = invalid > 0 or bool(buckets["unexpected"])
        for r in reports:
            for e in r.errors:
                print(f"  ✗ {r.topic}: {e}")
        if buckets["unexpected"]:
            print(f"  ✗ unexpected topics outside the contract: {buckets['unexpected']}")

        if failed:
            print("\nRESULT: FAIL — the backbone is not fully canonical")
            return 1
        print("RESULT: PASS — every event on every canonical topic conforms to envelope v1")
        print("        (raw CDC namespace is the documented pre-canonical inbox; see EVENT-CATALOG.md)")
        return 0
    finally:
        await consumer.stop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    sys.exit(asyncio.run(audit()))
