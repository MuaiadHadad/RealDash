"""Starts MQTT and Kafka bridges for real-time ingestion."""

from __future__ import annotations

import logging
import time

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Start MQTT and Kafka bridges that forward messages into Celery tasks.'

    def add_arguments(self, parser):  # pragma: no cover - argument wiring
        parser.add_argument('--skip-mqtt', action='store_true', help='Do not start the MQTT bridge')
        parser.add_argument('--skip-kafka', action='store_true', help='Do not start the Kafka bridge')

    def handle(self, *args, **options):
        skip_mqtt = options['skip_mqtt']
        skip_kafka = options['skip_kafka']

        if not skip_mqtt:
            self.stdout.write(self.style.NOTICE('Starting MQTT bridge...'))
            try:
                from ...integrations.mqtt import start_mqtt_bridge
            except ImportError as exc:
                logger.exception('MQTT dependencies missing: %s', exc)
                self.stdout.write(self.style.ERROR('paho-mqtt is not installed. Skipping MQTT bridge.'))
            else:
                start_mqtt_bridge()
        else:
            self.stdout.write('MQTT bridge skipped by flag.')

        if not skip_kafka:
            self.stdout.write(self.style.NOTICE('Starting Kafka bridge...'))
            try:
                from ...integrations.kafka import start_kafka_bridge
            except ImportError as exc:
                logger.exception('Kafka dependencies missing: %s', exc)
                self.stdout.write(self.style.ERROR('kafka-python is not installed. Skipping Kafka bridge.'))
            else:
                start_kafka_bridge()
        else:
            self.stdout.write('Kafka bridge skipped by flag.')

        self.stdout.write(self.style.SUCCESS('Bridges launched. Press Ctrl+C to stop.'))
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:  # pragma: no cover - manual exit
            self.stdout.write(self.style.WARNING('Stopping bridges.'))
