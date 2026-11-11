import { useEffect, useState } from "react";

/** Pantallas de celular y tableta vertical: el menú pasa a una barra superior con ☰ y un panel que se desliza. */
export const COMPACT_SCREEN = "(max-width: 900px)";

function matches(query: string): boolean {
  return typeof window !== "undefined" && typeof window.matchMedia === "function" && window.matchMedia(query).matches;
}

/** Si la pantalla cumple la consulta, y se actualiza al girar el celular o cambiar el tamaño de la ventana. */
export function useMediaQuery(query: string): boolean {
  const [active, setActive] = useState(() => matches(query));

  useEffect(() => {
    if (typeof window.matchMedia !== "function") return;
    const list = window.matchMedia(query);
    const update = () => setActive(list.matches);
    update();
    list.addEventListener("change", update);
    return () => list.removeEventListener("change", update);
  }, [query]);

  return active;
}
