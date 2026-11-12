import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it } from "vitest";
import { createMemoryBackend, createTestServices, createVerifyingAuthService } from "../test/fakes";
import { SAMPLE_DOCUMENT } from "../test/fixtures/sampleDocument";
import { App } from "./App";

afterEach(cleanup);

/** El panel en la nube: con cuentas y sin importar los negocios de ejemplo. */
function cloudServices() {
  const backend = createMemoryBackend([SAMPLE_DOCUMENT]);
  return createTestServices(backend, { auth: createVerifyingAuthService(), directory: { ...backend.directory, canImportExisting: false } });
}

describe("panel en la nube", () => {
  it("pide entrar o crear una cuenta, y después muestra solo lo que aplica en la nube", async () => {
    window.history.pushState({}, "", "/");
    const user = userEvent.setup({ applyAccept: false });
    render(<App services={cloudServices()} />);

    await user.click(await screen.findByRole("link", { name: "Crear cuenta" }));
    await user.type(await screen.findByLabelText(/Tu nombre/), "Camilo");
    await user.type(screen.getByLabelText(/Correo electrónico/), "camilo@example.com");
    await user.type(screen.getByLabelText(/^Contraseña/), "clave-segura-1");
    await user.type(screen.getByLabelText(/Confirmar contraseña/), "clave-segura-1");
    await user.click(screen.getByRole("button", { name: "Crear cuenta" }));

    await waitFor(() => expect(screen.getByRole("heading", { level: 1, name: SAMPLE_DOCUMENT.identity.name })).toBeInTheDocument());
    expect(window.location.pathname).toBe(`/negocios/${SAMPLE_DOCUMENT.tenant_slug}`);
    expect(screen.queryByText("Solo en este equipo")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /^Negocio/ }));
    expect(await screen.findByRole("menuitem", { name: SAMPLE_DOCUMENT.identity.name })).toBeInTheDocument();
    expect(screen.getByRole("menuitem", { name: "Crear negocio" })).toBeInTheDocument();
    expect(screen.queryByRole("menuitem", { name: "Administrar negocios" })).not.toBeInTheDocument();
  });
});
