/** Formatos de presentación (es-CO). */

export function formatPrice(amount: number | null, currency: string): string {
  if (amount === null || Number.isNaN(amount)) return "Sin precio";
  return new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency,
    maximumFractionDigits: currency === "COP" ? 0 : 2,
  }).format(amount);
}

export function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString("es-CO", { hour: "2-digit", minute: "2-digit" });
}

export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString("es-CO", { dateStyle: "long", timeStyle: "short" });
}
