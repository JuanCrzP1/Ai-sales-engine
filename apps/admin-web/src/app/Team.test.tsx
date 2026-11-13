import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it } from "vitest";
import { assignableRoles, expiryText, invitationMessage, invitationUrl, memberActions, type TeamMember } from "../domain/team/team";
import { createMemoryBackend, createMemoryTeam, createTestServices, createVerifyingAuthService, TEST_ACCOUNT } from "../test/fakes";
import { SAMPLE_DOCUMENT } from "../test/fixtures/sampleDocument";
import { App } from "./App";

afterEach(cleanup);

const SLUG = SAMPLE_DOCUMENT.tenant_slug;
const member = (role: TeamMember["role"], me = false): TeamMember => ({ userId: role + String(me), email: `${role}@x.co`, role, joinedAt: "2026-11-01T00:00:00Z", me });

describe("Reglas del equipo en el panel", () => {
  it("solo un dueño da el rol de dueño", () => {
    expect(assignableRoles("owner")).toEqual(["owner", "admin", "agent"]);
    expect(assignableRoles("admin")).toEqual(["admin", "agent"]);
  });

  it("explica por qué no se puede tocar a alguien, como el servidor", () => {
    expect(memberActions("owner", member("owner", true), 1)).toMatchObject({ changeRole: false, reason: "Eres tú." });
    expect(memberActions("admin", member("owner"), 2)).toMatchObject({ remove: false, reason: "Solo un dueño toca a otro dueño." });
    expect(memberActions("owner", member("owner"), 1)).toMatchObject({ remove: false, reason: "Es el único dueño." });
    expect(memberActions("admin", member("agent"), 1)).toEqual({ changeRole: true, remove: true });
  });

  it("arma el enlace y el mensaje para WhatsApp", () => {
    const url = invitationUrl("https://panel.example.com/", "inv_abc");
    expect(url).toBe("https://panel.example.com/invitacion/inv_abc");
    expect(invitationMessage("Café Aroma", "agent", url)).toBe(`Te invito a Café Aroma en AI Sales Engine como Asesor. Entra con este enlace (vence en 7 días): ${url}`);
    const now = new Date("2026-11-12T12:00:00Z");
    expect(expiryText("2026-11-19T13:00:00Z", now)).toBe("Vence en 7 días");
    expect(expiryText("2026-11-13T13:00:00Z", now)).toBe("Vence mañana");
    expect(expiryText("2026-11-12T11:00:00Z", now)).toBe("Venció");
  });
});

async function openAs(path: string, { role = "owner" as const, team = createMemoryTeam(), signedIn = true }: { role?: "owner" | "admin" | "agent"; team?: ReturnType<typeof createMemoryTeam>; signedIn?: boolean } = {}) {
  const backend = createMemoryBackend([SAMPLE_DOCUMENT]);
  backend.roles.set(SLUG, role);
  const auth = createVerifyingAuthService();
  if (signedIn) await auth.signUp({ ...TEST_ACCOUNT });
  window.history.pushState({}, "", path);
  const user = userEvent.setup();
  render(<App services={createTestServices(backend, { auth, team })} />);
  return { user, team };
}

describe("Configuración → Equipo", () => {
  it("el dueño invita con un enlace que se ve una sola vez", async () => {
    const { user, team } = await openAs(`/negocios/${SLUG}/configuracion/equipo`);
    expect(await screen.findByRole("heading", { level: 1, name: "Equipo" })).toBeInTheDocument();
    const people = screen.getByRole("region", { name: /Personas/ });
    expect(within(people).getByText("Tú")).toBeInTheDocument();
    // A sí mismo no se cambia el rol.
    expect(within(people).queryByRole("combobox", { name: "Rol de operador@example.com" })).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /Invitar/ }));
    const dialog = screen.getByRole("dialog", { name: "Invitar al equipo" });
    expect(within(dialog).getByLabelText(/^Rol/)).toHaveValue("agent");
    await user.click(within(dialog).getByRole("button", { name: "Crear invitación" }));
    expect(await within(dialog).findByText(/Escribe el correo de la persona/)).toBeInTheDocument();
    await user.type(within(dialog).getByLabelText(/^Correo/), "Pedro@Tienda.com");
    await user.click(within(dialog).getByRole("button", { name: "Crear invitación" }));

    const link = await screen.findByRole("dialog", { name: "Invitación lista" });
    expect(within(link).getByText(`${window.location.origin}/invitacion/inv_prueba_1`)).toBeInTheDocument();
    expect(within(link).getByRole("link", { name: /Enviar por WhatsApp/ }).getAttribute("href")).toContain("https://wa.me/?text=");
    expect(within(link).getByText(/no lo volvemos a mostrar/)).toBeInTheDocument();
    await user.click(within(link).getByRole("button", { name: "Listo" }));

    const invitations = screen.getByRole("region", { name: /Invitaciones sin usar/ });
    expect(await within(invitations).findByText("pedro@tienda.com")).toBeInTheDocument();
    expect(within(invitations).getByText(/Asesor · Vence en/)).toBeInTheDocument();
    expect(team.invitations).toHaveLength(1);

    await user.click(within(invitations).getByRole("button", { name: "Nuevo enlace" }));
    const renewed = await screen.findByRole("dialog", { name: "Nuevo enlace de invitación" });
    expect(within(renewed).getByText(/El enlace anterior ya no sirve/)).toBeInTheDocument();
    await user.click(within(renewed).getByRole("button", { name: "Listo" }));

    await user.click(within(invitations).getByRole("button", { name: "Retirar la invitación de pedro@tienda.com" }));
    await user.click(within(screen.getByRole("dialog", { name: /Retirar la invitación/ })).getByRole("button", { name: "Sí, retirar" }));
    await waitFor(() => expect(team.invitations).toHaveLength(0));
  });

  it("cambia el rol y quita a alguien, y muestra lo que el servidor no deja", async () => {
    const { user, team } = await openAs(`/negocios/${SLUG}/configuracion/equipo`);
    const select = await screen.findByRole("combobox", { name: "Rol de laura@example.com" });
    await user.selectOptions(select, "admin");
    await waitFor(() => expect(team.members.find((item) => item.userId === "laura")?.role).toBe("admin"));

    await user.click(screen.getByRole("button", { name: "Quitar a laura@example.com" }));
    const dialog = screen.getByRole("dialog", { name: /Quitar a laura@example.com/ });
    expect(within(dialog).getByText(/Lo que hizo .* se conserva/)).toBeInTheDocument();
    await user.click(within(dialog).getByRole("button", { name: "Sí, quitar" }));
    await waitFor(() => expect(screen.queryByText("laura@example.com")).not.toBeInTheDocument());
  });

  it("un administrador no puede tocar al dueño ni darle ese rol a nadie", async () => {
    const team = createMemoryTeam({
      myRole: "admin",
      members: [
        { userId: "dueno", email: "dueno@example.com", role: "owner", joinedAt: "2026-11-01T00:00:00Z", me: false },
        { userId: "yo", email: "admin@example.com", role: "admin", joinedAt: "2026-11-02T00:00:00Z", me: true },
        { userId: "laura", email: "laura@example.com", role: "agent", joinedAt: "2026-11-03T00:00:00Z", me: false },
      ],
    });
    await openAs(`/negocios/${SLUG}/configuracion/equipo`, { role: "admin", team });
    const people = await screen.findByRole("region", { name: /Personas/ });
    expect(within(people).getByTitle("Solo un dueño toca a otro dueño.")).toHaveTextContent("Dueño");
    expect(within(people).queryByRole("button", { name: "Quitar a dueno@example.com" })).not.toBeInTheDocument();
    const options = within(within(people).getByRole("combobox", { name: "Rol de laura@example.com" })).getAllByRole("option");
    expect(options.map((option) => option.textContent)).toEqual(["Administrador", "Asesor"]);
  });
});

describe("Lo que ve un asesor", () => {
  it("solo atiende: el menú no tiene la configuración del negocio ni los reportes", async () => {
    await openAs(`/negocios/${SLUG}`, { role: "agent" });
    expect(await screen.findByRole("region", { name: "Atajos" })).toBeInTheDocument();
    const menu = screen.getByRole("navigation", { name: "Menú del negocio" });
    expect(within(menu).getAllByRole("link").map((link) => link.textContent?.trim())).toEqual(["Inicio", "Conversaciones", "Clientes", "Ventas", "Ayuda", "Configuración"]);
    expect(screen.queryByText("Estado de la configuración")).not.toBeInTheDocument();
  });

  it("en Configuración solo ve las respuestas rápidas", async () => {
    await openAs(`/negocios/${SLUG}/configuracion`, { role: "agent" });
    expect(await screen.findByRole("heading", { level: 1, name: "Respuestas rápidas" })).toBeInTheDocument();
    const settings = screen.getByRole("navigation", { name: "Configuración" });
    expect(within(settings).getAllByRole("link").map((link) => link.textContent)).toEqual([expect.stringContaining("Respuestas rápidas")]);
  });

  it.each(["reportes", "asistente", "canales", "integraciones/claves", "configuracion/inteligencia-artificial", "configuracion/equipo"])(
    "si abre /%s con un enlace guardado, ve por qué no puede",
    async (path) => {
      await openAs(`/negocios/${SLUG}/${path}`, { role: "agent" });
      expect(await screen.findByRole("heading", { level: 1, name: "Tu rol no permite ver esta pantalla" })).toBeInTheDocument();
      expect(screen.getByText(/Eres Asesor en este negocio/)).toBeInTheDocument();
      expect(screen.getByRole("link", { name: "Ir a Conversaciones" })).toHaveAttribute("href", `/negocios/${SLUG}/conversaciones`);
    },
  );
});

describe("Aceptar una invitación", () => {
  async function invited(email: string) {
    const team = createMemoryTeam();
    const issued = await team.invite(SLUG, { email, role: "agent" });
    return { team, token: issued.token };
  }

  it("sin sesión, dice de qué negocio es y lleva a crear la cuenta o entrar", async () => {
    const { team, token } = await invited("nuevo@example.com");
    await openAs(`/invitacion/${token}`, { team, signedIn: false });
    expect(await screen.findByRole("heading", { level: 1, name: "Únete a Café Aroma" })).toBeInTheDocument();
    expect(screen.getByText("nuevo@example.com")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Crear mi cuenta" })).toHaveAttribute("href", "/crear-cuenta");
    expect(screen.getByRole("link", { name: "Ya tengo cuenta" })).toHaveAttribute("href", "/iniciar-sesion");
  });

  it("con la cuenta del correo invitado, entra al negocio", async () => {
    const { team, token } = await invited(TEST_ACCOUNT.email);
    team.acceptAs = TEST_ACCOUNT.email;
    const { user } = await openAs(`/invitacion/${token}`, { team });
    await user.click(await screen.findByRole("button", { name: "Aceptar y entrar a Café Aroma" }));
    await waitFor(() => expect(window.location.pathname).toBe(`/negocios/${SLUG}`));
    expect(team.accepted).toEqual([TEST_ACCOUNT.email]);
  });

  it("con otra cuenta, pide entrar con la del correo invitado", async () => {
    const { team, token } = await invited("otra@example.com");
    await openAs(`/invitacion/${token}`, { team });
    expect(await screen.findByText(`Entraste como ${TEST_ACCOUNT.email}`)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Aceptar y entrar/ })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Cerrar sesión" })).toBeInTheDocument();
  });

  it("un enlace que no sirve dice por qué", async () => {
    await openAs("/invitacion/inv_no-existe", { signedIn: false });
    expect(await screen.findByRole("heading", { level: 1, name: "Esta invitación no sirve" })).toBeInTheDocument();
    expect(screen.getByText(/Pídele a quien te invitó uno nuevo/)).toBeInTheDocument();
  });
});
