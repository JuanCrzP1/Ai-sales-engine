# Guía YAML de configuración comercial por negocio

Cada negocio (tenant) configura en YAML lo que vende y cómo lo cobra a **sus propios clientes**.
Las cuentas, suscripciones, facturación y límites de uso del motor no se configuran aquí: los
administra la plataforma externa.

## 1. Estructura mínima del tenant

Cada tenant vive en `project/config/tenants/<tenant_slug>/` e incluye:

- `business.yaml`
- `config.yaml`
- `inventory.yaml`
- `pricing.yaml`
- `sales.yaml`

El comportamiento comercial no se define en el código: si cambias sector, precios o estilo
comercial, cambias YAML.

## 2. config.yaml

```yaml
config:
  features:
    pricing_enabled: true
    catalog_mode: false
```

- Si `pricing_enabled: false` y no hay precios ni medios de pago, el prompt no incluye pricing.

## 3. pricing.yaml

`pricing.yaml` define la oferta del negocio. Debe tener `plans` o `catalog`.

### Planes o servicios (incluye negocios que venden suscripciones a sus clientes)

```yaml
pricing:
  plans:
    - id: plan_basico
      name: Plan Basico
      description: Configuracion inicial + servicio mensual
      pricing:
        COP:
          implementation: 150000   # cobro inicial (opcional)
          monthly: 180000          # cobro mensual recurrente del negocio a su cliente
        USD:
          implementation: 40
          monthly: 45
      includes:
        - configuracion inicial
      not_included:
        - costos de plataformas externas
      payment:
        link: https://...          # enlace de pago del negocio
        transfer:
          enabled: true
          methods:
            - type: nequi          # nequi | daviplata | bank | breb
              number: "..."
  conditions:
    - sin permanencia
```

- Para pago único usa `price` en lugar de `monthly`.
- `plans` siempre es una lista, aunque haya un solo plan.

### Catálogo de productos

```yaml
pricing:
  model: catalog
  catalog:
    categories:
      - id: camisetas
        name: Camisetas
    items:
      - id: camiseta_basica
        name: Camiseta basica
        category: camisetas
        price:
          COP: 45000
    payment:
      link: ""
      transfer:
        enabled: true
        methods: []
  conditions:
    - cambios hasta 5 dias despues de la entrega
```

## 4. Monedas

- El motor nunca convierte monedas ni calcula tasas de cambio.
- Los valores se muestran tal como están en el YAML, por moneda.

## 5. Datos sensibles

Los enlaces de pago, números de cuenta y referencias de transferencia son datos del negocio que el
motor entrega al comprador cuando elige un método de pago. Trátalos como información sensible.
