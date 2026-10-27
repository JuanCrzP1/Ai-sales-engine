import { useId, useRef, useState, type ChangeEvent } from "react";
import { Avatar } from "../../components/ui/Avatar";
import { Button } from "../../components/ui/Button";
import { Alert } from "../../components/ui/Feedback";
import { Icon } from "../../components/ui/Icon";
import { Card } from "../../components/ui/Layout";
import { AVATAR_ACCEPTED_TYPES } from "../../domain/auth/avatarRules";
import { authErrorMessage } from "../../domain/auth/messages";
import { AvatarImageError, fileToAvatarDataUrl } from "./avatarImage";
import { useAuth, useCurrentUser } from "../../state/auth/useAuth";

/** Foto de perfil: subir, cambiar o quitar. */
export function AvatarEditor() {
  const user = useCurrentUser();
  const { updateProfile } = useAuth();
  const inputId = useId();
  const inputRef = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /** Obtiene la nueva foto (o null para quitarla) y la guarda en el perfil. */
  const changeAvatar = async (produce: () => Promise<string | null>) => {
    setBusy(true);
    setError(null);
    try {
      await updateProfile({ avatarUrl: await produce() });
    } catch (caught) {
      setError(caught instanceof AvatarImageError ? caught.message : authErrorMessage(caught));
    } finally {
      setBusy(false);
    }
  };

  const handleFile = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (file) void changeAvatar(() => fileToAvatarDataUrl(file));
  };

  return (
    <Card title="Foto de perfil" description="Se muestra en el menú de tu cuenta. JPG, PNG, WebP o GIF de hasta 5 MB.">
      <div className="avatar-editor">
        <div className="avatar-editor__preview">
          <Avatar name={user.name} src={user.avatarUrl} size="xl" />
          <label htmlFor={inputId} className="avatar-editor__badge" title="Cambiar foto">
            <Icon name="camera" size={16} />
            <span className="visually-hidden">Cambiar foto</span>
          </label>
        </div>
        <div className="avatar-editor__actions">
          <input
            ref={inputRef}
            id={inputId}
            className="visually-hidden"
            type="file"
            accept={AVATAR_ACCEPTED_TYPES.join(",")}
            onChange={handleFile}
            disabled={busy}
          />
          <Button variant="secondary" onClick={() => inputRef.current?.click()} disabled={busy}>
            <Icon name="camera" size={16} />
            {user.avatarUrl ? "Cambiar foto" : "Subir foto"}
          </Button>
          {user.avatarUrl && (
            <Button variant="danger" onClick={() => void changeAvatar(async () => null)} disabled={busy}>
              <Icon name="trash" size={16} />
              Quitar foto
            </Button>
          )}
        </div>
      </div>
      {error && <Alert tone="danger">{error}</Alert>}
    </Card>
  );
}
