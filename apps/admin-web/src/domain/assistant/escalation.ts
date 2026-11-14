import type { Option } from "../config/options";
import type { Escalation } from "../../contracts/businessConfig.v1";
import { MAX_ESCALATION_TOPIC_CHARS, MAX_ESCALATION_TOPICS, MAX_MESSAGE_CHARS } from "../../contracts/businessConfig.v1";
import type { BusinessDocument } from "../config/types";
import type { ValidationIssue } from "../validation/types";

/**
 * «Cuándo pasar a una persona» (Asistente IA → Cómo atiende). El asistente decide con estas reglas como instrucciones
 * (`project/app/infrastructure/ai/prompting/sections/escalation.py`); el servidor valida lo mismo con el contrato al guardar
 * (`contract/escalation.py`). Sin cambios, el asistente pasa el chat cuando el cliente pide una persona, reclama o avisa que pagó.
 */

/** Límites del contrato para estas reglas: el formulario no deja pasarse. */
export { MAX_ESCALATION_TOPICS, MAX_MESSAGE_CHARS as MAX_ESCALATION_INSTRUCTIONS_CHARS };

/** Las reglas tal como las guarda el contrato. */
export type EscalationRules = Escalation;

export type OnRequest = NonNullable<Escalation["on_request"]>;

export const ON_REQUEST_OPTIONS: Option<OnRequest>[] = [
  { value: "always", label: "Pasarlo de inmediato", hint: "Apenas lo pida, el asistente le dice que lo pasa con tu equipo." },
  { value: "offer_help_first", label: "Primero ofrecerle ayuda", hint: "Le ofrece resolverlo una vez, sin insistir. Si lo vuelve a pedir, lo pasa con tu equipo." },
];

/** Las reglas del negocio, con los valores por defecto donde no hay nada escrito (documentos guardados antes de esta sección). */
export function escalationOf(document: BusinessDocument): Required<Omit<Escalation, "instructions">> & Pick<Escalation, "instructions"> {
  const escalation = document.escalation ?? {};
  return {
    on_request: escalation.on_request ?? "always",
    always_topics: escalation.always_topics ?? [],
    never_topics: escalation.never_topics ?? [],
    when_stuck: escalation.when_stuck ?? false,
    instructions: escalation.instructions ?? null,
  };
}

/**
 * Las reglas después de un cambio en el formulario. Si quedan como al principio, la sección se quita (undefined): un negocio que no
 * la usa no la guarda, y al publicar no aparece como cambio.
 */
export function updatedEscalation(document: BusinessDocument, patch: Partial<Escalation>): Escalation | undefined {
  const next = { ...escalationOf(document), ...patch };
  const isDefault =
    next.on_request === "always" && next.always_topics.length === 0 && next.never_topics.length === 0 && !next.when_stuck && !(next.instructions ?? "").trim();
  return isDefault ? undefined : next;
}

const key = (topic: string) => topic.trim().split(/\s+/).join(" ").toLocaleLowerCase("es");

/** Igual que el contrato: sin temas repetidos, ninguno en las dos listas y dentro de los límites. */
export function validateEscalation(document: BusinessDocument): ValidationIssue[] {
  const rules = escalationOf(document);
  const issues: ValidationIssue[] = [];
  const add = (field: string, message: string) => issues.push({ section: "assistant", field: `escalation.${field}`, severity: "error", message });
  const lists = [
    ["always_topics", "Temas que atiende tu equipo", rules.always_topics],
    ["never_topics", "Temas que resuelve el asistente", rules.never_topics],
  ] as const;
  for (const [field, label, topics] of lists) {
    const keys = topics.map(key);
    if (topics.length > MAX_ESCALATION_TOPICS) add(field, `${label}: puedes agregar hasta ${MAX_ESCALATION_TOPICS}.`);
    if (topics.some((topic) => topic.length > MAX_ESCALATION_TOPIC_CHARS)) add(field, `${label}: cada tema admite hasta ${MAX_ESCALATION_TOPIC_CHARS} caracteres.`);
    if (new Set(keys).size !== keys.length) add(field, `${label}: hay temas repetidos.`);
  }
  const always = new Set(rules.always_topics.map(key));
  const both = rules.never_topics.filter((topic) => always.has(key(topic)));
  if (both.length > 0) add("never_topics", `«${both[0]}» está en las dos listas: elige si lo atiende tu equipo o el asistente.`);
  if ((rules.instructions ?? "").length > MAX_MESSAGE_CHARS) add("instructions", `Las indicaciones admiten hasta ${MAX_MESSAGE_CHARS} caracteres.`);
  return issues;
}

/** En una frase, cuándo pasa el chat a una persona: para el resumen de la sección. */
export function escalationSummary(document: BusinessDocument): string {
  const rules = escalationOf(document);
  const parts = [rules.on_request === "offer_help_first" ? "Si piden una persona, primero ofrece ayuda" : "Si piden una persona, la pasa de inmediato"];
  if (rules.always_topics.length > 0) parts.push(`${rules.always_topics.length} ${rules.always_topics.length === 1 ? "tema" : "temas"} para tu equipo`);
  if (rules.when_stuck) parts.push("también si la conversación se estanca");
  return `${parts.join(" · ")}.`;
}
