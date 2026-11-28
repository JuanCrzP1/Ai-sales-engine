---
title: Seguimiento automático a quien deja de responder
module: conversaciones
summary: Cómo el asistente le vuelve a escribir a un cliente que dejó de responder, cuándo se detiene solo y cómo lo detienes para un cliente.
order: 4
updated: 2026-11-28
keywords: seguimiento, remarketing, recordatorio, cliente no responde, volver a escribir, retomar, mensaje automático, detener seguimiento, spam
related: mensajes-del-asistente, responder-y-pausar-la-ia, horario-del-equipo
---

Cuando un cliente estaba interesado y deja de responder, el asistente le vuelve a escribir para retomar la conversación. Funciona por WhatsApp y Telegram.

## Encenderlo

En [Mensajes y canales](panel:mensajes), en **Seguimiento**, activa **Enviar seguimientos**. Ya viene armado con tres mensajes recomendados, con tu trato (de tú o de usted) y con o sin emojis, como elegiste en el estilo:

1. **1 hora después:** «¿Pudiste ver la información? Si te quedó alguna duda, aquí estoy para ayudarte.»
2. **1 día después:** «Hola de nuevo, ¿seguimos con lo que estabas viendo?»
3. **3 días después:** «Te escribo por última vez por ahora: si todavía te interesa, respóndeme y lo retomamos.»

Si quieres, cámbialos:

- **Los textos y los tiempos:** cada mensaje sale el tiempo que elijas después del último mensaje del cliente (como pronto media hora, como tarde 30 días), y siempre después del anterior.
- **Hasta 5 mensajes:** agrega o quita los que quieras. Con **Usar los recomendados** vuelves a los tres de la plataforma.
- **Solo en tu horario:** si lo dejas activo, fuera del horario de [Mi negocio](panel:negocio) espera a que abras. Si no tienes horario, sale a cualquier hora.

Guarda y publica: los seguimientos salen con lo publicado.

## Cuándo se detiene solo

Nunca le escribe a quien no debe. El seguimiento se detiene cuando el cliente:

- **Responde:** el asistente sigue la conversación. Si después vuelve a quedarse callado, la secuencia empieza de nuevo desde el primer mensaje.
- **Compra o avisa un pago.**
- **Pide hablar con una persona,** o tu equipo está atendiendo el chat (la IA pausada).
- **Queda en «No compró»:** si tu equipo lo sacó del embudo en [Clientes](panel:clientes), no se le escribe más.
- **Dice que no le interesa:** antes de cada mensaje, la IA lee el final del chat. Si el cliente la cerró («no me interesa», «ya compré en otro lado», «no me escriban»), no se le escribe más.

Además, nunca salen dos mensajes seguidos ni mensajes viejos: si se juntan varios (por ejemplo, tu negocio estuvo cerrado), sale solo el más reciente, y uno que debía salir hace más de 3 días ya no sale. Por eso, al encenderlo no se les escribe a los clientes que dejaron de responder hace semanas.

## En el chat

Cada seguimiento aparece en el chat marcado como **Seguimiento**, y arriba ves cuántos se le enviaron.

- **Detener seguimiento:** no se le envía ninguno más a ese cliente.
- **Reanudar seguimiento:** vuelve a contar desde que el cliente deje de responder.

Si el cliente dijo que no le interesa, el chat te lo dice y también lo puedes reanudar.

> **Consejo:** tres mensajes bien espaciados funcionan mejor que muchos seguidos. Escribirle de más a quien no responde hace que lo reporten como spam.
