"""Entender las fotos y los audios que mandan los clientes: la descripción de una foto (y si es un comprobante de pago) y la
transcripción de una nota de voz.

Usa la clave de OpenRouter del negocio (la plataforma no tiene clave propia) con un modelo económico que ve imágenes y escucha audio
(`MEDIA_AI_MODEL`, por omisión `google/gemini-2.5-flash-lite`), y anota el consumo en la cuenta del negocio. Lo que entiende pasa al
asistente como texto, así el motor sigue igual. Si algo falla, devuelve None y el asistente sabe que llegó un archivo que no pudo ver.

Nunca pide números de cuenta ni teléfonos de pago: de un comprobante solo se toman la entidad, el valor y la fecha.
"""
from __future__ import annotations

import base64
import json
import os
import re
from collections.abc import Callable
from dataclasses import dataclass

import httpx

from app.config import settings
from app.domain.business_config.conversations import MediaFile
from app.utils.logger import logger

DEFAULT_MEDIA_MODEL = "google/gemini-2.5-flash-lite"
TIMEOUT = httpx.Timeout(45.0, connect=8.0)
MAX_NOTE_CHARS = 1200

# (modelo, tokens de entrada, tokens de salida, costo en dólares o None): el mismo registro de consumo del motor.
UsageCallback = Callable[[str, int, int, float | None], None]

_IMAGE_PROMPT = """
Eres los ojos del asistente de ventas de un negocio. Un cliente le envió esta imagen por chat.
Responde solo un objeto JSON: {"descripcion": "...", "comprobante_de_pago": false, "datos_del_pago": ""}
- descripcion: qué se ve, en una o dos frases en español, sin inventar nada que no se vea.
- comprobante_de_pago: true solo si es un comprobante, recibo o captura de una transferencia o un pago.
- datos_del_pago: si es un comprobante, la entidad, el valor y la fecha tal como se leen. No copies números de cuenta,
  teléfonos ni referencias completas.
""".strip()

_AUDIO_PROMPT = (
    "Transcribe exactamente esta nota de voz de un cliente, en el idioma en que habla. Responde solo con la transcripción, sin "
    "comentarios. Si no se entiende nada, responde vacío."
)

# Formato de audio que acepta el modelo, según el tipo del archivo (uazapi entrega las notas de voz en MP3).
_AUDIO_FORMATS = {"audio/mpeg": "mp3", "audio/mp3": "mp3", "audio/wav": "wav", "audio/x-wav": "wav", "audio/ogg": "ogg", "audio/aac": "aac", "audio/mp4": "m4a"}


@dataclass(frozen=True)
class ImageUnderstanding:
    description: str
    payment_proof: bool = False
    payment_details: str = ""


def media_model() -> str:
    return str(os.getenv("MEDIA_AI_MODEL") or "").strip() or DEFAULT_MEDIA_MODEL


class OpenRouterMediaInterpreter:
    def __init__(self, *, transport: httpx.BaseTransport | None = None, base_url: str | None = None, model: str | None = None) -> None:
        self._transport = transport
        self._base_url = (base_url or settings.openrouter_base_url).rstrip("/")
        self._model = model or media_model()

    def describe_image(self, api_key: str, media: MediaFile, *, on_usage: UsageCallback | None = None) -> ImageUnderstanding | None:
        """Qué se ve en la foto y, si es un comprobante, sus datos visibles (sin números de cuenta)."""
        data = base64.b64encode(media.content).decode("ascii")
        content = [
            {"type": "text", "text": _IMAGE_PROMPT},
            {"type": "image_url", "image_url": {"url": f"data:{media.mime_type};base64,{data}"}},
        ]
        answer = self._complete(api_key, content, on_usage=on_usage, json_output=True)
        if not answer:
            return None
        match = re.search(r"\{.*\}", answer, re.S)
        try:
            parsed = json.loads(match.group(0)) if match else {}
        except ValueError:
            parsed = {}
        description = _clip(parsed.get("descripcion") if isinstance(parsed, dict) else "") or _clip(answer if not match else "")
        if not description:
            return None
        proof = bool(parsed.get("comprobante_de_pago")) if isinstance(parsed, dict) else False
        details = _clip(parsed.get("datos_del_pago")) if proof else ""
        return ImageUnderstanding(description, proof, details)

    def transcribe_audio(self, api_key: str, media: MediaFile, *, on_usage: UsageCallback | None = None) -> str | None:
        """Lo que dice la nota de voz, o None si no se pudo escuchar."""
        audio_format = _AUDIO_FORMATS.get(media.mime_type)
        if audio_format is None:
            logger.warning("audio_formato_no_soportado", extra={"mime_type": media.mime_type})
            return None
        content = [
            {"type": "text", "text": _AUDIO_PROMPT},
            {"type": "input_audio", "input_audio": {"data": base64.b64encode(media.content).decode("ascii"), "format": audio_format}},
        ]
        return _clip(self._complete(api_key, content, on_usage=on_usage)) or None

    def _complete(self, api_key: str, content: list[dict], *, on_usage: UsageCallback | None, json_output: bool = False) -> str:
        body: dict = {"model": self._model, "messages": [{"role": "user", "content": content}], "temperature": 0, "usage": {"include": True}}
        if json_output:
            body["response_format"] = {"type": "json_object"}
        try:
            with httpx.Client(timeout=TIMEOUT, transport=self._transport) as client:
                response = client.post(
                    f"{self._base_url}/chat/completions", json=body,
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                )
        except httpx.HTTPError as exc:
            logger.warning("multimedia_sin_respuesta", extra={"error": type(exc).__name__})
            return ""
        if response.status_code >= 400:
            logger.warning("multimedia_rechazada", extra={"status": response.status_code, "model": self._model})
            return ""
        try:
            payload = response.json()
        except ValueError:
            return ""
        usage = payload.get("usage") if isinstance(payload.get("usage"), dict) else {}
        if on_usage is not None and usage:
            cost = usage.get("cost")
            on_usage(
                str(payload.get("model") or self._model), int(usage.get("prompt_tokens") or 0), int(usage.get("completion_tokens") or 0),
                float(cost) if isinstance(cost, (int, float)) else None,
            )
        choices = payload.get("choices") if isinstance(payload.get("choices"), list) else []
        message = choices[0].get("message") if choices and isinstance(choices[0], dict) else {}
        return str((message or {}).get("content") or "").strip()


def _clip(value: object) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= MAX_NOTE_CHARS else text[: MAX_NOTE_CHARS - 1] + "…"
