import { PersistenceError, persistenceErrorMessage } from "../../repositories/persistenceError";
import { createApiBusinessDirectory } from "./apiBusinessDirectory";
import { createApiConfigRepository } from "./apiConfigRepository";
import { createHttpClient } from "./httpClient";

const respond = (status: number, body?: unknown) => new Response(body === undefined ? null : JSON.stringify(body), { status });

function stubFetch(result: Response | Error) {
  const mock = vi.fn(async (url: string, init?: RequestInit) => {
    void url;
    void init;
    if (result instanceof Error) throw result;
    return result;
  });
  vi.stubGlobal("fetch", mock);
  return mock;
}

async function failure(promise: Promise<unknown>): Promise<PersistenceError> {
  try {
    await promise;
  } catch (error) {
    if (error instanceof PersistenceError) return error;
    throw error;
  }
  throw new Error("Debía fallar.");
}

afterEach(() => vi.unstubAllGlobals());

describe("cliente de la API local", () => {
  it("por defecto llama por el proxy del mismo origen, nunca a otro servidor", async () => {
    const mock = stubFetch(respond(200, []));
    await createHttpClient().get("/businesses");
    expect(mock.mock.calls[0]?.[0]).toBe("/api/businesses");
  });

  it("convierte una caída de la conexión en un error que se puede informar", async () => {
    stubFetch(new TypeError("Failed to fetch"));
    const error = await failure(createHttpClient().get("/businesses"));
    expect(error.code).toBe("unavailable");
    expect(persistenceErrorMessage(error)).toMatch(/No se pudo conectar con el servidor local/);
  });

  it("trata como caída un proxy sin servidor detrás", async () => {
    stubFetch(respond(502));
    expect((await failure(createHttpClient().get("/businesses"))).code).toBe("unavailable");
  });

  it("conserva el código, el mensaje y los problemas por campo del servidor", async () => {
    stubFetch(respond(422, { code: "invalid", message: "Hay datos por corregir.", issues: [{ path: "identity.name", message: "Obligatorio." }] }));
    const error = await failure(createHttpClient().put("/businesses/a/config", {}));
    expect(error.code).toBe("invalid");
    expect(persistenceErrorMessage(error)).toBe("Hay datos por corregir.");
    expect(error.problems).toEqual([{ path: "identity.name", message: "Obligatorio." }]);
  });

  it("un cuerpo inesperado no oculta el fallo", async () => {
    stubFetch(new Response("<html>", { status: 500 }));
    const error = await failure(createHttpClient().get("/businesses"));
    expect(error.code).toBe("unknown");
    expect(persistenceErrorMessage(error)).toBe("No se pudo completar la operación.");
  });
});

describe("repositorios sobre la API", () => {
  it("el guardado envía documento, valores de pago y versión de partida", async () => {
    const mock = stubFetch(respond(200, { slug: "a", name: "A", latest_version: 2, draft_version: 2, published_version: null, document: {}, version: { version: 2, status: "draft", created_at: "x", published_at: null } }));
    const stored = await createApiConfigRepository(createHttpClient(), "a").save({ document: { tenant_slug: "a" } as never, paymentValues: { ref: "valor" }, baseVersion: 1 });
    const [url, init] = mock.mock.calls[0]!;
    expect(url).toBe("/api/businesses/a/config");
    expect(init?.method).toBe("PUT");
    expect(JSON.parse(String(init?.body))).toEqual({ document: { tenant_slug: "a" }, payment_values: { ref: "valor" }, base_version: 1 });
    expect(stored).toMatchObject({ latestVersion: 2, publishedVersion: null, version: { version: 2, status: "draft", createdAt: "x" } });
  });

  it("eliminar envía la confirmación con el identificador del negocio", async () => {
    const mock = stubFetch(respond(204));
    await createApiBusinessDirectory(createHttpClient()).remove("mi_negocio");
    expect(mock.mock.calls[0]?.[0]).toBe("/api/businesses/mi_negocio?confirm=mi_negocio");
    expect(mock.mock.calls[0]?.[1]?.method).toBe("DELETE");
  });

  it("escapa el identificador en la ruta para no alcanzar otro recurso", async () => {
    const mock = stubFetch(respond(200, { slug: "x", name: "x", latest_version: null, draft_version: null, published_version: null, document: null, version: null }));
    await createApiConfigRepository(createHttpClient(), "../otro").load();
    expect(mock.mock.calls[0]?.[0]).toBe("/api/businesses/..%2Fotro/config");
  });
});
