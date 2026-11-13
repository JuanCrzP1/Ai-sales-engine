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
  return /^\d{6,20}$/.test(value.replace(/[\s.-]+/g, ""));
}

/** Celular de cualquier país: 7 a 15 dígitos, con o sin «+» (espacios, puntos y guiones permitidos). */
export function isPhone(value: string): boolean {
  return /^\+?\d{7,15}$/.test(value.replace(/[\s.-]+/g, ""));
}

export function isEmail(value: string): boolean {
  const text = value.trim();
  return text.length <= 200 && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(text);
}

/** La CLABE mexicana: 18 dígitos y el último es su dígito de control (pesos 3, 7, 1). */
export function isClabe(value: string): boolean {
  const digits = value.replace(/[\s.-]+/g, "");
  if (!/^\d{18}$/.test(digits)) return false;
  const weights = [3, 7, 1];
  const total = [...digits.slice(0, 17)].reduce((sum, digit, index) => sum + ((Number(digit) * weights[index % 3]!) % 10), 0);
  return (10 - (total % 10)) % 10 === Number(digits[17]);
}

/** El IBAN: país, dígitos de control y cuenta; se comprueba con el módulo 97, como lo hacen los bancos. */
export function isIban(value: string): boolean {
  const compact = value.replace(/\s+/g, "").toUpperCase();
  if (!/^[A-Z]{2}\d{2}[A-Z0-9]{11,30}$/.test(compact)) return false;
  const digits = [...(compact.slice(4) + compact.slice(0, 4))].map((char) => parseInt(char, 36).toString()).join("");
  let remainder = 0;
  for (const digit of digits) remainder = (remainder * 10 + Number(digit)) % 97;
  return remainder === 1;
}

export function isPositiveAmount(value: number | null): boolean {
  return value !== null && Number.isFinite(value) && value > 0;
}
