import { PersistenceError } from "../../repositories/persistenceError";
import { failingStorage } from "../../test/fakes";
import { SAMPLE_CONFIG } from "../../test/fixtures/sampleConfig";
import { configStorageKey, createLocalConfigRepository } from "./localConfigRepository";

async function expectPersistenceError(promise: Promise<unknown>, code: PersistenceError["code"]) {
  const error = await promise.then(
    () => null,
    (caught: unknown) => caught,
  );
  expect(error).toBeInstanceOf(PersistenceError);
  expect((error as PersistenceError).code).toBe(code);
}

describe("createLocalConfigRepository", () => {
  it("guarda y recupera la configuración", async () => {
    const repo = createLocalConfigRepository("cuenta-1", window.localStorage);
    expect(await repo.load()).toBeNull();
    const stored = await repo.save(SAMPLE_CONFIG);
    expect(await repo.load()).toEqual(stored);
    await repo.clear();
    expect(await repo.load()).toBeNull();
  });

  it("separa la configuración de cada cuenta", async () => {
    await createLocalConfigRepository("cuenta-1", window.localStorage).save(SAMPLE_CONFIG);
    expect(await createLocalConfigRepository("cuenta-2", window.localStorage).load()).toBeNull();
  });

  it("informa los datos corruptos o con otra forma en vez de ignorarlos", async () => {
    // Antes se devolvía null y el panel acababa sobrescribiendo esos datos con una configuración vacía.
    const repo = createLocalConfigRepository("cuenta-1", window.localStorage);
    window.localStorage.setItem(configStorageKey("cuenta-1"), "{no es json");
    await expectPersistenceError(repo.load(), "corrupted");
    window.localStorage.setItem(configStorageKey("cuenta-1"), JSON.stringify({ config: { version: 2 }, savedAt: "x" }));
    await expectPersistenceError(repo.load(), "corrupted");
    expect(window.localStorage.getItem(configStorageKey("cuenta-1"))).toContain('"version":2');
  });

  it("rechaza el guardado cuando no hay almacenamiento disponible", async () => {
    const repo = createLocalConfigRepository("cuenta-1", null);
    await expectPersistenceError(repo.save(SAMPLE_CONFIG), "unavailable");
  });

  it("rechaza el guardado cuando el almacenamiento está lleno", async () => {
    const repo = createLocalConfigRepository("cuenta-1", failingStorage("quota"));
    await expectPersistenceError(repo.save(SAMPLE_CONFIG), "quota_exceeded");
  });

  it("rechaza la carga cuando el navegador bloquea el almacenamiento", async () => {
    const repo = createLocalConfigRepository("cuenta-1", failingStorage("blocked"));
    await expectPersistenceError(repo.load(), "unavailable");
  });
});
