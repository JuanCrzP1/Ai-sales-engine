/** Comprobaciones primitivas reutilizables. No conocen el modelo de configuración. */

export function isBlank(value: string): boolean {
  return value.trim().length === 0;
}

export function isHttpUrl(value: string): boolean {
  try {
    const url = new URL(value.trim());
    return url.protocol === "https:" || url.protocol === "http:";
  } catch {
    return false;
  }
}

export function isHttpsUrl(value: string): boolean {
  return isHttpUrl(value) && value.trim().toLowerCase().startsWith("https://");
}

/** Celular colombiano: 10 dígitos que empiezan por 3 (espacios permitidos). */
export function isColombianMobile(value: string): boolean {
  return /^3\d{9}$/.test(value.replace(/\s+/g, ""));
}

export function isAccountNumber(value: string): boolean {
  return /^\d{6,20}$/.test(value.replace(/[\s-]+/g, ""));
}

export function isPositiveAmount(value: number | null): boolean {
  return value !== null && Number.isFinite(value) && value > 0;
}
