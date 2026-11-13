"""Un código QR de prueba (una imagen PNG en base64, como la que entrega uazapi): se ve como un QR, pero no se escanea con un
celular. Se «escanea» con el botón del teléfono de prueba. Se genera aquí, sin dependencias."""
from __future__ import annotations

import base64
import random
import struct
import zlib

_SIZE = 25  # módulos por lado
_SCALE = 8  # píxeles por módulo
_MARGIN = 2


def _modules() -> list[list[bool]]:
    rng = random.Random(2026)
    grid = [[rng.random() < 0.45 for _ in range(_SIZE)] for _ in range(_SIZE)]
    # Los tres cuadros de las esquinas que hacen que parezca un QR.
    for top, left in ((0, 0), (0, _SIZE - 7), (_SIZE - 7, 0)):
        for row in range(7):
            for column in range(7):
                ring = max(abs(row - 3), abs(column - 3))
                grid[top + row][left + column] = ring != 2
    return grid


def _png(grid: list[list[bool]]) -> bytes:
    side = (_SIZE + 2 * _MARGIN) * _SCALE
    rows = []
    for y in range(side):
        module_y = y // _SCALE - _MARGIN
        row = bytearray([0])  # filtro «ninguno»
        for x in range(side):
            module_x = x // _SCALE - _MARGIN
            dark = 0 <= module_x < _SIZE and 0 <= module_y < _SIZE and grid[module_y][module_x]
            row.append(0 if dark else 255)
        rows.append(bytes(row))

    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    header = struct.pack(">IIBBBBB", side, side, 8, 0, 0, 0, 0)  # escala de grises, 8 bits
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(b"".join(rows), 9)) + chunk(b"IEND", b"")


# Como uazapi: el PNG en base64, sin el prefijo `data:` (el motor lo agrega).
QR_DATA = base64.b64encode(_png(_modules())).decode("ascii")
