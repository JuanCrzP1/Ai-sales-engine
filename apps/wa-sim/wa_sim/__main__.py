"""Arranca el simulador: `cd apps/wa-sim && ../../.venv/bin/python -m wa_sim` (teléfono de prueba en http://localhost:3300)."""
from __future__ import annotations

import sys

import uvicorn

from wa_sim.config import ProductionRefused, load_config
from wa_sim.server import create_simulator


def main() -> int:
    try:
        config = load_config()
    except ProductionRefused as error:
        print(f"[detenido] {error}")
        return 1
    simulator = create_simulator(config)
    print(f"[ok] WhatsApp simulado en http://localhost:{config.port} (token de administrador: «{config.admin_token}»)")
    print(f"     En el panel: WHATSAPP_SIMULATOR_URL=http://127.0.0.1:{config.port} y ENGINE_PUBLIC_URL=http://127.0.0.1:8082")
    # Solo en este equipo: nunca escucha fuera de localhost.
    uvicorn.run(simulator.app, host="127.0.0.1", port=config.port, log_level="warning")
    return 0


if __name__ == "__main__":
    sys.exit(main())
