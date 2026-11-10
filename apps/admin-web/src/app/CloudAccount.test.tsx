import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it } from "vitest";
import { createMemoryBackend, createTestServices, createVerifyingAuthService } from "../test/fakes";
import { SAMPLE_DOCUMENT } from "../test/fixtures/sampleDocument";
import { App } from "./App";

afterEach(cleanup);

/** El panel en la nube: con cuentas, sin importar YAML ni eliminar negocios. */
function cloudServices() {
  const backend = createMemoryBackend([SAMPLE_DOCUMENT]);
  return createTestServices(backend, { auth: createVerifyingAuthService(), directory: { ...backend.directory, canImportExisting: false, canRemove: false } });
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

    await waitFor(() => expect(screen.getByRole("heading", { level: 1, name: "Tus negocios" })).toBeInTheDocument());
    expect(screen.getByText("Tu cuenta")).toBeInTheDocument();
    expect(await screen.findByRole("link", { name: `Abrir ${SAMPLE_DOCUMENT.identity.name}` })).toBeInTheDocument();
    expect(screen.queryByText("Solo en este equipo")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Importar negocios existentes" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /^Eliminar/ })).not.toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "Crear negocio" }).length).toBeGreaterThan(0);
  });
});
