"""Celery tasks for acquiring data and pushing real-time updates."""

from __future__ import annotations

import json
import os
from decimal import Decimal
from typing import Any, Dict, Iterable, Optional

import requests
from celery import shared_task
from celery.utils.log import get_task_logger

from . import models

logger = get_task_logger(__name__)


def persist_event(model_cls, *, payload: Dict[str, Any]) -> None:
    model_cls.objects.create(**payload)


def _get_json(url: str, params: Optional[Dict[str, Any]] = None, timeout: int = 10) -> Dict[str, Any]:
    response = requests.get(url, params=params, timeout=timeout)
    response.raise_for_status()
    return response.json()


@shared_task(bind=True, autoretry_for=(requests.RequestException,), retry_backoff=True, retry_kwargs={'max_retries': 5})
def fetch_weather(self, location: str = 'Sao Paulo,BR') -> None:
    api_key = os.environ.get('OPENWEATHER_API_KEY')
    if not api_key:
        logger.warning('OPENWEATHER_API_KEY not configured; skipping weather fetch')
        return

    params = {'q': location, 'appid': api_key, 'units': 'metric'}
    try:
        data = _get_json('https://api.openweathermap.org/data/2.5/weather', params)
    except requests.RequestException as exc:
        logger.exception('Weather request failed: %s', exc)
        raise

    payload = {
        'location': location,
        'payload': data,
    }
    persist_event(models.WeatherSnapshot, payload=payload)


@shared_task(bind=True)
def fetch_finance_quotes(self, symbols: Iterable[str] | None = None) -> None:
    symbols = list(symbols or os.environ.get('FINANCE_SYMBOLS', 'AAPL,MSFT,GOOG').split(','))
    api_key = os.environ.get('ALPHAVANTAGE_API_KEY')
    if not api_key:
        logger.warning('ALPHAVANTAGE_API_KEY not configured; skipping finance fetch')
        return

    for symbol in symbols:
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol.strip(),
            'apikey': api_key,
        }
        try:
            data = _get_json('https://www.alphavantage.co/query', params)
        except requests.RequestException as exc:
            logger.exception('Finance request failed for %s: %s', symbol, exc)
            continue

        quote = data.get('Global Quote') or {}
        payload = {
            'symbol': symbol,
            'payload': quote,
        }
        persist_event(models.FinancialMetric, payload=payload)


@shared_task(bind=True)
def fetch_public_transport_data(self, city_code: str | None = None) -> None:
    api_token = os.environ.get('TRANSPORT_API_TOKEN')
    if not api_token:
        logger.info('TRANSPORT_API_TOKEN not configured; using synthetic traffic data')
        fake_payload = {
            'region': city_code or 'SP-01',
            'payload': {
                'congestion_index': Decimal('0.35'),
                'updated_at': self.request.id,
            },
        }
        persist_event(models.TrafficUpdate, payload=fake_payload)
        return

    params = {'city': city_code or 'Sao Paulo', 'token': api_token}
    try:
        data = _get_json('https://api.citybik.es/v2/networks', params)
    except requests.RequestException as exc:
        logger.exception('Traffic request failed: %s', exc)
        return

    payload = {
        'region': city_code or 'Sao Paulo',
        'payload': data,
    }
    persist_event(models.TrafficUpdate, payload=payload)


@shared_task(bind=True)
def ingest_mqtt_message(self, topic: str, message: str) -> None:
    try:
        payload = json.loads(message)
    except json.JSONDecodeError:
        logger.warning('Invalid JSON from MQTT topic %s: %s', topic, message)
        payload = {'raw': message}

    persist_event(
        models.SensorReading,
        payload={'source': topic, 'payload': payload},
    )


@shared_task(bind=True)
def ingest_kafka_message(self, topic: str, message: Dict[str, Any]) -> None:
    persist_event(
        models.SensorReading,
        payload={'source': topic, 'payload': message},
    )
