import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it } from "vitest";
import { createMemoryBackend, createTestServices } from "../test/fakes";
import { SAMPLE_DOCUMENT } from "../test/fixtures/sampleDocument";
import { App } from "./App";

afterEach(cleanup);

const CAFE = SAMPLE_DOCUMENT.tenant_slug;

/** Un negocio con la versión 1 publicada y, si se pide, una versión 2 guardada con la marca nueva. */
async function business({ published = true, savedBrand }: { published?: boolean; savedBrand?: string } = {}) {
  const backend = createMemoryBackend([SAMPLE_DOCUMENT]);
  const repository = backend.createConfigRepository(CAFE);
  if (published) await repository.publish(1);
  if (savedBrand) {
    const { document } = await repository.load();
    await repository.save({ document: { ...document!, identity: { ...document!.identity, brand_name: savedBrand } }, paymentValues: {}, baseVersion: 1 });
  }
  return backend;
}

async function open(path: string, backend: Awaited<ReturnType<typeof business>>) {
  window.history.pushState({}, "", `/negocios/${CAFE}/${path}`);
  const user = userEvent.setup();
  render(<App services={createTestServices(backend)} />);
  await waitFor(() => expect(screen.queryByText(/Abriendo tu panel…|Cargando/)).not.toBeInTheDocument());
  return user;
}

const status = () => screen.getByRole("status", { name: "Estado del guardado y la publicación" });

describe("Cambios sin publicar", () => {
  it("guardado no es publicado: el editor y el menú avisan, y Revisar dice exactamente qué cambia", async () => {
    const user = await open("negocio", await business({ savedBrand: "Ai sales engine" }));
    await waitFor(() => expect(status()).toHaveTextContent(/^Guardado · .+ · Cambios sin publicar$/));
    const menu = screen.getByRole("navigation", { name: "Menú del negocio" });
    expect(within(menu).getByRole("img", { name: "Cambios sin publicar" })).toBeInTheDocument();

    await user.click(screen.getByRole("link", { name: "Revisar y publicar" }));
    const changes = await screen.findByRole("region", { name: "Lo que cambia al publicar" });
    expect(within(changes).getByRole("heading", { name: "Lo que cambia al publicar 1" })).toBeInTheDocument();
    expect(within(changes).getByText("Mi negocio")).toBeInTheDocument();
    expect(within(changes).getByText("Marca")).toBeInTheDocument();
    expect(within(changes).getByText("Nuevo")).toBeInTheDocument();
    expect(within(changes).getByText("Ai sales engine")).toBeInTheDocument();

    const publish = await screen.findByRole("button", { name: "Publicar versión 2" });
    await waitFor(() => expect(publish).toBeEnabled());
    await user.click(publish);
    await waitFor(() => expect(status()).toHaveTextContent("Publicado · es lo que responde a tus clientes"));
    expect(within(menu).queryByRole("img", { name: "Cambios sin publicar" })).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Todo está publicado" })).toBeInTheDocument();
  });

  it("compara el contenido y no el número de versión: guardar sin cambiar nada no deja nada pendiente", async () => {
    const backend = await business();
    const repository = backend.createConfigRepository(CAFE);
    const { document } = await repository.load();
    await repository.save({ document: document!, paymentValues: {}, baseVersion: 1 });
    await open("negocio", backend);
    await waitFor(() => expect(status()).toHaveTextContent("Publicado · es lo que responde a tus clientes"));
    expect(screen.queryByRole("link", { name: "Revisar y publicar" })).not.toBeInTheDocument();
  });

  it("si nunca se ha publicado lo dice, y en Revisar explica que es la primera vez", async () => {
    const user = await open("negocio", await business({ published: false }));
    await waitFor(() => expect(status()).toHaveTextContent(/Sin publicar todavía$/));
    await user.click(screen.getByRole("link", { name: "Revisar y publicar" }));
    expect(await screen.findByRole("heading", { name: "Primera publicación" })).toBeInTheDocument();
  });

  it("al probar avisa que se prueban cambios que los clientes todavía no ven", async () => {
    await open("probar", await business({ savedBrand: "Ai sales engine" }));
    expect(await screen.findByText("Estás probando cambios que tus clientes todavía no ven")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Revisar y publicar" })).toHaveAttribute("href", `/negocios/${CAFE}/revision`);
  });
});
