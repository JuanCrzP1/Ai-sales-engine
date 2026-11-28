import { BRAND_NAME } from "../../lib/brand";
import { BrandMark } from "./BrandMark";

/** Logotipo completo: el ícono con el nombre al lado. `size`: el alto del ícono. */
export function BrandLogo({ size = 48 }: { size?: number }) {
  return (
    <span className="brand-logo">
      <BrandMark size={size} />
      <span className="brand-logo__name">{BRAND_NAME}</span>
    </span>
  );
}
