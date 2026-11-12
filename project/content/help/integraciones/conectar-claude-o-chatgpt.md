---
title: Conecta Claude, ChatGPT u otro agente
module: integraciones
summary: Claude y ChatGPT se conectan iniciando sesión, sin clave; Claude Code, Cursor y n8n, con una clave para el agente.
order: 5
updated: 2026-11-12
keywords: claude, chatgpt, conector, conector personalizado, oauth, iniciar sesión, autorizar, claude code, cursor, n8n, mcp
related: agentes-de-ia, claves-de-api
---

## Claude (en la web o en la app) y ChatGPT

No necesitas crear una clave: pegas la dirección, inicias sesión y eliges qué puede hacer. La dirección del servidor está en [Integraciones → Agentes de IA (MCP)](panel:integraciones/agentes).

1. **En Claude:** Configuración → Conectores → **Agregar conector personalizado**. Ponle un nombre, pega la dirección del servidor y pulsa **Conectar**.
2. **En ChatGPT:** en la configuración de conectores, activa el modo de desarrollador, crea un conector, pega la dirección y elige **OAuth** como autenticación.
3. Se abre esta plataforma: inicia sesión, elige a qué negocios entra y qué puede hacer, y pulsa **Autorizar**.

## Claude Code, Cursor, n8n y otros

1. Crea una clave para el agente, con sus permisos.
2. La pantalla te da lo que se pega en cada uno, en su pestaña (Claude Code, Cursor y otros, n8n).

## Revocar el acceso

Las conexiones por inicio de sesión aparecen en [Claves de API](panel:integraciones/claves) con el nombre del agente. Revócalas cuando quieras: el agente deja de entrar al instante. Ver [Tus claves de API](claves-de-api).
