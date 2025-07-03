"""Flink job: AuditAnomalyJob

Consumes Debezium CDC topics (tms.cdc.*) focusing on audit logs,
performs simple rule-based anomaly detection, and writes results to
Kafka (tms.anomalies) and back to PostgreSQL audit_logs (via JDBC sink).

This is a placeholder implementation illustrating the intended data-flow.
Replace rule logic with ML model inference in Phase-2.
"""

from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.connectors import FlinkKafkaConsumer, FlinkKafkaProducer
from pyflink.common.serialization import SimpleStringSchema
import json

# ---------------------------------------------------------------------------
# Configuration (would normally be externalised via CLI args / env vars)
# ---------------------------------------------------------------------------
KAFKA_BOOTSTRAP_SERVERS = "kafka:29092"
INPUT_TOPIC = "tms.cdc.audit_logs"
OUTPUT_TOPIC = "tms.anomalies"


# ---------------------------------------------------------------------------
# Simple rule: if the same user_id generates > R actions within WINDOW seconds
# ---------------------------------------------------------------------------
RATE_THRESHOLD = 10  # actions
WINDOW_SEC = 60


def detect_anomaly(records):
    """Very naive, stateful rate check (placeholder)."""
    from collections import defaultdict
    counts = defaultdict(int)
    anomalies = []
    for rec in records:
        user = rec.get("user_id") or "unknown"
        counts[user] += 1
    for user, cnt in counts.items():
        if cnt > RATE_THRESHOLD:
            anomalies.append({
                "type": "ANOMALY_SUSPECTED",
                "user_id": user,
                "count": cnt
            })
    return anomalies


def main():
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(1)

    consumer = FlinkKafkaConsumer(
        topics=INPUT_TOPIC,
        deserialization_schema=SimpleStringSchema(),
        properties={"bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS}
    )

    producer = FlinkKafkaProducer(
        topic=OUTPUT_TOPIC,
        serialization_schema=SimpleStringSchema(),
        producer_config={"bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS}
    )

    stream = env.add_source(consumer).map(lambda s: json.loads(s))

    # Key by user_id and count within time window – extremely simplified
    from pyflink.datastream import TimeCharacteristic
    from pyflink.common import Time

    env.set_stream_time_characteristic(TimeCharacteristic.ProcessingTime)

    anomalies = (
        stream
        .time_window_all(Time.seconds(WINDOW_SEC))
        .apply(lambda _, it, collector: [collector.collect(json.dumps(a)) for a in detect_anomaly(list(it))])
    )

    anomalies.add_sink(producer)

    env.execute("AuditAnomalyJob")


if __name__ == "__main__":
    main()
