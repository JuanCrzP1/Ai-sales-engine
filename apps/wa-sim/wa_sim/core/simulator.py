"""Las reglas del WhatsApp falso: crear un número, vincularlo por QR, escribir como cliente, recibir lo que envía el negocio, y los
✓ (enviado), ✓✓ (entregado, a los `receipt_seconds`) y azul (leído, al abrir el chat).

No sabe de HTTP ni del formato de uazapi: cada cosa que pasa se la cuenta a `events` (`webhooks/notifier.py`), que la traduce.
"""
from __future__ import annotations

import secrets
import threading
import time
from collections.abc import Callable
from typing import Protocol

from wa_sim.core.models import DELIVERED, READ, SENT, Client, Instance, Media, Message
from wa_sim.core.store import SimulatorStore


class Events(Protocol):
    def connection(self, instance: Instance) -> None: ...

    def message(self, instance: Instance, message: Message) -> None: ...

    def receipt(self, instance: Instance, message_ids: list[str], status: str, phone: str) -> None: ...


class SimulatorError(Exception):
    """Algo que el simulador no puede hacer (un número o un cliente que no existe). El mensaje es para quien prueba."""


def _id(prefix: str) -> str:
    return f"{prefix}{secrets.token_hex(8).upper()}"


class Simulator:
    def __init__(self, store: SimulatorStore, events: Events, *, receipt_seconds: float = 0.7, clock: Callable[[], float] = time.time) -> None:
        self._store = store
        self._events = events
        self._receipt_seconds = receipt_seconds
        self._clock = clock

    @property
    def state(self):
        return self._store.state

    # ------------------------------------------------------------------ números del negocio

    def create_instance(self, name: str) -> Instance:
        with self._store.lock:
            instance = Instance(token=_id("sim-"), name=name or "Número de prueba")
            self.state.instances[instance.token] = instance
            self._store.save()
            return instance

    def instance(self, token: str) -> Instance:
        found = self.state.instances.get(token or "")
        if found is None:
            raise SimulatorError("Ese número no existe en el simulador.")
        return found

    def set_webhook(self, token: str, url: str, events: list[str], exclude: list[str]) -> Instance:
        with self._store.lock:
            instance = self.instance(token)
            instance.webhook_url, instance.events, instance.exclude = url, list(events), list(exclude)
            self._store.save()
            return instance

    def start_connecting(self, token: str) -> Instance:
        """Pedir el QR: queda «esperando el escaneo» (si ya estaba conectado, no cambia)."""
        with self._store.lock:
            instance = self.instance(token)
            if instance.status != "connected":
                instance.status = "connecting"
                self._store.save()
                self._events.connection(instance)
            return instance

    def scan(self, token: str, phone: str = "", profile_name: str = "") -> Instance:
        """El teléfono de prueba «escanea» el QR: el número queda conectado y el negocio recibe el aviso."""
        with self._store.lock:
            instance = self.instance(token)
            if instance.status != "connecting":
                raise SimulatorError("Ese número no está esperando el QR: pídelo primero desde el panel.")
            instance.status = "connected"
            instance.phone = "".join(char for char in phone if char.isdigit()) or f"57300{secrets.randbelow(10**7):07d}"
            instance.profile_name = profile_name or instance.name
            self._store.save()
        self._events.connection(instance)
        return instance

    def disconnect(self, token: str) -> Instance:
        with self._store.lock:
            instance = self.instance(token)
            instance.status, instance.phone = "disconnected", ""
            self._store.save()
        self._events.connection(instance)
        return instance

    def delete_instance(self, token: str) -> None:
        with self._store.lock:
            self.instance(token)
            del self.state.instances[token]
            self._store.save()

    # ------------------------------------------------------------------ clientes y chats

    def add_client(self, phone: str, name: str) -> Client:
        digits = "".join(char for char in phone if char.isdigit())
        if not 7 <= len(digits) <= 15:
            raise SimulatorError("Escribe el número del cliente con el código del país, por ejemplo 573001112233.")
        with self._store.lock:
            client = Client(phone=digits, name=name.strip() or f"Cliente {digits[-4:]}")
            self.state.clients[digits] = client
            self._store.save()
            return client

    def chat(self, token: str, phone: str) -> list[Message]:
        return [message for message in self.state.messages if message.instance == token and message.phone == phone]

    def _connected(self, token: str) -> Instance:
        instance = self.instance(token)
        if instance.status != "connected":
            raise SimulatorError("Ese número no está conectado: escanea el QR primero.")
        return instance

    def customer_writes(self, token: str, phone: str, *, text: str = "", kind: str = "text", media: Media | None = None) -> Message:
        """El cliente escribe (o envía una foto, una nota de voz, un documento): llega al negocio como un mensaje de WhatsApp."""
        return self._incoming(token, phone, "customer", text=text, kind=kind, media=media)

    def business_phone_writes(self, token: str, phone: str, text: str) -> Message:
        """Alguien del negocio responde desde su celular (no desde el sistema): uazapi lo avisa como `fromMe`."""
        return self._incoming(token, phone, "phone", text=text, kind="text", media=None)

    def _incoming(self, token: str, phone: str, author: str, *, text: str, kind: str, media: Media | None) -> Message:
        with self._store.lock:
            instance = self._connected(token)
            client = self.state.clients.get(phone)
            if client is None:
                raise SimulatorError("Agrega primero a ese cliente de prueba.")
            message = Message(id=_id("3EB0"), instance=token, phone=phone, author=author, kind=kind, text=text, media=media, status=READ if author == "customer" else SENT, at=self._clock())
            self.state.messages.append(message)
            self._store.save()
        self._events.message(instance, message)
        return message

    def business_sends(self, token: str, phone: str, *, text: str = "", kind: str = "text", media: Media | None = None) -> Message:
        """El sistema envía (por `/send/text` o `/send/media`): llega al teléfono con ✓ y, al rato, ✓✓."""
        with self._store.lock:
            instance = self._connected(token)
            digits = "".join(char for char in phone if char.isdigit())
            if digits not in self.state.clients:
                # Como en WhatsApp: se le puede escribir a un número aunque no esté en la lista; aparece como contacto nuevo.
                self.state.clients[digits] = Client(phone=digits, name=f"Cliente {digits[-4:]}")
            message = Message(id=_id("3EB0"), instance=token, phone=digits, author="business", kind=kind, text=text, media=media, status=SENT, at=self._clock())
            self.state.messages.append(message)
            self.state.typing.pop(f"{token}:{digits}", None)
            self._store.save()
        timer = threading.Timer(self._receipt_seconds, self._deliver, args=(token, message.id))
        timer.daemon = True
        timer.start()
        return message

    def _deliver(self, token: str, message_id: str) -> None:
        with self._store.lock:
            message = next((item for item in self.state.messages if item.id == message_id), None)
            instance = self.state.instances.get(token)
            if message is None or instance is None or message.status != SENT:
                return
            message.status = DELIVERED
            self._store.save()
        self._events.receipt(instance, [message.id], DELIVERED, message.phone)

    def open_chat(self, token: str, phone: str) -> list[str]:
        """El cliente abre el chat: lo que le envió el negocio queda leído (azul) y el negocio recibe el aviso."""
        with self._store.lock:
            instance = self.instance(token)
            unread = [item for item in self.chat(token, phone) if item.author == "business" and item.status != READ]
            for item in unread:
                item.status = READ
            self._store.save()
        ids = [item.id for item in unread]
        if ids:
            self._events.receipt(instance, ids, READ, phone)
        return ids

    def set_typing(self, token: str, phone: str, seconds: float) -> None:
        with self._store.lock:
            self.state.typing[f"{token}:{''.join(char for char in phone if char.isdigit())}"] = self._clock() + max(1.0, seconds)
            self._store.save()

    def media_of(self, token: str, message_id: str) -> Media | None:
        message = next((item for item in self.state.messages if item.instance == token and item.id == message_id), None)
        return message.media if message else None
