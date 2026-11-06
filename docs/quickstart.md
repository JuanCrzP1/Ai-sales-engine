# Quickstart

## ¿Qué es esto?

Es un motor de ventas conversacionales por WhatsApp. Las cuentas, suscripciones y facturación los gestiona la plataforma externa que lo integra.
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

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r project/requirements.txt
cd project
uvicorn app.main:app --reload
```

**macOS / Linux:**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r project/requirements.txt
cd project
uvicorn app.main:app --reload
```

### Simular una conversación

`POST /api/v1/simulate` es una ruta de pruebas internas. Está apagada por defecto y responde 404. Aunque se habilite, exige un
token de administrador que hoy ningún entorno puede emitir, porque la autenticación definitiva queda para la fase de nube, así
que por ahora no se puede usar de extremo a extremo. El estado completo está en `docs/operations.md`.

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