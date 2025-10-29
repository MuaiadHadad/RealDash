"""WebSocket consumer used by the real-time dashboard."""

import json
from typing import Any, Dict

from channels.generic.websocket import AsyncWebsocketConsumer


class DashboardConsumer(AsyncWebsocketConsumer):
    group_name = 'dashboard_updates'

    async def connect(self) -> None:
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code: int) -> None:  # pragma: no cover - network cleanup
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data: str | None = None, bytes_data: bytes | None = None) -> None:
        if not text_data:
            return
        payload: Dict[str, Any] = json.loads(text_data)
        if payload.get('type') == 'ping':
            await self.send_json({'type': 'pong'})

    async def dashboard_update(self, event: Dict[str, Any]) -> None:
        await self.send_json(event['data'])

    async def send_json(self, payload: Dict[str, Any]) -> None:
        await self.send(text_data=json.dumps(payload))
