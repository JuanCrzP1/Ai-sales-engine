import { useEffect, useState } from "react";

/** El valor, después de que deja de cambiar por `delay` milisegundos: para no pedirle al servidor en cada tecla. */
export function useDebounced<T>(value: T, delay = 300): T {
  const [settled, setSettled] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setSettled(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return settled;
}
