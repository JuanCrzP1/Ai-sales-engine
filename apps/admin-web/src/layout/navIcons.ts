import type { IconName } from "../components/ui/Icon";
import type { NavItem } from "../navigation/navItems";

/** Ícono de cada destino de la navegación. */
export const NAV_ICONS: Record<NavItem["key"], IconName> = {
  home: "home",
  business: "store",
  catalog: "box",
  payments: "card",
  assistant: "sparkles",
  messages: "chat",
  review: "check",
};
