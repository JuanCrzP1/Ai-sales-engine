"""La API de uazapi que usa el motor (`project/app/infrastructure/channels/uazapi.py`), con sus mismos tokens y errores:
`admintoken` para crear números, `token` para todo lo demás, 401 si el token no existe.

| uazapi | En el simulador |
|---|---|
| `POST /instance/create` | Un número nuevo, desconectado. |
| `POST /instance/connect`, `GET /instance/status` | Pide el QR; el teléfono de prueba lo «escanea». |
| `POST /instance/disconnect`, `DELETE /instance` | Cierra la sesión / borra el número. |
| `POST /webhook` | Guarda adónde avisar y qué eventos. |
| `POST /send/text`, `POST /send/media` | Llega al teléfono de prueba: ✓, y ✓✓ al rato. |
| `POST /message/presence` | «Escribiendo…» en el chat del teléfono. |
| `POST /message/download` | El archivo que envió el cliente, en base64. |
"""
from __future__ import annotations

import base64
import binascii
import mimetypes
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request

from wa_sim.core.models import Media
from wa_sim.core.simulator import Simulator, SimulatorError
from wa_sim.webhooks import uazapi_events
from wa_sim.webhooks.notifier import ActivityLog

# Lo que el motor envía como `type` de un archivo → cómo lo muestra el teléfono.
_MEDIA_KINDS = {"image": "image", "video": "video", "audio": "audio", "ptt": "audio", "document": "document"}


def build_router(simulator: Simulator, admin_token: str, log: ActivityLog) -> APIRouter:
    router = APIRouter()

    def instance_of(token: str | None):
        try:
            return simulator.instance(token or "")
        except SimulatorError:
            raise HTTPException(status_code=401, detail={"code": 401, "message": "Invalid token.", "data": {}}) from None

    async def body_of(request: Request) -> dict[str, Any]:
        try:
            payload = await request.json()
        except ValueError:
            payload = {}
        return payload if isinstance(payload, dict) else {}

    def record(summary: str, status: int = 200) -> None:
        log.add("pedido", summary, status)

    def failed(error: SimulatorError) -> HTTPException:
        return HTTPException(status_code=400, detail={"error": str(error)})

    # ------------------------------------------------------------------ números

    @router.post("/instance/create")
    async def create(request: Request, admintoken: str | None = Header(default=None)) -> dict:
        if admintoken != admin_token:
            record("crear número: token de administrador inválido", 401)
            raise HTTPException(status_code=401, detail={"error": "Invalid AdminToken Header"})
        body = await body_of(request)
        instance = simulator.create_instance(str(body.get("name") or ""))
        record(f"crear número «{instance.name}»")
        return {"instance": {"token": instance.token, "status": instance.status, "name": instance.name}, "token": instance.token}

    @router.post("/instance/connect")
    def connect(token: str | None = Header(default=None)) -> dict:
        instance = simulator.start_connecting(instance_of(token).token)
        record(f"pedir QR de «{instance.name}»")
        return uazapi_events.instance_status(instance)

    @router.get("/instance/status")
    def status(token: str | None = Header(default=None)) -> dict:
        return uazapi_events.instance_status(instance_of(token))

    @router.post("/instance/disconnect")
    def disconnect(token: str | None = Header(default=None)) -> dict:
        instance = simulator.disconnect(instance_of(token).token)
        record(f"desconectar «{instance.name}»")
        return {"response": "Disconnected"}

    @router.delete("/instance")
    def delete(token: str | None = Header(default=None)) -> dict:
        instance = instance_of(token)
        simulator.delete_instance(instance.token)
        record(f"borrar «{instance.name}»")
        return {"response": "Instance deleted"}

    @router.post("/webhook")
    async def webhook(request: Request, token: str | None = Header(default=None)) -> dict:
        instance = instance_of(token)
        body = await body_of(request)
        simulator.set_webhook(instance.token, str(body.get("url") or ""), list(body.get("events") or []), list(body.get("excludeMessages") or []))
        record(f"registrar el aviso de «{instance.name}»")
        return {"url": body.get("url"), "enabled": True}

    # ------------------------------------------------------------------ mensajes

    @router.post("/send/text")
    async def send_text(request: Request, token: str | None = Header(default=None)) -> dict:
        instance = instance_of(token)
        body = await body_of(request)
        try:
            message = simulator.business_sends(instance.token, str(body.get("number") or ""), text=str(body.get("text") or ""))
        except SimulatorError as error:
            raise failed(error) from None
        record(f"enviar texto a {message.phone}")
        return {"messageid": message.id, "id": message.id, "status": "sent"}

    @router.post("/send/media")
    async def send_media(request: Request, token: str | None = Header(default=None)) -> dict:
        instance = instance_of(token)
        body = await body_of(request)
        kind = _MEDIA_KINDS.get(str(body.get("type") or ""), "document")
        raw = str(body.get("file") or "")
        try:
            base64.b64decode(raw, validate=True)
        except (binascii.Error, ValueError):
            record("enviar archivo: el archivo no es base64", 400)
            raise HTTPException(status_code=400, detail={"error": "invalid file"}) from None
        name = str(body.get("docName") or "")
        media = Media(mime_type=str(body.get("mimetype") or _guess_mime(kind, name)), base64=raw, file_name=name)
        try:
            message = simulator.business_sends(instance.token, str(body.get("number") or ""), text=str(body.get("text") or ""), kind=kind, media=media)
        except SimulatorError as error:
            raise failed(error) from None
        record(f"enviar {kind} a {message.phone}")
        return {"messageid": message.id, "id": message.id, "status": "sent"}

    @router.post("/message/presence")
    async def presence(request: Request, token: str | None = Header(default=None)) -> dict:
        instance = instance_of(token)
        body = await body_of(request)
        simulator.set_typing(instance.token, str(body.get("number") or ""), float(body.get("delay") or 30_000) / 1000)
        return {"response": "ok"}

    @router.post("/message/download")
    async def download(request: Request, token: str | None = Header(default=None)) -> dict:
        instance = instance_of(token)
        body = await body_of(request)
        media = simulator.media_of(instance.token, str(body.get("id") or ""))
        if media is None:
            # 400 y no 404: para el motor, un 404 de uazapi significa que el número ya no existe.
            raise HTTPException(status_code=400, detail={"error": "message not found"})
        record("descargar un archivo del cliente")
        return {"base64Data": media.base64, "mimetype": media.mime_type, "fileName": media.file_name}

    return router


def _guess_mime(kind: str, file_name: str) -> str:
    guessed = mimetypes.guess_type(file_name)[0] if file_name else None
    return guessed or {"image": "image/jpeg", "video": "video/mp4", "audio": "audio/ogg"}.get(kind, "application/octet-stream")
