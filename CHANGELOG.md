# Cambios

Lo que cambió en AI Sales Engine, de lo más reciente a lo más antiguo. Cada entrada dice qué gana el negocio; el detalle técnico
está en el historial de git y en `docs/plan-v1.md`.

## 12 de noviembre de 2026

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
