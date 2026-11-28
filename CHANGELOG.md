# Cambios

Lo que cambió en Merceam, de lo más reciente a lo más antiguo. Cada entrada dice qué gana el negocio; el detalle técnico
está en el historial de git y en `docs/plan-v1.md`.

## 28 de noviembre de 2026

**Recordatorios del equipo**
- Desde la ficha de un cliente anotas qué hay que hacer y cuándo («llamarlo para cerrar», mañana a las 9), con atajos de fecha y
  para quién de tu equipo.
- En **Clientes → Recordatorios** los ves todos en vencidos, de hoy, próximos y hechos; los tuyos o los de todo el equipo. El botón
  dice cuántos tienes vencidos, y la tarjeta de cada cliente muestra el más próximo.
- Un toque los marca hechos, a tu nombre. Lo siguiente: que avisen en la campana y en el celular cuando llega la hora.

**Etiquetas para organizar a tus clientes**
- Crea las etiquetas que quieras, con su color («Mayorista», «VIP», «Llamar el lunes»), y pónselas a cada cliente desde su ficha.
- Se ven en la tarjeta del tablero, en la lista y en la ficha, y el tablero y la lista se filtran por una.
- Con el botón **Etiquetas** las administras: ves cuántos clientes tiene cada una, les cambias el color o el nombre y las borras
  (sus clientes solo la pierden). No se pueden repetir: «VIP» y «vip» son la misma.
- Todo tu equipo las usa y las crea; renombrarlas y borrarlas es del dueño o de un administrador. Lo siguiente: recordatorios.

**La ficha de cada cliente**
- Toca a un cliente en el tablero o en la lista y se abre su ficha, con todo lo suyo en un solo lugar.
- **Valor:** cuánto vale lo que podría comprar. Aparece en su tarjeta, suma en su columna y arriba ves cuánto tienes **por cerrar**.
- **Responsable:** asignas el cliente a alguien de tu equipo; sus iniciales salen en la tarjeta.
- **Notas:** lo que tu equipo quiera recordar de ese cliente. El cliente nunca las ve.
- **Historial:** cada cambio de etapa, de valor y de responsable, con quién lo hizo: el asistente, alguien de tu equipo o una venta.
- También están sus compras y el botón para pasarlo a la etapa siguiente. Lo siguiente: etiquetas.

**Clientes ahora es un tablero, como el de un CRM**
- Cada etapa es una columna y cada cliente una tarjeta. El asistente lo sigue avanzando solo; tú lo mueves cuando quieras:
  arrastrando la tarjeta o con «Mover a…» (también en el celular).
- **No compró:** saca del embudo a quien ya no va a comprar y anota por qué. Deja de recibir seguimientos automáticos y, si vuelve a
  escribir con interés, regresa solo.
- A «Cliente» se pasa registrando la venta, para que el tablero y Ventas digan lo mismo.
- Arriba, los números del embudo: cuántos siguen abiertos, lo vendido en 30 días, de cada 100 cuántos compran y cuánto tardan. Cada
  columna dice qué parte avanza a la siguiente etapa.
- La lista de siempre sigue ahí, con el botón **Lista**. Lo siguiente: la ficha de cada cliente, con notas, responsable e historial.

**La plataforma ahora se llama Merceam**
- El panel, la pantalla de entrada, las invitaciones al equipo, los correos y avisos, el Centro de ayuda y la app instalada en el
  celular muestran el nombre nuevo. El logo es el mismo.
- El motor de ventas conserva su nombre de siempre, **AI Sales Engine**: Merceam es la plataforma y AI Sales Engine la mueve por dentro.
- La dirección del panel pasa a `merceam.vercel.app` y la del motor (la API del asistente) a `merceam-api.vercel.app`. Quien tenga
  encendidas las notificaciones del navegador debe encenderlas otra vez en la dirección nueva, y los agentes conectados (Claude,
  ChatGPT, Cursor) se conectan de nuevo con ella.
- En el menú, el nombre se ve más grande y completo: la ayuda de la pantalla y la campana de avisos pasan abajo, al lado de tu
  nombre y tu correo.
- La pantalla de entrada es nueva: a un lado, un chat de ejemplo muestra al asistente atendiendo y cerrando una venta; al otro,
  solo el formulario, con campos y botón más grandes. El logo y el nombre aparecen una sola vez.

**Seguimiento automático: le volvemos a escribir a quien dejó de responder**
- En Mensajes → **Seguimiento** lo enciendes y ya viene armado con tres mensajes recomendados (a la hora, al día siguiente y a los
  3 días), con tu trato y con o sin emojis. Si quieres, cambias los textos y los tiempos, agregas hasta 5 o eliges que salgan solo
  en tu horario.
- Se detiene solo cuando el cliente responde, compra o avisa un pago, pide una persona, tu equipo lo atiende o dice que no le
  interesa: antes de cada mensaje, la IA lee el final del chat.
- Nunca salen dos seguidos ni mensajes viejos: al encenderlo no se les escribe a quienes dejaron de responder hace semanas.
- En el chat ves cada seguimiento marcado y lo detienes (o lo reanudas) para ese cliente. Funciona por WhatsApp y Telegram.

## 27 de noviembre de 2026

**«Confirmar pago»: tu cliente se entera de que su pago llegó**
- Antes escribías en el panel el mensaje de pago confirmado, pero nunca se enviaba. Ahora, cuando verificas el pago, tocas
  **Confirmar pago** en el chat (o en Ventas → Pagos por verificar) y tu cliente recibe ese mensaje. Si no escribiste uno, le llega
  uno corto de la plataforma, con tu trato y con o sin emojis.
- En el mismo paso el chat queda atendido, el cliente pasa a «Cliente» y, si anotas lo que compró y el valor, la venta queda en Ventas.
- La IA sabe que el pago quedó confirmado: si el cliente vuelve a escribir, ya no le dice que el equipo lo está verificando.
- El mensaje sale una sola vez, aunque toquen dos veces o lo confirmen dos personas a la vez. Si WhatsApp no lo entrega, el panel lo
  dice y el pago sigue por confirmar.

## 26 de noviembre de 2026

**Tu saludo de bienvenida le llega a quien salude, venga de donde venga**
- Antes el asistente reconocía solo saludos de Colombia («hola», «buenas», «qué más»). Un «qué onda», un «buen día, ¿cómo están?» o un
  👋 no recibían tu bienvenida. Ahora lo entiende la IA, en cualquier forma de saludar.
- Si el cliente saluda y además pregunta algo («hola, ¿cuánto cuesta?»), le responde el asistente, como siempre.
- Medido con 36 tipos de primer mensaje, cinco veces cada uno: acierta 178 de 180 (la lista de antes, 24 de 36), y nunca le mandó el
  saludo fijo a quien preguntaba algo.

## 25 de noviembre de 2026

**Si tu negocio no usa emojis, el mensaje de pago tampoco**
- Aunque eligieras «sin emojis», el mensaje con los datos de pago salía con 💳 y ✅. Ahora sale sin ellos, también el del efectivo, y
  la vista previa del panel lo muestra igual.
- Si escribiste tu propio mensaje de pago, sale tal cual. Si usas emojis o no elegiste, nada cambia.

## 24 de noviembre de 2026

**«Probar asistente» ya no confunde tu saludo con una falla**
- Cuando probabas tu asistente y respondía con tu saludo de bienvenida, debajo salía «Respondió sin la IA: revisa la clave o el
  modelo», como si algo estuviera mal. Ahora dice «Es el saludo de tu negocio». El aviso de la clave solo sale cuando la IA de
  verdad no pudo responder.
- La API para otras plataformas tampoco marca tu saludo como respaldo (`fallback`).

## 20 de noviembre de 2026

**Tu asistente habla por sí mismo, sin frases de rescate**
- Antes, si el asistente decía ciertas frases («no puedo enviarte los datos», «no recibimos Nequi»), la plataforma cambiaba su
  mensaje por uno fijo. Ahora el asistente responde con sus propias palabras: corregimos de raíz la indicación que lo llevaba a decir
  «no puedo enviar los datos», en vez de taparlo.
- Medido con 60 conversaciones de pago: 0 veces dijo algo falso sobre los pagos.
- Si el asistente no puede responder, tu cliente recibe tu mensaje de respaldo (Mensajes → «Si el asistente no puede responder»), no
  «Hubo un problema procesando el mensaje».

**Los mensajes automáticos también tratan de usted si tu negocio lo hace**
- Si en el panel elegiste tratar a los clientes de usted, los mensajes que envía la plataforma también van de usted: el de los datos
  de pago («Cuando pague, envíeme aquí la captura…»), el del efectivo, «¿Quiere que le envíe los datos?», «Una persona de nuestro
  equipo le responderá…», el aviso fuera del horario, la disculpa cuando la IA retoma el chat y el mensaje si la IA no puede
  responder.
- Las vistas previas y los ejemplos del panel también se muestran de usted, como le llegan a tu cliente.
- Si escribiste tus propios mensajes, salen tal cual. Si tu negocio trata de tú o de forma neutral, nada cambia.

## 19 de noviembre de 2026

**Si tu negocio trata a los clientes de usted, el asistente ya no los tutea**
- Antes, aunque eligieras «formal» en el panel, el asistente se pasaba al tú en muchas respuestas («¿Te gustaría avanzar?», «tu
  nombre»), sobre todo al usar tus frases de ejemplo escritas de tú o cuando el cliente le hablaba de tú.
- Ahora trata de usted en todo el mensaje, también tus frases de ejemplo. Medido con 30 conversaciones: ninguna con «te» o «tu»
  (antes, 10 de 18), y 28 enteras de usted.
- Si tu negocio trata de tú o de forma neutral, nada cambia.

**El asistente entiende cuando tu cliente se decide a comprar**
- Si tu cliente dice «me convence, lo quiero» o «listo, avancemos», el asistente lo toma como lo que es: que quiere comprar. Antes lo
  confundía con que pedía los datos para pagar y le preguntaba con qué medio iba a pagar, aunque tu negocio cerrara tomando sus
  datos para llamarlo.
- Si le ofreció enviarle los datos para pagar y el cliente responde «sí, lo quiero», se los envía, como siempre.
- Medido con 32 tipos de mensaje, cinco veces cada uno: entiende bien 156 de 160 (antes, 69 %).

## 18 de noviembre de 2026

**El asistente recuerda lo que tu cliente ya le dijo, aunque el chat sea largo**
- Si tu cliente da su nombre, su teléfono o cuenta qué negocio tiene, el asistente lo anota y lo tiene presente en cada mensaje.
  Ya no se lo vuelve a pedir veinte mensajes después.
- Cuida los datos: del teléfono, el correo, el documento o la dirección solo recuerda que el cliente ya los dio, no el número. Se
  borran con la conversación.
- Medido con 90 conversaciones de venta: 0 veces pidió algo que el cliente ya había dado (antes, 2).

**Un motor más limpio y seguro, sin cambiar lo que responde tu asistente**
- Retiramos el resto del sistema anterior: un webhook de WhatsApp de Meta que no atendía a ningún negocio, una ruta de pruebas
  que estaba apagada, el sistema de cuentas viejo con su clave por defecto y una base de datos de prueba que seguía guardada en el
  código. Menos puertas abiertas y menos código que mantener.
- Tu asistente responde exactamente igual: lo comprobamos con los 9 negocios de ejemplo, mensaje por mensaje, y por el mismo
  camino que siguen los mensajes de WhatsApp.

## 15 de noviembre de 2026

**El asistente ya no le pide al cliente lo que ya le dijo**
- Si tu cliente escribe «soy Laura» o te da su teléfono, el asistente lo usa y pide solo lo que falta para cerrar. Antes, justo al
  enviarle los datos de pago, le pedía otra vez el nombre o el teléfono.
- Medido con 90 conversaciones de venta: los casos bajaron de 7 a 2, y seguimos con los que quedan.

**El asistente espera a que tu cliente termine de escribir**
- Por WhatsApp la gente escribe en varios mensajes seguidos («Hola»… «quiero el plan»… «¿cuánto vale?»). Antes el asistente
  contestaba cada uno por separado y a medias. Ahora espera unos segundos, lee todo junto y **responde una sola vez**.
- Lo eliges en Asistente IA → Cómo atiende → **Esperar antes de responder**: 8 segundos (recomendado), al instante, 3, 5, 12 o 20.
- Si el cliente no para de escribir, a los 30 segundos le responde igual. Las fotos y los audios se entienden mientras espera.
- Funciona en WhatsApp y Telegram. En Probar sigue respondiendo al instante.

**Menos mensajes sin respuesta**
- Si la conexión con el proveedor de IA se corta, se demora o está ocupado por un momento, el asistente lo intenta otra vez antes de
  rendirse. Antes, tu cliente recibía «En este momento no puedo responderte» a la primera (pasó en 2 de 123 respuestas).
- Si aun así no responde, queda anotada la causa para revisarla.

## 14 de noviembre de 2026

**Los modelos más nuevos ya responden bien**
- Si elegiste un modelo que «razona» antes de responder (por ejemplo Claude Haiku 5.5, GPT-6 Luna o DeepSeek V4.1 Flash), muchos
  mensajes le llegaban a tu cliente como «Hubo un problema procesando el mensaje». Ahora el asistente le pide al modelo responder
  directo: contesta completo, más rápido y gastando menos de tu clave.
- Comparamos seis modelos con las mismas conversaciones de venta y el modelo recomendado sigue siendo `openai/gpt-4o-mini`: fue el
  que menos se equivocó con los pagos y con el paso de los chats a tu equipo.

**Tu equipo sabe qué necesita el cliente antes de abrir el chat**
- Cuando un chat pasa a tu equipo, el asistente deja una **nota corta**: quién es el cliente, qué le interesaba y qué pidió. Antes
  el aviso solo traía su último mensaje («No, gracias, prefiero una persona»), que no decía de qué se trataba.
- La ves en la campana, en el correo, en la notificación del celular y arriba del chat en Conversaciones.
- Sale solo de lo que dijo el cliente y nunca lleva datos de pago. Usa tu clave de IA una vez por cada chat que pasa a tu equipo.
- El resumen de las conversaciones largas ya no agrega cosas que el cliente no dijo ni afirma que le falta un dato que dio después.

**Tú decides cuándo el asistente pasa un chat a tu equipo**
- Nueva tarjeta **Cuándo pasar a una persona** en Asistente IA → Cómo atiende. Si el cliente pide una persona, puedes elegir que el
  asistente **primero le ofrezca ayuda** (una vez, sin insistir) y lo pase si insiste.
- **Temas que siempre atiende tu equipo** (por ejemplo, reembolsos) y **temas que resuelve el asistente** (por ejemplo, precios).
- **Pasar el chat si la conversación se estanca:** cuando el cliente repite lo mismo o se frustra.
- En la bandeja ves el motivo: «Un tema que atiende tu equipo» o «No logra avanzar con el asistente».
- Si no cambias nada, el asistente se comporta igual que antes. Los reclamos y los pagos avisados siempre pasan a tu equipo.
- Si el asistente decide pasar un chat y no escribe el mensaje, el chat pasa igual y el cliente recibe «Claro, te paso con una
  persona del equipo por este mismo chat.» (antes recibía «Hubo un problema procesando el mensaje»).

## 13 de noviembre de 2026

**El asistente decide cuándo pasar un chat a tu equipo**
- Antes, si el asistente escribía «te paso con el equipo», el chat pasaba a tu equipo aunque solo estuviera explicando un paso de
  después. Ahora lo decide el asistente entendiendo la conversación: cuando el cliente pide una persona, reclama o avisa que ya pagó.
- Si el asistente le dice al cliente que lo pasa con el equipo sin decidirlo, se le pide que responda otra vez: lo que le dice al
  cliente y lo que hace siempre coinciden.

**Tu asistente ya no olvida en conversaciones largas**
- Pasados 40 mensajes, el asistente leía el principio de la conversación y no lo último. Ahora siempre lee lo más reciente, y lo de
  antes le llega **resumido** (quién es el cliente, qué necesita, qué eligió). El resumen lo escribe la IA cada 10 mensajes en chats
  largos: suma un poco al consumo de tu clave solo en esas conversaciones.
- Lo que recuerda de cada cliente (el medio de pago que eligió, si ya pagó, en qué paso va) es el mismo en todos los servidores: antes
  uno podía responder con un dato viejo. Y responde más rápido: cada mensaje consulta la memoria 5 veces en lugar de unas 50.
- Si el asistente llegara a escribir el teléfono del cliente como si fuera tu Nequi («Nequi: 315…»), ese número no sale: va el tuyo.

**Pagos: tu asistente habla como un asesor, no como un contestador**
- Cuando el cliente necesita los datos para pagar, el asistente **le habla y debajo van los datos**. Antes llegaba solo la plantilla,
  sin una palabra.
- **Preguntar no es pedir la cuenta:** «¿puedo transferir?» o «¿y Nequi no?» se responden y el asistente sigue guiando. Los datos
  llegan cuando el cliente los pide, dice con qué medio paga o acepta que se los envíen.
- **No se repiten solos:** si el cliente no entendió algo («¿cómo así?»), el asistente le explica en vez de mandar el bloque otra vez.
- Qué pide el cliente ahora **lo entiende la IA** con una segunda mirada corta por mensaje (antes eran reglas de palabras que se
  equivocaban). Suma al consumo de tu clave cerca de un 30 % (medido con la IA real).
- Más cuidados: si la IA escribe un número de pago por su cuenta, no sale (va el real); si dice que no puede enviar los datos o que
  no recibes un medio que sí tienes, se le pide otra respuesta antes de contestarle al cliente. Los datos nunca llegan solos.
- Antes de publicar un cambio al asistente, ahora debe pasar una prueba con la IA real: tu chat de producción y frases de
  clientes, revisadas con 12 reglas de pasa o no pasa.

## 12 de noviembre de 2026

**«Probar asistente» ya no olvida la conversación**
- La conversación de prueba se guarda en la base, como las de WhatsApp: en la nube, un mensaje puede atenderlo otro servidor y antes
  el asistente a veces empezaba de cero. Cada prueba es su propio contacto y nunca se mezcla con un cliente real.
- Al borrar las pruebas (o un chat de prueba) también se borra lo que el asistente recordaba de ellas. Si no se puede, no se borra nada.

**Respuestas rápidas con fotos y PDF**
- Una respuesta rápida ahora puede llevar **archivos**: fotos, PDF, documentos, videos o audios de hasta 4 MB, cada uno con un texto
  opcional (también con `{nombre}`). Por ejemplo, `/catalogo` envía un saludo y después el PDF del catálogo.
- El archivo se sube una vez en el editor (**Agregar archivo**) y queda guardado con el negocio. En el chat sale desde el servidor,
  sin volver a subirlo, en orden con los textos.

**Fotos y documentos desde el chat**
- En Conversaciones, el **clip** junto al cuadro de texto adjunta un archivo: fotos, PDF, Word, Excel, PowerPoint, texto, videos MP4 y
  audios, de hasta 4 MB. También se puede pegar una imagen. Lo que escribas sale como su texto.
- El archivo queda en el chat como los que mandan los clientes, y la IA se pausa como cuando respondes tú. Si no sale, vuelve al
  cuadro para intentarlo de nuevo. Lo que no se puede enviar se explica antes de subirlo.

**Tu equipo, con roles**
- Nuevo **Configuración → Equipo**: invitas a las personas que atienden o administran tu negocio con un **enlace** que se copia o
  se envía por WhatsApp. Vence en 7 días, se puede renovar o retirar, y solo funciona con la cuenta del correo invitado.
- Tres roles: **Dueño** (todo), **Administrador** (todo menos eliminar el negocio y tocar a los dueños) y **Asesor** (atiende chats,
  clientes y ventas y usa las respuestas rápidas). El negocio siempre conserva al menos un dueño.
- El asesor ve un panel a su medida: su inicio con lo del día y un menú sin la configuración ni los reportes. Si abre una pantalla
  que su rol no permite, el panel le dice por qué.
- Un agente de IA solo trabaja en los negocios donde quien lo conectó es dueño o administrador.

**Centro de ayuda**
- Nuevo **Ayuda** en el menú, junto a Configuración: un buscador, **Empieza aquí** con los cinco pasos para dejar al asistente
  vendiendo (se marcan solos cuando los haces) y 41 artículos en 10 temas que siguen el menú del panel.
- **La ayuda de cada pantalla:** el botón **?** junto a la campana abre al lado los artículos de la pantalla en la que estás, sin
  salir de ella, con el que la explica primero.
- Cada artículo dice cuánto se tarda en leer, tiene su índice, los relacionados y enlaces que te llevan directo a la pantalla.
- Los agentes de IA conectados por MCP leen la misma ayuda (`search_help` y `read_help_article`) para explicarte cómo se hace algo.

**Respuestas rápidas**
- Nuevo **Configuración → Respuestas rápidas** (ya no dice «Pronto»): guarda los mensajes que tu equipo envía todos los días con un
  atajo, una categoría y de 1 a 10 mensajes, con vista previa de cómo le llegan al cliente.
- En el chat, escribe **/** o toca el rayo ⚡ para buscarlas por atajo, categoría o texto. Un solo mensaje queda en el cuadro para
  retocarlo; varios salen en orden. `{nombre}` se cambia por el nombre del cliente.
- Cada respuesta dice cuántas veces se usó, y las más usadas salen primero. Se pueden duplicar, editar y borrar.

**El asistente cierra como elegiste**
- La **estrategia de cierre** ya cambia lo que hace el asistente:
  - **Confirmar la compra**: confirma con el cliente lo que decidió, le pide los datos y le dice cómo pagar.
  - **Enviar el pago**: apenas decide, lo lleva directo a pagar, sin más preguntas.
  - **Capturar datos**: le pide sus datos para que tu equipo lo contacte y no le cobra, salvo que el cliente lo pida.
  - **Agendar**: igual que antes.
- **Qué vendes** reemplaza a «Tipo de negocio» y «Modo catálogo», que decían lo mismo. Eliges entre Productos, Planes o
  suscripción, Servicios y Servicios con cita, y el asistente vende según eso.
- Si tu negocio tenía «Checkout», ahora aparece como Productos, y si tenía «Proceso», como Servicios. Para guiar al cliente paso a
  paso sigue estando «Guiar paso a paso».

**Eliminar un negocio, también en la nube**
- Nuevo **Configuración → Eliminar negocio** (y «Eliminar» en Tus negocios). Te dice qué se pierde y pide escribir el nombre del
  negocio. Solo el dueño puede hacerlo.
- Se borra todo lo suyo: configuración y versiones, datos de pago, conversaciones con fotos y audios, clientes, ventas, reportes,
  claves de API y ajustes. WhatsApp se desconecta y el asistente olvida a sus clientes.
- Si WhatsApp no se puede desconectar, no se borra nada y te avisa para intentarlo de nuevo.

**Conecta Claude y ChatGPT sin copiar claves**
- En Claude (web y app) o ChatGPT agregas un conector personalizado con la dirección del servidor. Se abre la plataforma, inicias
  sesión, eliges a qué negocios entra y qué puede hacer, y pulsas «Autorizar».
- Si no habías iniciado sesión, al entrar vuelves directo a la autorización.
- La conexión aparece en **Claves de API** con el nombre del agente y la etiqueta «Inicio de sesión». Revocarla lo desconecta al
  instante.
- Autorizar de nuevo el mismo agente reemplaza sus permisos, no suma conexiones.
- Por seguridad: el acceso del agente dura una hora y se renueva solo; ningún código ni token queda guardado tal cual.

**Agentes de IA en el día a día: conversaciones, ventas y atención humana**
- Con los nuevos permisos **Conversaciones**, **Clientes y ventas** y **Atención humana**, el agente te ayuda en la operación:
  - te dice quién espera a una persona, lee los chats y les responde a tus clientes por WhatsApp cuando apruebas el texto (la IA
    se pausa en ese chat); pausa o reanuda la IA y marca chats atendidos;
  - ve tus clientes, ventas y reportes, y registra o anula ventas que confirmas (quedan a su nombre);
  - ajusta el horario del equipo, los tiempos y a dónde llegan los avisos;
  - ve el modelo de IA y lo que ha gastado, y lo cambia si lo apruebas.
- **Los datos de pago siguen sin salir:** en los chats que lee el agente aparecen como «[dato de pago]», también los de versiones
  anteriores.
- Una clave de «algunos negocios» solo ve los chats de esos negocios, aunque tengas otros.
- Lo que escriben tus clientes nunca es una orden para el agente: así se lo indica la plataforma.

**Agentes de IA, más precisos** (después de probarlos en producción)
- El agente ve los mismos avisos que tú en el panel («sin dirección», «cuéntale qué problemas resuelves»...), con el campo donde
  corregir.
- Los errores de formato dicen qué usar: «solo letras sin tildes ni ñ, números y guion bajo (por ejemplo, pan_aliniado)».
- La primera versión de un negocio queda a nombre de quien lo creó, persona o agente.
- En «Publicar» ya no se repiten los avisos que la pantalla muestra en vivo.

**Agentes de IA (MCP): que Claude monte tu negocio**
- Nueva pantalla **Integraciones → Agentes de IA (MCP)**: la dirección del servidor y lo que se pega en Claude Code, Cursor (y
  Claude Desktop, Windsurf, Gemini CLI) y n8n.
- Un agente puede crear negocios y montar su configuración completa: negocio, productos y precios, pagos, preguntas frecuentes y
  mensajes. Revisa lo que falta y lo que cambia, prueba el asistente y publica solo cuando confirmas.
- **Claves de la cuenta:** al crear una clave eliges qué puede hacer por área, a qué negocios entra (este, todos o algunos) y cuándo
  vence. Los datos de pago se pueden escribir, nunca leer.
- Cada cliente, lo suyo: una clave solo llega a los negocios de quien la creó.

**Configuración del negocio y Mi cuenta, separadas**
- **Configuración** es solo del negocio y va fija abajo en el menú de la izquierda.
- **Mi cuenta**, en el menú de tu foto, es tuya: Mi perfil, **Seguridad** (cambiar tu contraseña y cerrar tu sesión en los demás
  equipos) y **Notificaciones** (los avisos en este celular o computador).
- Las direcciones de antes siguen funcionando.

**Siempre sabes si falta publicar**
- Arriba del editor del asistente: «Cambios sin publicar» en ámbar con el botón **Revisar y publicar**, o «Publicado · es lo que
  responde a tus clientes». Un punto ámbar en «Asistente IA» mientras haya cambios guardados sin publicar.
- Antes de publicar ves **lo que cambia**, sección por sección y con cómo estaba y cómo queda. Los datos de pago nunca se muestran.
- Compara lo que de verdad cambió: guardar sin tocar nada no deja cambios pendientes.
- «Probar» avisa cuando pruebas cambios que tus clientes todavía no ven.

**Integraciones, un catálogo como el de las plataformas grandes**
- Pestañas por categoría, buscador y tarjetas en Activas, Disponibles y Próximamente.
- Los logos reales de cada servicio (OpenRouter, OpenAI, Anthropic, Gemini, MCP), también en Configuración → Inteligencia artificial.

**La API del asistente, más clara**
- Una sola página para cualquier plataforma: arriba dice si alguna ya la está usando, cómo funciona y tus datos de conexión.
- Guías en pestañas: **Leona** (probada con un flujo real que conversa), **Otra plataforma** y **Desarrolladores** (cURL, JavaScript y
  Python).
- Si una plataforma manda una variable sin reemplazar (como «{nombre}»), la API la rechaza y dice cuál fue: tus clientes no se mezclan
  en un mismo chat ni se gasta la IA.

**Integraciones: tu asistente en otras plataformas**
- Nueva sección **Integraciones** en el menú.
- **API del asistente:** conecta tu asistente a Leona, a tu página web o a cualquier sistema. Te dan el mensaje del cliente y
  reciben la respuesta: el mismo asistente de WhatsApp, con la memoria de cada cliente y el paso a una persona.
- Paso a paso para Leona, con todo listo para copiar, y una prueba desde el panel.
- **Claves de API:** se muestran una sola vez, se ve cuándo se usó cada una y se revocan en un clic.
- Los chats que llegan así aparecen en Conversaciones con el canal «API» y cuentan en Clientes y Reportes.
- El Inicio muestra el estado real de tu WhatsApp, en lugar de «Sin conectar» siempre.

**Variables ordenadas**
- Una plantilla con todas las variables, separadas entre este equipo y Vercel, y una guía para desplegar en otra parte.

## 11 de noviembre de 2026

**Configuración, más clara y completa**
- «Ajustes» ahora es **Configuración**, con su propio menú: Mi perfil, Inteligencia artificial, Atención humana, y Respuestas rápidas y
  Pagos y suscripciones marcadas «Próximamente». También se abre desde el menú de tu cuenta.
- Inteligencia artificial por partes: el proveedor (OpenRouter; OpenAI, Anthropic y Google, pronto), la clave guardada oculta con
  «Cambiar clave», y el modelo en una lista desplegable con buscador.

**Atención humana completa** (Fase 3)
- Configuración → Atención humana: el horario del equipo (el de tu negocio, otro o siempre), lo que se le dice al cliente y cuándo retoma
  la IA. Se aplica al instante.
- Dentro del horario, el cliente sabe cuánto tarda tu equipo; fuera de él, la IA sigue ayudando y le dice cuándo lo atienden.
- Si nadie responde a tiempo, la IA retoma el chat, pide disculpas, responde lo pendiente y te avisa. Ningún cliente queda esperando.
- Avisos por correo y notificaciones en el celular y el computador, además de la campana. El panel se puede instalar en el celular.
- Lo que respondes desde el celular del negocio aparece en el chat y pausa la IA.
- Dos mensajes nuevos en Asistente IA → Mensajes: «Fuera del horario del equipo» y «Cuando la IA retoma el chat».

**Una sola puerta de entrada**
- La dirección del motor y el enlace del repositorio en GitHub llevan al panel, que es donde se trabaja.

**Eliminar chats y clientes** (Fase 1)
- Botón de papelera en cada chat y en cada cliente, con confirmación que explica qué se borra.
- Se borra todo: mensajes, fotos, audios, avisos y lo que el asistente recordaba de ese cliente (si vuelve a escribir, empieza de
  cero). Las ventas registradas se conservan.
- «Borrar pruebas» elimina de una vez los chats de «Probar asistente».
- Los diálogos (registrar venta, eliminar) cubren toda la página, también el menú.

**El panel en el celular**
- Barra superior con el menú ☰, el nombre de la sección y los avisos siempre a mano.
- Menú que se desliza desde la izquierda, se cierra al tocar afuera, con la X, deslizándolo o al elegir una opción.
- El chat abierto se ve como en WhatsApp, las pestañas del asistente se deslizan de lado y ninguna pantalla se sale del ancho.

**Más claro de un vistazo**
- El canal del cliente es un ícono pequeño sobre su foto; las etiquetas quedan solo para lo importante («Tiene un reclamo»).
- Cada contacto tiene su color; el verde queda para «sin leer» y para WhatsApp.
- Con el asistente ya configurado, el Inicio pone primero las cifras del día y el progreso queda en una franja pequeña.
- El menú del perfil y la campana se abren por encima del contenido.

**Limpieza**
- Se retiraron los YAML de los negocios: los 9 negocios de ejemplo ahora son JSON y responden exactamente igual (comprobado con el
  laboratorio de regresión).
- Se retiraron la API de administración vieja, el *polling* de Telegram de un solo negocio y archivos sin uso.

**Clientes, ventas y reportes de verdad**
- Cada cliente con su etapa, que avanza sola: nuevo, interesado, listo para comprar, pagó (por verificar) y cliente.
- Registrar y anular ventas, pagos por verificar, embudo, actividad por día, quién respondió y costo de la IA.

**Conversaciones en vivo**
- Escribiendo…, chulos de enviado, entregado y leído, no leídos, y responder desde el panel.
- Fotos y notas de voz que la IA entiende (por ejemplo, un comprobante de pago).
- Cuando el cliente pide una persona, reclama o reporta un pago, la IA se pausa y el equipo recibe un aviso.
- Conversaciones a pantalla completa y configuración organizada por secciones, sin huecos.

## 10 de noviembre de 2026

**WhatsApp por código QR**
- El negocio toca «Conectar WhatsApp» y escanea un QR; el servidor y los tokens de uazapi los pone la plataforma.
- Las migraciones de la base se aplican solas en cada despliegue.

**Un asistente que vende mejor**
- Todo lo que el panel deja configurar llega al asistente, cada campo con su prueba.
- Prompt por capas: la forma de vender de la plataforma, un manual por tipo de negocio y el negocio completo en cada mensaje.
- Medido con la IA real en el laboratorio de calidad: mejores respuestas, menos inventos y menos tokens.
- Una sola llamada a la IA por mensaje.

**Cuentas y nube**
- Cuentas con Neon Auth: cada usuario solo ve y modifica sus negocios.
- Cada negocio responde con su propia clave de IA y elige su modelo de la lista de OpenRouter, con su costo aproximado.
- Consumo de la IA por negocio y por día, y límites de uso para evitar abusos.
- Crear un negocio de cero o con una plantilla (restaurante, tienda, agencia, escuela, servicios con cita, software).
- Avisos al equipo con la campana de notificaciones.
- El motor responde solo con lo publicado en el panel y tiene un mensaje de respaldo editable.

**Seguridad**
- Ningún registro guarda tokens ni mensajes de clientes.
- El webhook de la API de Meta solo acepta lo que firmó Meta.

## 6 de noviembre de 2026

- Contrato de configuración de los negocios (BusinessConfig v1): validado, con versiones, borrador, publicar y volver atrás.
- Panel de administración en este equipo, con datos de pago cifrados.
- Funciona igual en Windows y en macOS.

## 28 y 30 de octubre de 2026

- La plataforma deja de manejar suscripciones y planes propios: cada negocio vende lo suyo.
- Pruebas automáticas estables y dependencias sin vulnerabilidades conocidas.
- Primera base del panel de administración.

## Mayo y junio de 2026

- Primera versión del motor: atención por WhatsApp con contexto, memoria de cada cliente y criterio comercial.
- Laboratorio de precios y de regresión, y la suite de pruebas del comportamiento de ventas.
