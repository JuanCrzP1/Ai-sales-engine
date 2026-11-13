---
title: Conecta Telegram con el bot de tu negocio
module: canales
summary: Crear el bot de tu negocio con @BotFather, pegar su código en Canales y compartir su enlace para que tus clientes te escriban.
order: 4
updated: 2026-11-13
keywords: telegram, bot, botfather, token, código, conectar, enlace, t.me
related: conectar-whatsapp, guardar-y-publicar
---

Tu asistente también atiende por **Telegram**, con la versión **publicada** de tu negocio. Telegram es oficial y gratis: no hay código QR ni riesgo de bloqueo, porque Telegram permite los bots.

En Telegram, tu negocio es un **bot**: una cuenta con su propio nombre y su usuario (por ejemplo, `@CafeAromaBot`). Tú lo creas y nosotros lo conectamos con tu asistente.

## Crear el bot

1. En Telegram, en el celular o en el computador, busca **@BotFather** (es el bot oficial de Telegram, con la insignia azul) y toca **Iniciar**.
2. Escríbele `/newbot`.
3. Te pide el **nombre**: el que verán tus clientes, por ejemplo `Café Aroma`.
4. Te pide el **usuario**: debe terminar en «bot» y no estar en uso, por ejemplo `CafeAromaBot`.
5. Te responde con un **código** (token) que se ve así: `7123456789:AAH…`. Cópialo completo.

> **Importante:** ese código es la llave de tu bot. No lo compartas con nadie: solo pégalo en el panel.

## Conectarlo

1. En [Canales](panel:canales), en la tarjeta **Telegram**, toca **Conectar Telegram**.
2. Pega el código y toca **Conectar**.
3. Listo: la tarjeta dice **Conectado como @tubot** y te muestra el enlace del bot.

El código queda guardado cifrado y nunca se vuelve a mostrar.

## Que tus clientes te escriban

Toca **Copiar enlace** y compártelo donde te encuentran tus clientes: Instagram, tu página web, tus estados de WhatsApp o un código QR impreso en tu local. El enlace es `t.me/` seguido del usuario de tu bot.

Al abrirlo, el cliente toca **Iniciar** y tu asistente lo saluda. Sus chats llegan a [Conversaciones](panel:conversaciones), con el ícono de Telegram, y tu equipo puede responder desde ahí, con respuestas rápidas, fotos y documentos, como en WhatsApp.

## Qué cambia frente a WhatsApp

| | WhatsApp | Telegram |
|---|---|---|
| Quién escribe primero | Tu negocio puede escribirle a un número | Siempre el cliente: Telegram no deja que un bot escriba primero |
| Cómo ves al cliente | Por su número | Por su nombre de Telegram (su número no llega) |
| Conexión | Código QR; puede desconectarse | Código del bot; no se cae |
| Grupos | No se atienden | Tampoco: solo chats privados |

## Si dice «No recibe mensajes»

Pasa en dos casos:

- **Cambiaste el código en @BotFather** (por ejemplo, con `/revoke`). Pídele el código nuevo con `/token`, toca **Pegar un código nuevo** y pégalo.
- **Conectaste el mismo bot en otra plataforma.** Un bot solo envía sus mensajes a un lugar. Toca **Volver a conectar** para traerlos aquí.

Para comprobarlo cuando quieras, toca **Revisar conexión**.

## Cambiar de bot o desconectarlo

- **Cambiar de bot:** pega el código del otro bot. El anterior deja de recibir mensajes aquí.
- **Desconectar:** el bot deja de recibir mensajes aquí. Los chats y su historial se quedan en Conversaciones.

> **Consejo:** cada negocio necesita su propio bot. Si tienes varios negocios, crea un bot para cada uno en @BotFather.
