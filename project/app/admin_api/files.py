"""Archivos que entran y salen por la API del panel: leer una subida (el archivo tal cual en el cuerpo, con su nombre y su texto en
encabezados) y servir uno sin riesgo (nunca se ejecuta en el panel: solo tipos seguros se muestran en línea, sin scripts)."""
from __future__ import annotations

from urllib.parse import unquote

from fastapi import Request, Response, status

from app.admin_api.errors import ApiError
from app.domain.business_config.conversations import MAX_MEDIA_BYTES, Attachment, MediaFile, validated_attachment

# Lo que se muestra en línea: fotos que no ejecutan nada (ni SVG ni HTML) y PDF.
INLINE_TYPES = frozenset({"image/jpeg", "image/png", "image/webp", "image/gif", "application/pdf"})


async def read_upload(request: Request) -> Attachment:
    """El archivo de la petición, revisado: el cuerpo es el archivo con su `Content-Type`; `X-File-Name` y `X-Caption` van
    codificados como en una URL. Más de 4 MB se rechaza antes de leerlo."""
    declared = request.headers.get("content-length", "")
    if declared.isdigit() and int(declared) > MAX_MEDIA_BYTES:
        raise ApiError(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "El archivo pesa más de 4 MB. Envía uno más liviano.", code="too_large")
    return validated_attachment(
        mime_type=request.headers.get("content-type"),
        content=await request.body(),
        file_name=unquote(request.headers.get("x-file-name", "")),
        caption=unquote(request.headers.get("x-caption", "")),
    )


def file_response(file: MediaFile) -> Response:
    safe = file.mime_type in INLINE_TYPES or file.mime_type.startswith(("audio/", "video/"))
    headers = {
        "X-Content-Type-Options": "nosniff",
        "Content-Security-Policy": "default-src 'none'; sandbox",
        "Content-Disposition": "inline" if safe else "attachment",
    }
    return Response(content=file.content, media_type=file.mime_type if safe else "application/octet-stream", headers=headers)
