import schemaFile from "../../../../../project/config/contracts/v1/business-config.schema.json";
import { emptyValue, fieldHint, fieldLabel, fieldShape, nodeAt, valueLabel, type ContractSchema, type SchemaNode } from "./contractSchema";

const SCHEMA = schemaFile as unknown as ContractSchema;

const shapeAt = (...path: string[]) => fieldShape(SCHEMA, nodeAt(SCHEMA, path));

/** Recorre los campos del contrato por donde el formulario generado podría pasar. */
function walk(node: SchemaNode, path: string, visit: (path: string, node: SchemaNode) => void, seen = new Set<string>()): void {
  const shape = fieldShape(SCHEMA, node);
  visit(path, node);
  const ref = node.$ref ?? node.anyOf?.find((option) => option.$ref)?.$ref;
  if (ref) {
    if (seen.has(ref)) return;
    seen = new Set(seen).add(ref);
  }
  for (const [key, child] of Object.entries(shape.node.properties ?? {})) walk(child, `${path}.${key}`, visit, seen);
  if (shape.node.items) walk(shape.node.items, `${path}[]`, visit, seen);
}

describe("lectura del contrato para generar formularios", () => {
  it("reconoce cada clase de campo con el contrato real", () => {
    expect(shapeAt("sales", "objections").kind).toBe("objectList");
    expect(shapeAt("identity", "name").kind).toBe("text");
    expect(shapeAt("identity", "differentiators").kind).toBe("list");
    expect(shapeAt("identity", "differentiators").nullable).toBe(true);
    expect(shapeAt("identity", "service_modes").kind).toBe("choiceList");
    expect(shapeAt("response_style", "length").kind).toBe("choice");
    expect(shapeAt("response_style", "max_words").kind).toBe("number");
    expect(shapeAt("features", "multi_plan").kind).toBe("boolean");
    expect(shapeAt("identity", "location").kind).toBe("object");
    expect(shapeAt("identity", "location").nullable).toBe(true);
  });

  it("entiende todos los campos sin lanzar errores y sus referencias existen", () => {
    let visited = 0;
    walk(SCHEMA, "", () => (visited += 1));
    expect(visited).toBeGreaterThan(150);
  });

  it("los valores iniciales de una lista solo traen lo obligatorio", () => {
    const objection = fieldShape(SCHEMA, nodeAt(SCHEMA, ["sales", "objections"])).node.items!;
    const value = emptyValue(SCHEMA, objection) as Record<string, unknown>;
    expect(Object.keys(value)).toEqual(fieldShape(SCHEMA, objection).node.required ?? []);
    expect(value.topic).toBe("");
  });

  it("falla de forma explícita si se pide un campo que el contrato no define", () => {
    expect(() => nodeAt(SCHEMA, ["sales", "no_existe"])).toThrow("El contrato no define sales.no_existe.");
    expect(() => fieldShape(SCHEMA, { $ref: "#/$defs/NoExiste" })).toThrow("El esquema del contrato no define NoExiste.");
  });

  it("nombra los campos en lenguaje del negocio y usa la descripción del contrato como ayuda", () => {
    const node = { description: "Descripción del contrato" };
    expect(fieldLabel("objections", node)).toBe("Objeciones");
    expect(fieldHint("objections", node)).toBe("Descripción del contrato");
    expect(fieldLabel("campo_nuevo", node)).toBe("Descripción del contrato");
    expect(fieldHint("campo_nuevo", node)).toBeUndefined();
    expect(fieldLabel("campo_nuevo", {})).toBe("campo nuevo");
    expect(valueLabel("service_booking")).toBe("Servicio con reserva");
    expect(valueLabel("otro_valor")).toBe("Otro valor");
  });

  it("no pide datos de pago en los formularios generados", () => {
    const secretPaths: string[] = [];
    walk(SCHEMA, "", (path) => {
      if (path.endsWith(".secret_ref")) secretPaths.push(path);
    });
    // Los datos de pago solo existen dentro de `payments`, que tiene su propia pantalla y nunca se genera desde el esquema.
    expect(secretPaths.length).toBeGreaterThan(0);
    expect(secretPaths.every((path) => path.startsWith(".payments"))).toBe(true);
  });
});
