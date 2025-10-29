"""Model signal handlers that keep the dashboard in sync."""

from __future__ import annotations

from django.db.models.signals import post_save
from django.dispatch import receiver

from . import models
from .realtime import DashboardEvent, broadcast_event

MODEL_EVENT = {
    models.SensorReading: 'sensor',
    models.FinancialMetric: 'finance',
    models.TrafficUpdate: 'traffic',
    models.WeatherSnapshot: 'weather',
}


@receiver(post_save, sender=models.SensorReading)
@receiver(post_save, sender=models.FinancialMetric)
@receiver(post_save, sender=models.TrafficUpdate)
@receiver(post_save, sender=models.WeatherSnapshot)
def push_dashboard_update(sender, instance, created, **kwargs):
    if not created:
        return

    event_type = MODEL_EVENT[sender]
    payload = {
        'id': instance.pk,
        'payload': instance.payload,
        'timestamp': instance.created_at.isoformat(),
    }
    if hasattr(instance, 'source') and instance.source:
        payload['source'] = instance.source
    if hasattr(instance, 'symbol') and instance.symbol:
        payload['symbol'] = instance.symbol
    if hasattr(instance, 'region') and instance.region:
        payload['region'] = instance.region
    if hasattr(instance, 'location') and instance.location:
        payload['location'] = instance.location

    if isinstance(instance.payload, dict):
        if 'value' in instance.payload:
            payload['value'] = instance.payload.get('value')
        if '05. price' in instance.payload:
            try:
                payload['price'] = float(instance.payload.get('05. price') or 0)
            except (TypeError, ValueError):
                payload['price'] = 0
        main = instance.payload.get('main', {})
        if isinstance(main, dict):
            try:
                payload['temperature'] = float(main.get('temp') or 0)
            except (TypeError, ValueError):
                payload['temperature'] = 0
            try:
                payload['humidity'] = float(main.get('humidity') or 0)
            except (TypeError, ValueError):
                payload['humidity'] = 0
        if 'congestion_index' in instance.payload:
            try:
                payload['congestion_index'] = float(instance.payload.get('congestion_index') or 0)
            except (TypeError, ValueError):
                payload['congestion_index'] = 0

    broadcast_event(DashboardEvent(event_type=event_type, data=payload))
