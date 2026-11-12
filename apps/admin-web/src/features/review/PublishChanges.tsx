import { useMemo, useState } from "react";
import { Badge } from "../../components/ui/Feedback";
import { schemaFieldNamer } from "../../domain/config/contractSchema";
import { documentChanges, type ChangeKind, type DocumentChange } from "../../domain/config/publishChanges";
import { CONFIG_SECTIONS } from "../../domain/sections";
import { useContractSchema } from "../../state/directoryContext";
import { useConfig } from "../../state/useConfig";

const KIND: Record<ChangeKind, { label: string; tone: "success" | "warning" | "neutral" }> = {
  added: { label: "Nuevo", tone: "success" },
  changed: { label: "Cambió", tone: "warning" },
  removed: { label: "Se quita", tone: "neutral" },
};

/** Cuántos se ven de cada sección antes de «Ver todos». */
const PREVIEW = 6;

/**
 * Antes de publicar: qué va a cambiar para los clientes, sección por sección, comparando lo guardado con lo publicado. Así se
 * publica sabiendo qué se publica. Los datos de pago se nombran, pero nunca se muestra su valor.
 */
export function PublishChanges() {
  const { dirty, publication, publishedDocument, savedDocument } = useConfig();
  const schema = useContractSchema();
  const changes = useMemo(
    () => (publishedDocument ? documentChanges(publishedDocument, savedDocument, schemaFieldNamer(schema)) : []),
    [publishedDocument, savedDocument, schema],
  );

  if (publication === "never") {
    return (
      <section className="publish-changes" aria-label="Lo que cambia al publicar">
        <h3 className="publish-changes__title">Primera publicación</h3>
        <p className="field__hint">Todavía no has publicado nada: al publicar, tu asistente empieza a responder con todo lo que configuraste.</p>
      </section>
    );
  }
  if (publication === "checking") return null;
  if (publication === "published") {
    return (
      <section className="publish-changes" aria-label="Lo que cambia al publicar">
        <h3 className="publish-changes__title">Todo está publicado</h3>
        <p className="field__hint">
          {dirty ? "Guarda tus cambios para ver aquí lo que cambiaría al publicar." : "Lo que tienes guardado es lo que ya responde a tus clientes."}
        </p>
      </section>
    );
  }

  const bySection = CONFIG_SECTIONS.map((section) => ({ section, items: changes.filter((change) => change.section === section.id) })).filter((group) => group.items.length > 0);
  return (
    <section className="publish-changes" aria-label="Lo que cambia al publicar">
      <h3 className="publish-changes__title">
        Lo que cambia al publicar <span className="publish-changes__count">{changes.length}</span>
      </h3>
      <p className="field__hint">Comparado con lo que tus clientes reciben hoy.{dirty ? " Lo que todavía no guardas no está aquí." : ""}</p>
      {bySection.map(({ section, items }) => (
        <ChangeGroup key={section.id} title={section.title} items={items} />
      ))}
    </section>
  );
}

function ChangeGroup({ title, items }: { title: string; items: DocumentChange[] }) {
  const [open, setOpen] = useState(false);
  const shown = open ? items : items.slice(0, PREVIEW);
  return (
    <div className="publish-changes__group">
      <h4 className="publish-changes__section">{title}</h4>
      <ul className="publish-changes__list">
        {shown.map((change, index) => (
          <li key={`${change.label}-${index}`} className="publish-changes__item">
            <Badge tone={KIND[change.kind].tone}>{KIND[change.kind].label}</Badge>
            <span className="publish-changes__label">{change.label}</span>
            <ChangeValues change={change} />
          </li>
        ))}
      </ul>
      {items.length > PREVIEW && (
        <button type="button" className="link-button" onClick={() => setOpen((value) => !value)}>
          {open ? "Ver menos" : `Ver los ${items.length}`}
        </button>
      )}
    </div>
  );
}

function ChangeValues({ change }: { change: DocumentChange }) {
  if (change.protectedValue) return <span className="publish-changes__values">Dato de pago actualizado (protegido)</span>;
  if (change.kind === "changed" && change.before !== null && change.after !== null) {
    return (
      <span className="publish-changes__values">
        <del>{change.before}</del> → <ins>{change.after}</ins>
      </span>
    );
  }
  // Un elemento nuevo o que se quita ya se nombra en la etiqueta; un campo suelto muestra su valor.
  const value = change.kind === "removed" ? change.before : change.after;
  if (value === null || change.label.endsWith(`«${value}»`)) return null;
  return <span className="publish-changes__values">{change.kind === "removed" ? <del>{value}</del> : <ins>{value}</ins>}</span>;
}
