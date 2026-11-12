import { Link, useParams } from "react-router-dom";
import { Icon } from "../../components/ui/Icon";
import { startSteps } from "../../domain/help/help";
import { helpArticlePath } from "../../navigation/navItems";
import { useWorkspacePath } from "../../navigation/useWorkspacePath";
import { useAISettings } from "../../state/useAISettings";
import { useConfig } from "../../state/useConfig";
import { useQuickReplies } from "../../state/useQuickReplies";
import { useWhatsAppStatus } from "../../state/useWhatsAppStatus";

/**
 * «Empieza aquí»: los cinco pasos para dejar el asistente vendiendo, marcados solos con lo que el panel ve del negocio abierto. Lo
 * que todavía no se sabe (la clave mientras carga, WhatsApp si no responde) no se marca ni se desmarca: queda sin estado.
 */
export function GettingStarted() {
  const { slug = "" } = useParams();
  const pathTo = useWorkspacePath();
  const { progress, publication } = useConfig();
  const ai = useAISettings();
  const whatsapp = useWhatsAppStatus();
  const quick = useQuickReplies(slug);
  const steps = startSteps({
    sectionsReady: progress.total > 0 && progress.completed === progress.total,
    aiKey: ai.status === "ready" ? Boolean(ai.settings?.key.configured) : null,
    published: publication === "pending" || publication === "published",
    whatsapp: whatsapp === null ? null : whatsapp === "connected",
    quickReplies: quick.status === "ready" ? quick.replies.length > 0 : null,
  });
  const done = steps.filter((step) => step.done).length;
  const next = steps.find((step) => step.done === false);

  return (
    <section className="help-start" aria-labelledby="empieza-aqui">
      <header className="help-start__header">
        <div>
          <h2 id="empieza-aqui" className="help-start__title">
            {done === steps.length ? "Tu asistente ya está listo" : "Empieza aquí"}
          </h2>
          <p className="help-start__text">
            {done === steps.length ? "Hiciste los cinco pasos. Lo demás de la ayuda es para afinar." : "Los pasos para dejar a tu asistente vendiendo. Se marcan solos cuando los haces."}
          </p>
        </div>
        <span className="help-start__count" aria-label={`${done} de ${steps.length} pasos listos`}>
          {done}/{steps.length}
        </span>
      </header>
      <ol className="help-start__steps">
        {steps.map((step, index) => (
          <li key={step.id} className={`help-step${step.done ? " help-step--done" : ""}${step === next ? " help-step--next" : ""}`}>
            <span className="help-step__mark" aria-hidden="true">
              {step.done ? <Icon name="check" size={14} /> : index + 1}
            </span>
            <span className="help-step__text">
              <Link to={pathTo(step.path)} className="help-step__title">
                {step.title}
              </Link>
              <span className="help-step__detail">{step.detail}</span>
            </span>
            <span className="help-step__state">
              {step.done ? <span className="visually-hidden">Listo</span> : step.done === false ? <span className="visually-hidden">Pendiente</span> : null}
              <Link to={pathTo(helpArticlePath(step.article))} className="help-step__how">
                Cómo se hace
              </Link>
            </span>
          </li>
        ))}
      </ol>
    </section>
  );
}
