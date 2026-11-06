import { ConfirmButton } from "../../components/ui/ConfirmButton";
import { Card } from "../../components/ui/Layout";
import { useConfigActions } from "../../state/useConfig";

/** Acciones irreversibles sobre la configuración de la cuenta. */
export function DangerZoneCard() {
  const { resetConfig } = useConfigActions();

  return (
    <Card title="Zona de riesgo" description="Borra todo lo configurado del asistente (negocio, productos, pagos y mensajes). Tu cuenta no se elimina.">
      <div className="button-row">
        <ConfirmButton variant="danger" size="default" confirmLabel="Sí, borrar todo" onConfirm={resetConfig}>
          Borrar configuración del asistente
        </ConfirmButton>
      </div>
    </Card>
  );
}
