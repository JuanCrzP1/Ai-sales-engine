import { PageHeader } from "../../components/ui/Layout";
import { AvatarEditor } from "./AvatarEditor";
import { DangerZoneCard } from "./DangerZoneCard";
import { ProfileDetailsForm } from "./ProfileDetailsForm";
import { SessionCard } from "./SessionCard";

export function ProfilePage() {
  return (
    <>
      <PageHeader eyebrow="Cuenta" title="Mi perfil" description="Tu foto, tus datos y tu sesión." />
      <AvatarEditor />
      <ProfileDetailsForm />
      <SessionCard />
      <DangerZoneCard />
    </>
  );
}
