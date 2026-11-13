"""El teléfono de prueba: la API (`/_sim/*`) que usan la página del navegador y los recorridos automáticos para hacer de cliente.

Nada de esto existe en uazapi: es el «otro lado» del chat. Escanear el QR, agregar clientes, escribir como cliente (texto, foto, nota
de voz, documento), escribir como el negocio desde su celular, abrir un chat (lo marca leído) y ver lo que pasó.
"""
from __future__ import annotations

import base64
import time
from dataclasses import asdict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from wa_sim.core.models import Media
from wa_sim.core.simulator import Simulator, SimulatorError
from wa_sim.webhooks.notifier import ActivityLog

# Lo más grande que acepta el teléfono de prueba (el motor guarda hasta 4 MB por archivo).
MAX_FILE_BYTES = 5 * 1024 * 1024


class ScanRequest(BaseModel):
    phone: str = ""
    profile_name: str = ""


class ClientRequest(BaseModel):
    phone: str
    name: str = ""


class WriteRequest(BaseModel):
    text: str = Field(default="", max_length=4000)
    # Un archivo: su tipo (image, audio, video, document), en base64 y con su nombre.
    kind: str = "text"
    file_base64: str = ""
    mime_type: str = ""
    file_name: str = ""
    # true: lo escribe el negocio desde su celular (no el cliente).
    from_business_phone: bool = False


def build_router(simulator: Simulator, log: ActivityLog, reset) -> APIRouter:
    router = APIRouter(prefix="/_sim")

    def run(action):
        try:
            return action()
        except SimulatorError as error:
            raise HTTPException(status_code=400, detail=str(error)) from None

    @router.get("/state")
    def state() -> dict:
        now = time.time()
        current = simulator.state
        last: dict[str, dict] = {}
        for message in current.messages:
            last[f"{message.instance}:{message.phone}"] = {"instance": message.instance, "phone": message.phone, "preview": message.text or message.kind, "at": message.at}
        return {
            # El webhook solo dice si el motor lo registró: su dirección lleva el identificador secreto del negocio.
            "instances": [asdict(instance) | {"webhook_url": bool(instance.webhook_url)} for instance in current.instances.values()],
            "clients": [asdict(client) for client in current.clients.values()],
            "chats": sorted(last.values(), key=lambda chat: chat["at"], reverse=True),
            "typing": [key for key, until in current.typing.items() if until > now],
        }

    @router.get("/chats/{token}/{phone}")
    def chat(token: str, phone: str) -> dict:
        messages = simulator.chat(token, phone)
        return {"messages": [_message_view(message) for message in messages]}

    @router.post("/instances/{token}/scan")
    def scan(token: str, body: ScanRequest) -> dict:
        return asdict(run(lambda: simulator.scan(token, body.phone, body.profile_name)))

    @router.post("/clients")
    def add_client(body: ClientRequest) -> dict:
        return asdict(run(lambda: simulator.add_client(body.phone, body.name)))

    @router.post("/chats/{token}/{phone}/write")
    def write(token: str, phone: str, body: WriteRequest) -> dict:
        media = None
        if body.kind != "text":
            content = _decoded(body.file_base64)
            media = Media(mime_type=body.mime_type or "application/octet-stream", base64=base64.b64encode(content).decode("ascii"), file_name=body.file_name)
        if body.from_business_phone:
            message = run(lambda: simulator.business_phone_writes(token, phone, body.text))
        else:
            message = run(lambda: simulator.customer_writes(token, phone, text=body.text, kind=body.kind, media=media))
        return _message_view(message)

    @router.post("/chats/{token}/{phone}/open")
    def open_chat(token: str, phone: str) -> dict:
        return {"read": run(lambda: simulator.open_chat(token, phone))}

    @router.get("/log")
    def activity() -> dict:
        return {"items": log.items()}

    @router.post("/reset")
    def start_over() -> dict:
        reset()
        log.add("simulador", "Empezar de cero")
        return {"ok": True}

    return router


def _decoded(raw: str) -> bytes:
    data = raw.split(",", 1)[-1] if raw.startswith("data:") else raw
    try:
        content = base64.b64decode(data, validate=True)
    except ValueError:
        raise HTTPException(status_code=400, detail="El archivo no se pudo leer.") from None
    if not 0 < len(content) <= MAX_FILE_BYTES:
        raise HTTPException(status_code=400, detail="El archivo está vacío o pesa más de 5 MB.")
    return content


def _message_view(message) -> dict:
    view = asdict(message)
    if message.media is not None:
        view["media"] = {"mime_type": message.media.mime_type, "file_name": message.media.file_name, "data_url": f"data:{message.media.mime_type};base64,{message.media.base64}"}
    return view
