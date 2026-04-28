# Guía YAML SaaS

Esta guía define la estructura canónica de configuración por tenant para un runtime SaaS multi-tenant.

## 1. Estructura Mínima Del Tenant

Cada tenant debe vivir en:

`project/config/tenants/<tenant_slug>/`

Y debe incluir como mínimo:

- `business.yaml`
- `config.yaml`
- `inventory.yaml`
- `pricing.yaml`
- `sales.yaml`

## 2. Regla General

El comportamiento comercial no se define en el código.
Se define en los YAML del tenant.

Si cambias sector, pricing o estilo comercial, cambias YAML.
No cambias la lógica interna del motor.

## 3. config.yaml

`config.yaml` debe incluir switches operativos del runtime:

```yaml
config:
  features:
    pricing_enabled: true
    multi_currency: true
    multi_plan: true
    catalog_mode: false
```

Regla:

- si `pricing_enabled: false`, el runtime no debe inyectar pricing comercial en el prompt final

## 4. pricing.yaml

`pricing.yaml` define la estructura económica del tenant.

Ejemplo canónico:

```yaml
pricing:
  currencies:
    primary: COP
    supported:
      - COP
      - USD

  exchange_reference: manual
  model: hybrid

  plans:
    - id: plan_basico
      name: Plan Basico
      description: Configuracion inicial + sistema mensual
      pricing:
        COP:
          implementation: 150000
          monthly: 180000
        USD:
          implementation: 40
          monthly: 45
      includes:
        - configuracion inicial
        - integracion con canales
        - seguimiento automatico
      not_included:
        - costos de plataformas externas
        - inversion publicitaria

  custom_rules:
    show_single_plan_as_main: true
    allow_multi_plan_selection: false

  payment_methods:
    - transferencia
    - nequi
    - tarjeta

  conditions:
    - sin permanencia
    - cancelacion mensual
```

Regla clave:

- `plans` siempre debe ser una lista, incluso cuando exista un solo plan

## 5. Adaptación Multi-Tenant

El mismo motor puede operar para:

- servicios
- salud
- ecommerce
- educación
- cualquier operación comercial con conversación como canal principal

La diferencia la marca el tenant activo y su configuración YAML.
          monthly: 250000
    - id: premium
      name: Premium
      pricing:
        COP:
          implementation: 350000
          monthly: 420000
```

### Ecommerce catalog

```yaml
pricing:
  model: catalog
  currencies:
    primary: COP
    supported:
      - COP
  plans:
    - id: producto_1
      name: Camiseta deportiva
      pricing:
        COP:
          price: 80000
```

## 4. Real Examples by Industry

### Service business

- Use `model: single` or `model: hybrid`.
- Use `implementation` and/or `monthly` per currency.
- Use `includes` and `not_included` to define scope.

### Ecommerce

- Use `model: catalog`.
- Define one product per `plans[]` item.
- Prefer `price` over `monthly` when subscription does not apply.

### SaaS subscription

- Use `model: subscription` or `model: hybrid`.
- Keep `monthly` in each currency bucket.
- Optionally keep `implementation` if onboarding is charged.

### Multi-plan commercial strategy

- Keep all available options in `plans`.
- Use `custom_rules.show_single_plan_as_main` and `custom_rules.allow_multi_plan_selection` for sales behavior hints.

## 5. Multi-currency Behavior

- Never convert currencies in runtime prompt assembly.
- Never calculate exchange rates in code.
- Prompt rendering should only display values as provided in YAML.
