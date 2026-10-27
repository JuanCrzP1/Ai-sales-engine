import logoFull from "../../assets/brand/logo-full.png";

/** Logotipo completo (ícono + "AI Sales Engine"). */
export function BrandLogo({ width = 220 }: { width?: number }) {
  return <img className="brand-logo" src={logoFull} alt="AI Sales Engine" width={width} height={Math.round((width * 380) / 860)} />;
}
