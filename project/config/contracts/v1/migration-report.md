# Informe de migración a BusinessConfig v1

Generado por `scripts/migrate_tenants_to_contract.py`. Cada documento se validó contra el contrato,
se comprobó que compilado con sus ajustes técnicos reproduce exactamente sus YAML de origen y que no
contiene datos de pago.

- Negocios encontrados: 9
- Negocios migrados: 9
- Errores: 0

| Negocio | Oferta | Campos comerciales | Ajustes técnicos | Referencias a secretos |
|---|---|---|---|---|
| agencia_viajes | catalog | 187 | 7 | 4 |
| asesor_ai_prod | plans | 241 | 8 | 5 |
| clinic | plans | 136 | 6 | 5 |
| demo | plans | 223 | 6 | 10 |
| ecommerce | plans | 135 | 6 | 5 |
| escuela_conduccion | catalog | 187 | 6 | 4 |
| restaurant | catalog | 154 | 7 | 4 |
| saas | plans | 131 | 6 | 5 |
| tienda_ropa | catalog | 161 | 6 | 4 |

Totales: 1555 campos comerciales, 58 ajustes técnicos, 46 referencias a secretos.

## Diagnóstico de los documentos

Documentos válidos con datos que el negocio debe decidir o completar (`app/domain/business_config/diagnostics.py`).
No se corrigen automáticamente: cambiarían la configuración comercial del negocio.

| Negocio | Tipo | Código | Detalle |
|---|---|---|---|
| agencia_viajes | incoherencia | `cierre_por_link_sin_link` | El asistente puede cerrar enviando el link de pago, pero ningún perfil de pago tiene link. |
| agencia_viajes | incompleto | `agenda_sin_horarios` | El servicio requiere agendar, pero no hay horarios de atención. |
| asesor_ai_prod | incoherencia | `recomienda_oferta_no_disponible` | Se recomienda 'plan_pro', que no está disponible. |
| asesor_ai_prod | incompleto | `sin_canales_de_atencion` | No hay canales de atención: el asistente no sabe por dónde atiende el negocio. |
| clinic | incompleto | `agenda_sin_horarios` | El servicio requiere agendar, pero no hay horarios de atención. |
| demo | incoherencia | `recomienda_oferta_no_disponible` | Se recomienda 'plan_pro', que no está disponible. |
| demo | incoherencia | `recomienda_oferta_no_disponible` | Se recomienda 'plan_basico', que no está disponible. |
| ecommerce | incoherencia | `modo_catalogo_contradice_oferta` | catalog_mode=True pero la oferta es de tipo 'plans'. |
| escuela_conduccion | incoherencia | `cierre_por_link_sin_link` | El asistente puede cerrar enviando el link de pago, pero ningún perfil de pago tiene link. |
| escuela_conduccion | incompleto | `agenda_sin_horarios` | El servicio requiere agendar, pero no hay horarios de atención. |
| restaurant | incoherencia | `cierre_por_link_sin_link` | El asistente puede cerrar enviando el link de pago, pero ningún perfil de pago tiene link. |
| tienda_ropa | incoherencia | `cierre_por_link_sin_link` | El asistente puede cerrar enviando el link de pago, pero ningún perfil de pago tiene link. |
| tienda_ropa | incoherencia | `entrega_sin_modalidad` | fulfillment.delivery está disponible, pero service_modes no incluye 'domicilio'. |
| tienda_ropa | incoherencia | `entrega_sin_modalidad` | fulfillment.pickup está disponible, pero service_modes no incluye 'recoger'. |
