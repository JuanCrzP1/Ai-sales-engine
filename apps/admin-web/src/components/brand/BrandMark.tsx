import logoMark from "../../assets/brand/logo-mark.png";

/** Ícono de la marca (burbuja con flecha). Decorativo: el nombre siempre va en texto al lado. */
export function BrandMark({ size = 36 }: { size?: number }) {
  return <img className="brand-mark" src={logoMark} alt="" width={size} height={size} />;
}
