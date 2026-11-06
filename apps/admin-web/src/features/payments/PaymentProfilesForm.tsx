import { Button } from "../../components/ui/Button";
import { ConfirmButton } from "../../components/ui/ConfirmButton";
import { EmptyState } from "../../components/ui/Feedback";
import { Card } from "../../components/ui/Layout";
import { Toggle } from "../../components/ui/Toggle";
import { isLinkActive, isStoredRef } from "../../domain/config/document";
import type { PaymentProfile } from "../../domain/config/types";
import { useConfig } from "../../state/useConfig";
import { SecretField } from "./SecretField";
import { TransferMethodsForm } from "./TransferMethodsForm";

/** Medios de pago del negocio. Casi todos usan un solo perfil; varios permiten cobrar cada plan por una vía distinta. */
export function PaymentProfilesForm() {
  const { document, actions } = useConfig();
  const profiles = document.payments;

  if (profiles.length === 0) {
    return (
      <Card title="Medios de pago">
        <EmptyState
          title="Todavía no hay medios de pago"
          description="Agrega un enlace de pago o las cuentas a las que te pueden transferir."
          action={<Button onClick={actions.addPaymentProfile}>Configurar medios de pago</Button>}
        />
      </Card>
    );
  }

  return (
    <>
      {profiles.map((profile, index) => (
        <ProfileCard key={profile.id} profile={profile} index={index} several={profiles.length > 1} />
      ))}
      <div className="button-row">
        <Button variant="secondary" onClick={actions.addPaymentProfile}>
          Agregar otro perfil de pago
        </Button>
      </div>
    </>
  );
}

function ProfileCard({ profile, index, several }: { profile: PaymentProfile; index: number; several: boolean }) {
  const { actions } = useConfig();
  const title = several ? `Medios de pago: ${profile.id}` : "Medios de pago";

  return (
    <Card
      title={title}
      description={several ? "Cada plan o catálogo indica con qué perfil se cobra." : "Un enlace de tu pasarela de pagos (Wompi, Mercado Pago, PayU u otra) y las cuentas a las que te pueden transferir."}
      actions={
        <ConfirmButton confirmLabel="Sí, quitar" onConfirm={() => actions.removePaymentProfile(profile.id)}>
          Quitar perfil
        </ConfirmButton>
      }
    >
      <Toggle
        label="Ofrecer pago por enlace"
        description={profile.link && !isLinkActive(profile) ? "Desactivado: el enlace se conserva, pero el asistente no lo ofrece." : undefined}
        checked={isLinkActive(profile)}
        onChange={(enabled) => actions.setPaymentLinkEnabled(profile.id, enabled)}
      />
      {profile.link && (
        <>
          <SecretField
            label="Enlace de pago"
            secretRef={profile.link.secret_ref}
            path={`payments.${index}.link`}
            type="url"
            inputMode="url"
            placeholder="https://"
            hint="El asistente usa un único enlace para todas las compras."
          />
          {isStoredRef(profile.link.secret_ref) && (
            <div>
              <ConfirmButton confirmLabel="Sí, quitar" onConfirm={() => actions.removePaymentLink(profile.id)}>
                Quitar enlace
              </ConfirmButton>
            </div>
          )}
        </>
      )}
      <TransferMethodsForm profile={profile} profileIndex={index} />
    </Card>
  );
}
