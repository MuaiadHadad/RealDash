"""Utility bridge that streams MQTT messages into the dashboard workflow."""

from __future__ import annotations

import logging
import os
import threading
from typing import Iterable

import paho.mqtt.client as mqtt

from .. import tasks

logger = logging.getLogger(__name__)


def _on_connect(client: mqtt.Client, userdata, flags, rc):  # pragma: no cover - network callback
    if rc != 0:
        logger.error('MQTT connection failed with code %s', rc)
        return
    topics: Iterable[str] = userdata.get('topics', [])
    for topic in topics:
        client.subscribe(topic)
        logger.info('Subscribed to topic %s', topic)


def _on_message(client: mqtt.Client, userdata, msg: mqtt.MQTTMessage):  # pragma: no cover - network callback
    payload = msg.payload.decode('utf-8') if isinstance(msg.payload, (bytes, bytearray)) else msg.payload
    tasks.ingest_mqtt_message.delay(msg.topic, payload)


def start_mqtt_bridge(topics: Iterable[str] | None = None) -> None:
    """Start an MQTT consumer in a daemon thread."""

    host = os.environ.get('MQTT_HOST', '127.0.0.1')
    port = int(os.environ.get('MQTT_PORT', '1883'))
    topics = list(topics or os.environ.get('MQTT_TOPICS', 'sensors/temperature').split(','))

    client = mqtt.Client()
    client.user_data_set({'topics': topics})
    client.on_connect = _on_connect
    client.on_message = _on_message

    username = os.environ.get('MQTT_USERNAME')
    password = os.environ.get('MQTT_PASSWORD')
    if username and password:
        client.username_pw_set(username, password)

    logger.info('Connecting to MQTT broker %s:%s', host, port)
    client.connect(host, port)

    thread = threading.Thread(target=client.loop_forever, daemon=True)
    thread.start()
    logger.info('MQTT bridge running on thread %s', thread.name)
