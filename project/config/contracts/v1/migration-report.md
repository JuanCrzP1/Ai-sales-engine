# Informe de migración a BusinessConfig v1

Generado por `scripts/migrate_tenants_to_contract.py`. Cada documento se validó contra el contrato,
se comprobó que compilado reproduce exactamente sus YAML de origen y que no contiene datos de pago.

- Negocios encontrados: 9
- Negocios migrados: 9
- Errores: 0

| Negocio | Oferta | Campos tipados | Campos en compatibilidad | Referencias a secretos |
|---|---|---|---|---|
| agencia_viajes | catalog | 189 | 18 | 4 |
| asesor_ai_prod | plans | 234 | 25 | 5 |
| clinic | plans | 129 | 17 | 5 |
| demo | plans | 212 | 25 | 10 |
| ecommerce | plans | 130 | 17 | 5 |
| escuela_conduccion | catalog | 184 | 17 | 4 |
| restaurant | catalog | 155 | 18 | 4 |
| saas | plans | 126 | 17 | 5 |
| tienda_ropa | catalog | 160 | 17 | 4 |

Totales: 1519 campos tipados, 171 en compatibilidad, 46 referencias a secretos.

## Diagnóstico de los documentos

Documentos válidos con datos que el negocio debe decidir o completar (`app/domain/business_config/diagnostics.py`).
No se corrigen automáticamente: cambiarían la configuración comercial del negocio.

| Negocio | Tipo | Código | Detalle |
|---|---|---|---|
| agencia_viajes | incoherencia | `cierre_por_link_sin_link` | El asistente puede cerrar enviando el link de pago, pero ningún perfil de pago tiene link. |
| agencia_viajes | incompleto | `datos_sin_aviso_de_tratamiento` | Se piden datos personales sin un aviso de tratamiento de datos. |
| agencia_viajes | incompleto | `agenda_sin_horarios` | El servicio requiere agendar, pero no hay horarios de atención. |
| asesor_ai_prod | incompleto | `sin_canales_de_atencion` | No hay canales de atención: el asistente no sabe por dónde atiende el negocio. |
| asesor_ai_prod | incompleto | `datos_sin_aviso_de_tratamiento` | Se piden datos personales sin un aviso de tratamiento de datos. |
| clinic | incompleto | `datos_sin_aviso_de_tratamiento` | Se piden datos personales sin un aviso de tratamiento de datos. |
| clinic | incompleto | `agenda_sin_horarios` | El servicio requiere agendar, pero no hay horarios de atención. |
| demo | incompleto | `datos_sin_aviso_de_tratamiento` | Se piden datos personales sin un aviso de tratamiento de datos. |
| ecommerce | incoherencia | `modo_catalogo_contradice_oferta` | catalog_mode=True pero la oferta es de tipo 'plans'. |
| ecommerce | incompleto | `datos_sin_aviso_de_tratamiento` | Se piden datos personales sin un aviso de tratamiento de datos. |
| escuela_conduccion | incoherencia | `cierre_por_link_sin_link` | El asistente puede cerrar enviando el link de pago, pero ningún perfil de pago tiene link. |
| escuela_conduccion | incompleto | `datos_sin_aviso_de_tratamiento` | Se piden datos personales sin un aviso de tratamiento de datos. |
| escuela_conduccion | incompleto | `agenda_sin_horarios` | El servicio requiere agendar, pero no hay horarios de atención. |
| restaurant | incoherencia | `cierre_por_link_sin_link` | El asistente puede cerrar enviando el link de pago, pero ningún perfil de pago tiene link. |
| restaurant | incompleto | `datos_sin_aviso_de_tratamiento` | Se piden datos personales sin un aviso de tratamiento de datos. |
| saas | incompleto | `datos_sin_aviso_de_tratamiento` | Se piden datos personales sin un aviso de tratamiento de datos. |
| tienda_ropa | incoherencia | `cierre_por_link_sin_link` | El asistente puede cerrar enviando el link de pago, pero ningún perfil de pago tiene link. |
| tienda_ropa | incoherencia | `entrega_sin_modalidad` | fulfillment.delivery está disponible, pero service_modes no incluye 'domicilio'. |
| tienda_ropa | incoherencia | `entrega_sin_modalidad` | fulfillment.pickup está disponible, pero service_modes no incluye 'recoger'. |
| tienda_ropa | incompleto | `datos_sin_aviso_de_tratamiento` | Se piden datos personales sin un aviso de tratamiento de datos. |
