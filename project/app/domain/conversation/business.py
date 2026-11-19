"""El negocio al que llega un mensaje, como lo lee el motor: su identificador (`slug`) y su nombre.

Los canales (WhatsApp por código QR, Telegram, la API del asistente) saben el negocio por su identificador; el resto de su
configuración el motor la lee de la versión publicada (`application/runtime`). Reemplaza al modelo `Tenant` del sistema anterior,
que se usaba solo para llevar estos dos datos.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BusinessRef:
    slug: str
    name: str = ""

    @classmethod
    def of(cls, slug: str) -> "BusinessRef":
        return cls(slug=slug, name=slug)
