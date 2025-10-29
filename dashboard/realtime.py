"""Helpers for broadcasting real-time updates through Django Channels."""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Any, Dict

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)

DASHBOARD_GROUP = 'dashboard_updates'


@dataclass
class DashboardEvent:
    event_type: str
    data: Dict[str, Any]

    def to_message(self) -> Dict[str, Any]:
        return {'type': 'dashboard_update', 'data': asdict(self)}


def broadcast_event(event: DashboardEvent) -> None:
    channel_layer = get_channel_layer()
    if channel_layer is None:
        logger.warning('Channel layer unavailable; skipping broadcast')
        return

    async_to_sync(channel_layer.group_send)(DASHBOARD_GROUP, event.to_message())
