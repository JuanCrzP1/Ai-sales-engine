# Código anterior del panel, sin uso

La Fase 2 conectó el panel con la API local y BusinessConfig v1. Estos archivos ya no se compilan ni se ejecutan: guardaban en
`localStorage` o traducían un modelo propio hacia el contrato. Se movieron aquí, sin borrarlos, porque algunos tenían cambios sin
commit. Se pueden eliminar cuando el dueño del proyecto lo decida; nada del panel ni de las pruebas depende de ellos.

| Archivos | Qué hacían | Qué los sustituye |
|---|---|---|
| `infrastructure/browser/browserStorage.ts`, `infrastructure/local/localConfigRepository.ts` y su prueba | Guardar en `localStorage` | `infrastructure/api/` y las pruebas de integración |
| `infrastructure/local/openAuthService.ts` y su prueba | Cuentas abiertas en `localStorage` | `infrastructure/local/localOperatorAuthService.ts` |
| `adapters/contractAdapter.ts`, `translateToEngine.ts`, `engineNotices.ts` y su prueba | Traducir `AssistantConfig` al contrato o a los YAML | El panel edita el documento del contrato |
| `app/AccountWorkspace.tsx` | Espacio de trabajo por cuenta | `app/BusinessWorkspace.tsx` |
| `features/payments/PaymentLinkForm.tsx` | Enlace de pago en claro | `features/payments/PaymentProfilesForm.tsx` y `SecretField.tsx` |
| `features/profile/DangerZoneCard.tsx` | Borrar la configuración del navegador | Eliminar un negocio desde la lista |
| `domain/config/operations.test.ts`, `domain/validation/rules.test.ts`, `features/review/buildSummary.test.ts` | Pruebas sobre `AssistantConfig` | Las mismas comprobaciones sobre el documento, en esas mismas rutas de `src/` |
| `test/fixtures/sampleConfig.ts` | Datos de prueba de `AssistantConfig` | `src/test/fixtures/sampleDocument.ts` |
