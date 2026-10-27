import { initials } from "../../lib/text";

interface AvatarProps {
  name: string;
  src?: string | null;
  size?: "sm" | "md" | "lg" | "xl";
}

/** Foto de perfil o, si no hay, las iniciales sobre el degradado de la marca. Decorativo. */
export function Avatar({ name, src, size = "md" }: AvatarProps) {
  return (
    <span className={`avatar avatar--${size}`} aria-hidden="true">
      {src ? <img className="avatar__image" src={src} alt="" /> : <span className="avatar__initials">{initials(name) || "?"}</span>}
    </span>
  );
}
