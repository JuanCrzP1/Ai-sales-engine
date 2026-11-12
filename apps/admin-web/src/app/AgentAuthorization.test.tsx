import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { leavePanel } from "../features/integrations/OAuthConsentPage";
import { createMemoryAgentAuthorization, createMemoryBackend, createTestServices, createVerifyingAuthService } from "../test/fakes";
import { SAMPLE_DOCUMENT } from "../test/fixtures/sampleDocument";
import { App } from "./App";

/**
 * Conectar un agente iniciando sesión (Claude web y app, ChatGPT): el agente abre `/oauth/authorize` con sus parámetros, la
 * persona ve quién pide acceso, elige negocios y permisos, y autoriza o cancela; el navegador vuelve al agente.
 */

const CALLBACK = "https://claude.ai/api/mcp/auth_callback";
const QUERY = new URLSearchParams({
  client_id: "claude", redirect_uri: CALLBACK, response_type: "code", code_challenge: "c".repeat(43), code_challenge_method: "S256", state: "xyz",
}).toString();

afterEach(cleanup);
beforeEach(() => {
  vi.restoreAllMocks();
});

async function open(query = QUERY, services = {}) {
  window.history.pushState({}, "", `/oauth/authorize?${query}`);
  const user = userEvent.setup();
  const authorization = createMemoryAgentAuthorization();
  const went = vi.spyOn(leavePanel, "to").mockImplementation(() => undefined);
  render(<App services={createTestServices(createMemoryBackend([SAMPLE_DOCUMENT]), { agentAuthorization: authorization, ...services })} />);
  return { user, authorization, went };
}

describe("Autorizar a un agente", () => {
  it("dice quién pide acceso y, al autorizar, vuelve al agente con lo que se eligió", async () => {
    const { user, authorization, went } = await open();
    expect(await screen.findByRole("heading", { level: 1, name: "Conectar «Claude»" })).toBeInTheDocument();
    expect(screen.getByText("claude.ai")).toBeInTheDocument();
    // Conversar con el asistente no es de un agente: no se ofrece.
    expect(screen.queryByRole("radiogroup", { name: "Conversar con el asistente" })).not.toBeInTheDocument();
    await user.click(within(screen.getByRole("radiogroup", { name: "Conversaciones" })).getByRole("radio", { name: "Ver" }));
    await user.click(screen.getByRole("button", { name: "Autorizar" }));
    await waitFor(() => expect(went).toHaveBeenCalledWith(`${CALLBACK}?code=codigo-de-prueba&state=xyz`));
    expect(authorization.decisions[0]).toMatchObject({
      approve: true, reach: "all", businesses: [], permissions: { businesses: "write", assistant: "write", conversations: "read" },
    });
    expect(authorization.decisions[0]!.params.client_id).toBe("claude");
  });

  it("con algunos negocios, se eligen; sin elegir, dice qué falta", async () => {
    const { user, authorization } = await open();
    await screen.findByRole("heading", { level: 1, name: "Conectar «Claude»" });
    await user.click(screen.getByRole("radio", { name: /Algunos/ }));
    await user.click(screen.getByRole("button", { name: "Autorizar" }));
    expect(await screen.findByText("Elige al menos un negocio.")).toBeInTheDocument();
    await user.click(screen.getByRole("checkbox", { name: "Café Aroma" }));
    await user.click(screen.getByRole("button", { name: "Autorizar" }));
    await waitFor(() => expect(authorization.decisions[0]).toMatchObject({ reach: "some", businesses: [SAMPLE_DOCUMENT.tenant_slug] }));
  });

  it("cancelar vuelve al agente con el rechazo", async () => {
    const { user, authorization, went } = await open();
    await screen.findByRole("heading", { level: 1, name: "Conectar «Claude»" });
    await user.click(screen.getByRole("button", { name: "Cancelar" }));
    await waitFor(() => expect(went).toHaveBeenCalledWith(`${CALLBACK}?error=access_denied&state=xyz`));
    expect(authorization.decisions[0]).toEqual({ approve: false, params: expect.objectContaining({ client_id: "claude" }) });
  });

  it("una solicitud que no sirve lo dice y no deja autorizar", async () => {
    await open(QUERY.replace("client_id=claude", "client_id=desconocido"));
    expect(await screen.findByRole("heading", { level: 1, name: "No se puede conectar" })).toBeInTheDocument();
    expect(screen.getByText("El agente no está registrado. Vuelve a conectarlo desde su programa.")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Autorizar" })).not.toBeInTheDocument();
  });

  it("sin sesión, pide entrar y después vuelve a la autorización con sus parámetros", async () => {
    const auth = createVerifyingAuthService();
    await auth.signUp({ name: "Laura", email: "laura@empresa.com", password: "una-clave-segura-1" });
    await auth.signOut();
    const { user } = await open(QUERY, { auth });
    expect(await screen.findByRole("heading", { name: "Bienvenido de nuevo" })).toBeInTheDocument();
    await user.type(screen.getByLabelText(/Correo/), "laura@empresa.com");
    await user.type(screen.getByLabelText(/^Contraseña/), "una-clave-segura-1");
    await user.click(screen.getByRole("button", { name: "Iniciar sesión" }));
    expect(await screen.findByRole("heading", { level: 1, name: "Conectar «Claude»" })).toBeInTheDocument();
    expect(window.location.search).toContain("client_id=claude");
  });
});
