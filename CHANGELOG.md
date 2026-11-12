# Cambios

Lo que cambió en AI Sales Engine, de lo más reciente a lo más antiguo. Cada entrada dice qué gana el negocio; el detalle técnico
está en el historial de git y en `docs/plan-v1.md`.

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
