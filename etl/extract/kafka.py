"""
Kafka stream extractor — consumes a batch of messages from a Kafka topic.

Requires: ``pip install kafka-python``
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import json

import pandas as pd
from prefect import task

from infrastructure.logging.logger import get_logger
from etl.config.settings import get_settings

logger = get_logger(__name__)


class KafkaExtractor:
    """
    Consume a batch of messages from a Kafka topic and return them
    as a DataFrame.

    Uses ``kafka-python`` (KafkaConsumer) under the hood.
    """

    def __init__(
        self,
        topic: str,
        bootstrap_servers: Optional[str] = None,
        group_id: Optional[str] = None,
        auto_offset_reset: Optional[str] = None,
    ):
        settings = get_settings().extract.kafka
        self.topic = topic
        self.bootstrap_servers = bootstrap_servers or settings.bootstrap_servers
        self.group_id = group_id or settings.group_id
        self.auto_offset_reset = auto_offset_reset or settings.auto_offset_reset
        self.max_messages = settings.max_messages
        self.poll_timeout_ms = settings.poll_timeout_ms
        self._consumer = None

    def _get_consumer(self):
        """Lazy-init the KafkaConsumer."""
        if self._consumer is None:
            from kafka import KafkaConsumer

            self._consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                auto_offset_reset=self.auto_offset_reset,
                enable_auto_commit=False,
                value_deserializer=lambda v: json.loads(v.decode("utf-8")),
                consumer_timeout_ms=self.poll_timeout_ms,
            )
        return self._consumer

    def validate_connection(self) -> bool:
        """Check that the Kafka broker is reachable."""
        try:
            consumer = self._get_consumer()
            topics = consumer.topics()
            return self.topic in topics
        except Exception as exc:
            logger.error(f"Kafka connection check failed: {exc}")
            return False

    def extract(self) -> tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Consume up to ``max_messages`` from the topic.

        Returns:
            (DataFrame of message values, metadata_dict)
        """
        logger.info(
            f"Consuming from Kafka topic={self.topic}, "
            f"max_messages={self.max_messages}"
        )

        consumer = self._get_consumer()
        records: List[Dict[str, Any]] = []

        for message in consumer:
            records.append(message.value)
            if len(records) >= self.max_messages:
                break

        # Commit offsets after successful batch read
        consumer.commit()

        df = pd.DataFrame(records)

        metadata: Dict[str, Any] = {
            "source_type": "kafka",
            "source_name": f"kafka://{self.bootstrap_servers}/{self.topic}",
            "topic": self.topic,
            "record_count": len(df),
            "extracted_at": datetime.now(timezone.utc).isoformat(),
        }

        logger.info(f"Consumed {len(df)} messages from topic={self.topic}")
        return df, metadata

    def close(self):
        """Close the Kafka consumer."""
        if self._consumer:
            self._consumer.close()
            self._consumer = None


# ── Prefect task wrapper ────────────────────────────────────────────

@task(
    name="extract-from-kafka",
    retries=2,
    retry_delay_seconds=15,
    description="Consume a batch of messages from a Kafka topic.",
)
def extract_from_kafka(
    topic: str,
    bootstrap_servers: Optional[str] = None,
    group_id: Optional[str] = None,
    max_messages: Optional[int] = None,
) -> tuple[pd.DataFrame, Dict[str, Any]]:
    """Prefect task: extract data from a Kafka topic."""
    extractor = KafkaExtractor(
        topic=topic,
        bootstrap_servers=bootstrap_servers,
        group_id=group_id,
    )
    if max_messages is not None:
        extractor.max_messages = max_messages

    try:
        return extractor.extract()
    finally:
        extractor.close()
