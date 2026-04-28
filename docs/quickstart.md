# Quickstart

## ¿Qué es esto?

Es un sistema SaaS de ventas conversacionales por WhatsApp.
No responde por responder.
Toma el mensaje, entiende el contexto comercial del negocio y mueve la conversación hacia una acción concreta.
Está diseñado para vender, no para simular atención.

## Diferencial

- no es automatización genérica
- vende
- sigue contexto

Responde con criterio comercial, no con plantillas decoradas.
Conecta dolor con impacto, impacto con dinero y dinero con decisión.
Su salida no busca sonar tecnológica. Busca cerrar, avanzar o activar.

## Ejecución

Entorno:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Dependencias:

```powershell
Set-Location project
pip install -r requirements.txt
```

Levantar el sistema:

```powershell
uvicorn app.main:app --reload
```

Simular conversación:

```text
POST /api/v1/simulate
```

Header:

```text
X-Tenant-Slug: asesor_ai_prod
```

JSON:

```json
{
  "user_message": "tengo muchos mensajes",
  "user_id": "demo_1"
}
```

## Resultado

- naturalidad
- guía
- cierre

## Pruebas

- tenant: asesor_ai_prod

Mensajes dirigidos:

- como funciona
- esta caro
- quiero empezar

Lectura esperada:

- "tengo muchos mensajes": dolor operativo y costo de oportunidad
- "como funciona": explicación breve con dirección comercial
- "esta caro": defensa de valor con conexión a dinero
- "quiero empezar": avance directo a activación o compra

## Siguiente paso

- README + docs + WhatsApp