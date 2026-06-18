from fastapi import WebSocket
from typing import Dict, Set
import json


class ConnectionManager:
    """
    Gestionnaire de connexions WebSocket.
    Supporte les canaux (probe, alerts) et les abonnements par device_id.
    """

    def __init__(self):
        # canal → set de websockets
        self._channels: Dict[str, Set[WebSocket]] = {
            "probe":  set(),
            "alerts": set(),
        }
        # websocket → set de device_ids abonnés
        self._subscriptions: Dict[WebSocket, Set[str]] = {}

    async def connect(self, websocket: WebSocket, channel: str):
        await websocket.accept()
        self._channels.setdefault(channel, set()).add(websocket)
        self._subscriptions[websocket] = set()

    def disconnect(self, websocket: WebSocket, channel: str):
        self._channels.get(channel, set()).discard(websocket)
        self._subscriptions.pop(websocket, None)

    def subscribe(self, websocket: WebSocket, device_ids: list[str]):
        if websocket in self._subscriptions:
            self._subscriptions[websocket].update(device_ids)

    def unsubscribe(self, websocket: WebSocket, device_ids: list[str]):
        if websocket in self._subscriptions:
            self._subscriptions[websocket].difference_update(device_ids)

    async def send_probe_result(self, device_id: str, data: dict):
        """Envoyer un résultat de sonde aux abonnés du device."""
        dead = set()
        for ws in self._channels.get("probe", set()):
            subs = self._subscriptions.get(ws, set())
            if not subs or device_id in subs:
                try:
                    await ws.send_text(json.dumps(data))
                except Exception:
                    dead.add(ws)
        for ws in dead:
            self.disconnect(ws, "probe")

    async def broadcast_alert(self, data: dict):
        """Diffuser une alerte à tous les connectés sur le canal alerts."""
        dead = set()
        for ws in self._channels.get("alerts", set()):
            try:
                await ws.send_text(json.dumps(data))
            except Exception:
                dead.add(ws)
        for ws in dead:
            self.disconnect(ws, "alerts")


manager = ConnectionManager()
