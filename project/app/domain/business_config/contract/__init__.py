"""Contrato global de configuración de negocios (BusinessConfig v1).

Fuente canónica del contrato. Desde estos modelos se generan el JSON Schema publicado
(`project/config/contracts/v1/business-config.schema.json`, con `scripts/export_business_config_schema.py`),
los tipos TypeScript del panel (`apps/admin-web/src/contracts/businessConfig.v1.ts`, con
`scripts/generate_business_config_types.py`) y la referencia de campos de
`docs/business-config-traceability.md` (con `scripts/generate_traceability_matrix.py`).

Un único documento comercial por negocio, con secciones comunes a todos los modelos comerciales; cada
negocio rellena solo las que necesita (las opcionales se omiten). Los modelos de oferta son `plans`
(planes o servicios, con pago único, mensual, anual o de instalación) y `catalog` (productos por
categoría, con variantes y precio por variante).

Lo técnico queda fuera de este documento: ventanas de conversación, banderas internas y estructuras
heredadas están en `EngineSettings` (`../engine_settings.py`), que el negocio no edita.

Marcas de cada campo en el esquema (se heredan: un campo sin marca toma la de su sección):
- `x-audience`: quién lo configura. `cliente` (el negocio, en lenguaje comercial), `avanzado`
  (estrategia comercial detallada, opcional) o `sistema` (versión y dueño del documento).
- `x-engine`: `conectado` si el motor actual lo usa (con una prueba en
  `tests/test_business_config_engine_integration.py`); `programado` si lo enviará la plataforma cuando
  exista el evento que lo dispara; `solo panel` si es solo para el equipo (nunca va a la IA); `pendiente`
  si solo está representado y conservado. Sin marca en ningún nivel: `pendiente`.

Los datos sensibles de pago (links, números de cuenta, referencias) nunca se guardan en el contrato:
se representan con `SecretRef`.

Versionado: `schema_version` es "1.0". Los cambios compatibles (campos opcionales nuevos, validaciones
que todos los documentos publicados cumplen) se hacen dentro de v1; un cambio incompatible exige un
contrato v2 en `project/config/contracts/v2/` y una migración de los documentos.
"""
from __future__ import annotations

from app.domain.business_config.contract.document import BusinessConfig, business_config_json_schema
from app.domain.business_config.contract.offer import Plan
from app.domain.business_config.contract.payments import PaymentProfile
from app.domain.business_config.contract.sales import Closing
from app.domain.business_config.primitives import SCHEMA_VERSION, SecretRef, Slug

__all__ = ["SCHEMA_VERSION", "BusinessConfig", "Closing", "PaymentProfile", "Plan", "SecretRef", "Slug", "business_config_json_schema"]
