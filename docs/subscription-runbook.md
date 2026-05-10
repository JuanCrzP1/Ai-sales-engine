# Runbook Operativo de Suscripciones

**Versión:** 1.1  
**Audience:** Operador (tú)  
**Tenant de referencia:** `asesor_ai_prod`

---

## Propósito

Este manual permite administrar manualmente el ciclo de vida de las suscripciones. El modelo es simple:

1. El cliente transfiere el pago.
2. Tú verificas la transferencia.
3. Ejecutas el SQL correspondiente.
4. El sistema habilita el acceso automáticamente.

Los ejemplos usan `asesor_ai_prod` como tenant de referencia. Están listos para copiar y pegar.

---

## Paso 0 — Obtener el UUID de `asesor_ai_prod`

Ejecutar esto primero. El valor de `id` es lo que debes usar en todos los comandos como `<UUID_DE_ASESOR_AI_PROD>`:

```sql
SELECT id, name, slug, status
FROM tenants
WHERE slug = 'asesor_ai_prod';
```

---

## 1. Crear una suscripción nueva (plan `starter`)

Usar cuando el tenant no tiene fila en `subscriptions` todavía:

```sql
INSERT INTO subscriptions (
    tenant_id,
    plan_code,
    status,
    current_period_end
)
VALUES (
    '<UUID_DE_ASESOR_AI_PROD>',
    'starter',
    'active',
    now() + interval '30 days'
);
```

---

## 2. Renovar por 30 días

Usar cuando el cliente paga la renovación:

```sql
UPDATE subscriptions
SET
    status = 'active',
    current_period_end = now() + interval '30 days'
WHERE tenant_id = '<UUID_DE_ASESOR_AI_PROD>';
```

---

## 3. Cambiar a plan `pro`

```sql
UPDATE subscriptions
SET plan_code = 'pro'
WHERE tenant_id = '<UUID_DE_ASESOR_AI_PROD>';
```

El nuevo límite se aplica en la siguiente solicitud del tenant.

---

## 4. Cambiar a plan `enterprise`

```sql
UPDATE subscriptions
SET plan_code = 'enterprise'
WHERE tenant_id = '<UUID_DE_ASESOR_AI_PROD>';
```

Sin límite de mensajes.

---

## 5. Suspender temporalmente

Usar cuando el pago está pendiente y necesitas pausar el acceso sin cancelar:

```sql
UPDATE subscriptions
SET status = 'suspended'
WHERE tenant_id = '<UUID_DE_ASESOR_AI_PROD>';
```

El bloqueo es inmediato. El historial y la configuración se conservan.

---

## 6. Cancelar el servicio

```sql
UPDATE subscriptions
SET status = 'canceled'
WHERE tenant_id = '<UUID_DE_ASESOR_AI_PROD>';
```

---

## 7. Reactivar el servicio

Usar cuando un tenant suspendido o cancelado retoma tras verificar el pago:

```sql
UPDATE subscriptions
SET
    status = 'active',
    current_period_end = now() + interval '30 days'
WHERE tenant_id = '<UUID_DE_ASESOR_AI_PROD>';
```

---

## 8. Consultar uso de los últimos 30 días

```sql
SELECT *
FROM usage_daily
WHERE tenant_id = '<UUID_DE_ASESOR_AI_PROD>'
ORDER BY date DESC
LIMIT 30;
```

---

## 9. Verificar la suscripción actual

```sql
SELECT *
FROM subscriptions
WHERE tenant_id = '<UUID_DE_ASESOR_AI_PROD>'
ORDER BY created_at DESC
LIMIT 1;
```

Estado esperado para acceso activo:
- `status` = `active` o `trialing`
- `plan_code` = el plan contratado
- `current_period_end` > hoy

---

## Planes disponibles

| Plan | Límite de mensajes |
|---|---|
| `starter` | 2.000 |
| `pro` | 10.000 |
| `enterprise` | Ilimitado |

---

## Estados válidos

| Estado | Acceso |
|---|---|
| `active` | ✅ |
| `trialing` | ✅ |
| `suspended` | ❌ |
| `canceled` | ❌ |
| `past_due` | ❌ |

---

## Checklist operativo

1. Confirmar que el pago fue recibido.
2. Obtener el UUID del tenant con el Paso 0.
3. Ejecutar el SQL correspondiente.
4. Verificar con la consulta del paso 9.
5. Confirmar que el tenant puede acceder enviando un mensaje de prueba.

---

## Sincronización de tenants YAML → PostgreSQL

Si se añade un nuevo tenant en `project/config/tenants/` y aún no tiene fila en la tabla `tenants`, ejecutar:

```bash
python scripts/sync_tenants_to_db.py
```

El script detecta todos los slugs en disco, crea los que faltan en PostgreSQL con `status = 'active'` y deja intactos los existentes. Es idempotente: puede ejecutarse varias veces sin efectos secundarios.

---

## Bootstrap inicial del SaaS

Usar cuando se clona el proyecto por primera vez o cuando se añaden tenants nuevos y se necesita garantizar la estructura mínima en PostgreSQL para todos ellos.

```bash
python scripts/bootstrap_saas_data.py
```

El script recorre todos los subdirectorios de `project/config/tenants/` y garantiza que cada tenant tenga exactamente una fila en:

| Tabla | Valores iniciales |
|---|---|
| `tenants` | `name=slug`, `status='active'` |
| `admin_users` | `name=slug`, resto `NULL` |
| `subscriptions` | `plan_code='starter'`, `status='trialing'`, vigente 30 días |
| `tenant_settings` | `settings='{}'` |

Nunca sobreescribe ni modifica registros existentes. Cada tenant se procesa en su propia transacción. Salida esperada:

```text
[existing] asesor_ai_prod
[created]  agencia_viajes -> tenant, admin_user, subscription, tenant_settings
[created]  clinic -> tenant, admin_user, subscription, tenant_settings
...

Summary:
  tenants processed: 9
  records created:   32
  records existing:  4
  errors:            0
```

Si todos los tenants ya existen correctamente, el script reporta `[existing]` para cada uno y termina con `records created: 0`.

> **Nota:** el script no crea suscripciones. Después de sincronizar, crear la suscripción manualmente con el SQL de la sección 1.
