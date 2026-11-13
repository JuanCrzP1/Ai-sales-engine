---
title: "Mensajes y canales: la bienvenida y los mensajes fijos"
module: asistente
summary: La bienvenida, lo que dice al recibir un pago, al pasar a una persona, fuera del horario, al retomar un chat y si no puede responder.
order: 6
updated: 2026-11-13
keywords: bienvenida, saludo, mensajes, pago recibido, pasar a una persona, fuera del horario, la ia retoma, si no puede responder, canales, restricciones
related: como-atiende, horario-del-equipo, si-la-ia-falla
---

En [Mensajes y canales](panel:mensajes) escribes los mensajes que el asistente envía **tal cual** en momentos clave.

## Mensajes

- **Mensaje de bienvenida:** se envía tal cual cuando un cliente nuevo solo saluda. Si lo desactivas, responde el asistente.
- **Cómo le llegan los datos de pago:** el mensaje que recibe el cliente cuando elige cómo pagar. Ya viene escrito y ordenado: el medio, el número en su propia línea (se copia con un toque), a nombre de quién está y que envíe el comprobante. Puedes cambiarlo con los marcadores `{medio}`, `{datos}` (obligatorio) y `{titular}`. Lo envía el sistema con tus datos reales: la IA nunca los ve. Ver [Pagos y cierre](pagos-y-cierre).
- **Mensajes de pago:** lo que dice cuando el cliente dice que ya pagó y cuando tu equipo confirma el pago. El asistente no verifica pagos: estos mensajes solo acompañan lo que el cliente informa.
- **Si el asistente no puede responder:** lo que recibe el cliente si la IA falla (por ejemplo, si se acabó el saldo de tu clave). Ver [Si la IA falla](si-la-ia-falla).

### Otros mensajes

Son opcionales: si no los escribes, el asistente responde con sus propias palabras.

- **Al pedir los datos del cliente** y **al pasar la conversación a una persona.**
- **Fuera del horario del equipo:** cuando un chat pasa a una persona fuera del horario. Si lo dejas vacío, el asistente dice tu horario y cuándo lo atienden. Ver [El horario del equipo](horario-del-equipo).
- **Cuando la IA retoma el chat:** si nadie de tu equipo responde a tiempo, la IA vuelve a atender y envía este mensaje primero. Ver [Si nadie responde](si-nadie-responde).
- **Después de una compra:** lo usa cuando el cliente vuelve a escribir después de pagar.
- **Seguimiento a un cliente que no respondió:** se guarda para cuando los canales puedan escribirle primero al cliente.

## Canales

- **Canales de atención:** por dónde atiende tu negocio. El asistente los menciona cuando el cliente pregunta.
- **Otros canales y restricciones:** por dónde no atiendes y lo que tu negocio no hace.

> **Importante:** estos mensajes son parte de la configuración del asistente: llegan a tus clientes cuando publicas.
