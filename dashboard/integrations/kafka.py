"""Kafka consumer bridge that streams messages into Celery tasks."""

from __future__ import annotations

import json
import logging
import os
import threading
from typing import Iterable

from kafka import KafkaConsumer

from .. import tasks

logger = logging.getLogger(__name__)


def start_kafka_bridge(topics: Iterable[str] | None = None) -> None:
    bootstrap_servers = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    group_id = os.environ.get('KAFKA_GROUP_ID', 'dashboard-consumer')
    topics = list(topics or os.environ.get('KAFKA_TOPICS', 'dashboard-events').split(','))

    consumer = KafkaConsumer(
        *topics,
        bootstrap_servers=bootstrap_servers,
        group_id=group_id,
        value_deserializer=lambda value: json.loads(value.decode('utf-8')),
        auto_offset_reset=os.environ.get('KAFKA_OFFSET_RESET', 'latest'),
        enable_auto_commit=True,
    )

    def _consume():  # pragma: no cover - network loop
        logger.info('Kafka consumer listening on %s for topics %s', bootstrap_servers, topics)
        for message in consumer:
            tasks.ingest_kafka_message.delay(message.topic, message.value)

    thread = threading.Thread(target=_consume, daemon=True)
    thread.start()
    logger.info('Kafka bridge running on thread %s', thread.name)
