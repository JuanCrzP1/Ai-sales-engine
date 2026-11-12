"""El servidor MCP de la plataforma: los agentes de IA (Claude, Cursor, n8n...) trabajan en los negocios de una cuenta con una
clave de API y sus permisos por área.

- `tool.py`: qué es una herramienta (lo que ve el agente, el permiso que exige y cómo se ejecuta) y la revisión de sus argumentos.
- `access.py`: quién llama (la clave, su dueño, sus permisos y a qué negocios entra).
- `protocol.py`: el protocolo (JSON-RPC 2.0, sin estado): `initialize`, `ping`, `tools/list` y `tools/call`.
- `tools/`: las herramientas, adaptadores delgados sobre los MISMOS servicios que usa el panel. No hay reglas de negocio aquí.
- `server.py`: arma el servidor con sus herramientas y reconoce las claves.

El transporte HTTP está en `app/admin_api/mcp_routes.py`. Ver `docs/mcp.md`.
"""
