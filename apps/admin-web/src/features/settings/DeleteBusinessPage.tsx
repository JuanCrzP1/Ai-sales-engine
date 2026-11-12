import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Button } from "../../components/ui/Button";
import { Alert } from "../../components/ui/Feedback";
import { Card, PageHeader } from "../../components/ui/Layout";
import { DeleteBusinessDialog, WHAT_IS_DELETED } from "../../layout/DeleteBusinessDialog";
import { BUSINESSES_PATH } from "../../navigation/navItems";
import { useMyBusinesses } from "../../state/useMyBusinesses";

/**
 * Configuración → Eliminar negocio: qué se pierde y el botón para eliminarlo (con su confirmación). Al terminar lleva a «Tus negocios»
 * con el aviso de que se eliminó.
 */
export function DeleteBusinessPage() {
  const { slug = "" } = useParams();
  const navigate = useNavigate();
  const business = useMyBusinesses().find((item) => item.slug === slug);
  const [confirming, setConfirming] = useState(false);

  return (
    <>
      <PageHeader title="Eliminar negocio" description="Bórralo con todo lo suyo, si ya no lo vas a usar. No se puede deshacer." />
      <Card icon="trash" tone="rose" title={business ? `Eliminar «${business.name}»` : "Eliminar este negocio"}>
        <div className="form-stack">
          <p className="field__hint">Al eliminarlo se borra para siempre:</p>
          <ul className="delete-chat__list">
            {WHAT_IS_DELETED.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
          <Alert tone="info" title="¿Solo quieres pausarlo?">
            Desconecta WhatsApp en Canales: el asistente deja de responder y conservas todo.
          </Alert>
          <div>
            <Button variant="danger" className="button--danger-outline" disabled={!business} onClick={() => setConfirming(true)}>
              Eliminar este negocio
            </Button>
          </div>
        </div>
      </Card>
      {confirming && business && (
        <DeleteBusinessDialog
          business={business}
          onClose={() => setConfirming(false)}
          onDeleted={() => navigate(BUSINESSES_PATH, { replace: true, state: { deleted: business.name } })}
        />
      )}
    </>
  );
}
