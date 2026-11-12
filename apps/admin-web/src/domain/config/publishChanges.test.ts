import schemaFile from "../../../../../project/config/contracts/v1/business-config.schema.json";
import { SAMPLE_DOCUMENT } from "../../test/fixtures/sampleDocument";
import { schemaFieldNamer, type ContractSchema } from "./contractSchema";
import { differsFromPublished, documentChanges } from "./publishChanges";
import type { BusinessDocument } from "./types";

const NAME = schemaFieldNamer(schemaFile as unknown as ContractSchema);

function edited(change: (document: BusinessDocument) => void): BusinessDocument {
  const copy = structuredClone(SAMPLE_DOCUMENT);
  change(copy);
  return copy;
}

describe("lo que cambia al publicar", () => {
  it("guardar sin cambiar nada no deja nada pendiente, aunque cambie el orden o haya vacíos", () => {
    const reordered = Object.fromEntries(Object.entries(structuredClone(SAMPLE_DOCUMENT)).reverse()) as unknown as BusinessDocument;
    const withEmpties = edited((document) => Object.assign(document.identity, { brand_name: null, positioning: "" }));
    expect(differsFromPublished(SAMPLE_DOCUMENT, reordered)).toBe(false);
    expect(documentChanges(SAMPLE_DOCUMENT, withEmpties, NAME).filter((change) => change.label.includes("Marca"))).toEqual([]);
  });

  it("dice qué campo cambió, en su sección y con cómo estaba y cómo queda", () => {
    const draft = edited((document) => {
      document.identity.brand_name = "Ai sales engine";
      document.identity.name = "Café Aroma Centro";
    });
    expect(differsFromPublished(SAMPLE_DOCUMENT, draft)).toBe(true);
    const changes = documentChanges(SAMPLE_DOCUMENT, draft, NAME);
    expect(changes).toContainEqual({ section: "business", label: "Marca", kind: "added", before: null, after: "Ai sales engine" });
    expect(changes).toContainEqual({ section: "business", label: "Nombre", kind: "changed", before: SAMPLE_DOCUMENT.identity.name, after: "Café Aroma Centro" });
  });

  it("en las listas dice qué elemento se agregó, se quitó o cambió, por su título", () => {
    const published = edited((document) => {
      document.knowledge = { ...document.knowledge, faqs: [{ question: "¿Hay permanencia?", answer: "No, mes a mes." }, { question: "¿Hacen envíos?", answer: "Sí." }] };
    });
    const faqs = published.knowledge!.faqs!;
    const draft = structuredClone(published);
    ((document: BusinessDocument) => {
      const list = document.knowledge!.faqs!;
      list[0] = { ...list[0]!, answer: "Respuesta nueva" };
      list.splice(1, 1);
      list.push({ question: "¿Tienen domicilio?", answer: "Sí, en toda la ciudad." });
    })(draft);
    const changes = documentChanges(published, draft, NAME).filter((change) => change.section === "assistant");
    expect(changes).toContainEqual(expect.objectContaining({ kind: "changed", label: `Preguntas frecuentes › «${faqs[0]!.question}» › Respuesta`, after: "Respuesta nueva" }));
    expect(changes).toContainEqual(expect.objectContaining({ kind: "added", label: "Preguntas frecuentes › «¿Tienen domicilio?»" }));
    expect(changes).toContainEqual(expect.objectContaining({ kind: "removed", label: `Preguntas frecuentes › «${faqs[1]!.question}»` }));
  });

  it("un dato de pago que cambió se informa sin mostrar nunca su valor", () => {
    const draft = edited((document) => {
      const holder = document.payments![0]!.link!;
      holder.secret_ref = `${holder.secret_ref}~nuevo`;
    });
    const [change] = documentChanges(SAMPLE_DOCUMENT, draft, NAME);
    expect(change).toEqual(expect.objectContaining({ section: "payments", kind: "changed", before: null, after: null, protectedValue: true }));
    expect(JSON.stringify(change)).not.toContain("secret_store");
  });

  it("sin nada publicado todavía no hay comparación: todo es nuevo", () => {
    expect(documentChanges(null, SAMPLE_DOCUMENT, NAME)).toEqual([]);
  });
});
