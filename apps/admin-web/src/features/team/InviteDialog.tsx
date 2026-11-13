import { useState, type FormEvent } from "react";
import { Button } from "../../components/ui/Button";
import { CopyButton } from "../../components/ui/CopyButton";
import { Dialog } from "../../components/ui/Dialog";
import { Alert } from "../../components/ui/Feedback";
import { SelectField, TextField } from "../../components/ui/FormFields";
import { Icon } from "../../components/ui/Icon";
import { ROLE_DESCRIPTIONS, ROLE_LABELS, expiryText, invitationMessage, invitationUrl, type InvitationInput, type IssuedInvitation, type Role } from "../../domain/team/team";
import { teamProblems } from "../../state/useTeam";

/** Invitar: el correo de la persona y su rol. Al crearla, el panel muestra el enlace (`InvitationLinkDialog`). */
export function InviteDialog({
  roles,
  onInvite,
  onDone,
  onClose,
}: {
  roles: Role[];
  onInvite: (input: InvitationInput) => Promise<IssuedInvitation>;
  onDone: (issued: IssuedInvitation) => void;
  onClose: () => void;
}) {
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<Role>("agent");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [problems, setProblems] = useState<Record<string, string>>({});

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setProblems({});
    try {
      onDone(await onInvite({ email: email.trim(), role }));
    } catch (reason) {
      const failure = teamProblems(reason);
      setError(failure.message);
      setProblems(failure.problems);
      setBusy(false);
    }
  };

  return (
    <Dialog
      title="Invitar al equipo"
      description="Te damos un enlace para que se lo envíes. Al abrirlo, entra con su cuenta (o la crea) con este mismo correo."
      onClose={busy ? () => undefined : onClose}
      footer={
        <>
          <Button variant="ghost" disabled={busy} onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" form="invite-form" disabled={busy}>
            {busy ? "Creando…" : "Crear invitación"}
          </Button>
        </>
      }
    >
      <form id="invite-form" className="form-stack" onSubmit={(event) => void submit(event)} noValidate>
        <TextField label="Correo" type="email" value={email} placeholder="ana@tunegocio.com" required error={problems.email} onChange={setEmail} />
        <SelectField
          label="Rol"
          value={role}
          options={roles.map((value) => ({ value, label: ROLE_LABELS[value] }))}
          hint={ROLE_DESCRIPTIONS[role]}
          error={problems.role}
          onChange={setRole}
        />
        {error && !problems.email && !problems.role && <Alert tone="danger">{error}</Alert>}
      </form>
    </Dialog>
  );
}

/** El enlace de una invitación recién creada o renovada: solo se ve ahora. Copiarlo o enviarlo por WhatsApp. */
export function InvitationLinkDialog({ issued, businessName, renewed, onClose }: { issued: IssuedInvitation; businessName: string; renewed: boolean; onClose: () => void }) {
  const url = invitationUrl(window.location.origin, issued.token);
  const whatsapp = `https://wa.me/?text=${encodeURIComponent(invitationMessage(businessName, issued.role, url))}`;
  return (
    <Dialog
      title={renewed ? "Nuevo enlace de invitación" : "Invitación lista"}
      description={`Envíaselo a ${issued.email}. Entrará como ${ROLE_LABELS[issued.role]}. ${expiryText(issued.expiresAt)}.`}
      onClose={onClose}
      footer={<Button onClick={onClose}>Listo</Button>}
    >
      <div className="invite-link">
        <code className="invite-link__url">{url}</code>
        <div className="invite-link__actions">
          <CopyButton text={url} label="Copiar enlace" />
          <a className="button button--secondary button--small" href={whatsapp} target="_blank" rel="noreferrer">
            <Icon name="send" size={14} /> Enviar por WhatsApp
          </a>
        </div>
        <p className="invite-link__note">
          {renewed ? "El enlace anterior ya no sirve. " : ""}Guárdalo ahora: por seguridad no lo volvemos a mostrar. Si se pierde, crea un nuevo enlace desde el equipo.
        </p>
      </div>
    </Dialog>
  );
}
