"""Le avisa al motor lo que pasa en el simulador, como uazapi: a la dirección que registró cada número y solo los eventos que pidió
(sin lo que excluyó). Anota cada aviso y cada pedido en el registro que muestra el teléfono de prueba («Ver lo que pasó»)."""
from __future__ import annotations

import threading
import time
from collections import deque
from collections.abc import Callable

import httpx

from wa_sim.core.models import Instance, Message
from wa_sim.webhooks import uazapi_events

MAX_LOG = 300


class ActivityLog:
    """Lo que pidió el motor y lo que se le avisó, con su respuesta: para ver qué pasó sin mirar consolas."""

    def __init__(self) -> None:
        self._items: deque[dict] = deque(maxlen=MAX_LOG)
        self._lock = threading.Lock()

    def add(self, kind: str, summary: str, status: int | None = None, detail: str = "") -> None:
        with self._lock:
            self._items.appendleft({"at": time.time(), "kind": kind, "summary": summary, "status": status, "detail": detail[:300]})

    def items(self) -> list[dict]:
        with self._lock:
            return list(self._items)


class UazapiNotifier:
    def __init__(self, log: ActivityLog, sender_name: Callable[[str], str], *, transport: httpx.BaseTransport | None = None) -> None:
        self._log = log
        self._sender_name = sender_name
        self._transport = transport

    def _wanted(self, instance: Instance, event: str, payload: dict) -> bool:
        if not instance.webhook_url or (instance.events and event not in instance.events):
            return False
        message = payload.get("message") if isinstance(payload.get("message"), dict) else {}
        if "isGroupYes" in instance.exclude and message.get("isGroup"):
            return False
        return not ("wasSentByApi" in instance.exclude and message.get("wasSentByApi"))

    def _send(self, instance: Instance, event: str, payload: dict) -> None:
        if not self._wanted(instance, event, payload):
            return
        try:
            with httpx.Client(timeout=30.0, transport=self._transport) as client:
                response = client.post(instance.webhook_url, json=payload)
            self._log.add("aviso", f"{event} → {instance.name}", response.status_code, response.text)
        except httpx.HTTPError as exc:
            self._log.add("aviso", f"{event} → {instance.name}: no llegó", None, type(exc).__name__)

    def connection(self, instance: Instance) -> None:
        self._send(instance, "connection", uazapi_events.connection_event(instance))

    def message(self, instance: Instance, message: Message) -> None:
        self._send(instance, "messages", uazapi_events.message_event(instance, message, self._sender_name(message.phone)))

    def receipt(self, instance: Instance, message_ids: list[str], status: str, phone: str) -> None:
        self._send(instance, "messages_update", uazapi_events.receipt_event(instance, message_ids, status, phone))
