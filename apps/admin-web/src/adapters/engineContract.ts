import type { EngineTenantSections } from "./engineTypes";

/**
 * Comprobaciones mínimas que hoy aplica el motor al cargar un negocio
 * (`RuntimeYamlBuilder._validate` en project/app/application/runtime/runtime_yaml_builder.py),
 * reproducidas sin ejecutar el motor. CONTRATO PROVISIONAL: se revisará al corregir los YAML.
 *
 * Devuelve la lista de incumplimientos (vacía si cumple).
 */
export function checkEngineContract(sections: EngineTenantSections): string[] {
  const violations: string[] = [];
  for (const key of ["business", "sales", "pricing", "inventory", "config"] as const) {
    const section: unknown = sections[key];
    if (typeof section !== "object" || section === null || Array.isArray(section) || Object.keys(section).length === 0) {
      violations.push(`La sección "${key}" debe ser un objeto con contenido.`);
    }
  }
  if (!("description" in sections.business)) violations.push('La sección "business" debe incluir la clave "description".');
  if (!("plans" in sections.pricing) && !("catalog" in sections.pricing)) {
    violations.push('La sección "pricing" debe incluir "plans" o "catalog".');
  }
  return violations;
}
