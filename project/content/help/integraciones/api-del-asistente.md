---
title: Conecta tu asistente a otra plataforma con la API
module: integraciones
summary: Usar el mismo asistente de WhatsApp desde Leona u otra plataforma que haga peticiones HTTP, con tu dirección y tu clave.
order: 2
updated: 2026-11-12
keywords: api, http, leona, webhook, plataforma, desarrolladores, curl, javascript, python, conectar, variable sin reemplazar
related: claves-de-api, catalogo-de-integraciones, bandeja-en-vivo
---

En [Integraciones → API del asistente](panel:integraciones/api) conectas tu asistente a cualquier plataforma que haga peticiones HTTP: la plataforma le manda el mensaje de tu cliente y le envía la respuesta. **Es el mismo asistente de WhatsApp**, con lo que publicaste.

Arriba ves si alguna plataforma ya la está usando, por ejemplo «Conectada · usada hace 2 min».

## Conectarla

1. **Tus datos de conexión:** la dirección y tu clave. Crea una clave por plataforma; se muestra **una sola vez**: cópiala y pégala allá.
2. **Conéctala a tu plataforma:** elige su pestaña y sigue los pasos.
3. **Pruébala** desde la misma pantalla: ves lo que respondería tu asistente.

## Las pestañas

- **Leona (Probado):** el flujo que conversa, con sus variables y todo listo para copiar.
- **Otra plataforma:** qué mandar y qué hacer con la respuesta, para cualquier sistema.
- **Desarrolladores:** ejemplos en cURL, JavaScript y Python.

> **Importante:** si tu plataforma manda una variable sin reemplazar (por ejemplo «{nombre}»), la API la rechaza y te dice cuál fue. Así no se mezclan tus clientes en un solo chat.

## Lo que pasa con esos chats

- Llegan a [Conversaciones](panel:conversaciones) con el canal «API» y cuentan en Clientes y Reportes.
- Cuando un cliente pide una persona, la otra plataforma recibe el aviso para pasarlo a tu equipo. La IA se pausa en ese chat hasta que toques **Reanudar IA**.
