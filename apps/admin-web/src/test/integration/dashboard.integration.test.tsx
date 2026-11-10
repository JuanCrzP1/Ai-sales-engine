import { cleanup, configure, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import publishedSchema from "../../../../../project/config/contracts/v1/business-config.schema.json";
import { App } from "../../app/App";
import { createLocalServices } from "../../app/compositionRoot";
import { SCHEMA_VERSION } from "../../contracts/businessConfig.v1";
import type { BusinessDocument } from "../../domain/config/types";
import { PersistenceError } from "../../repositories/persistenceError";
import { SAMPLE_DOCUMENT, SAMPLE_PLANS_DOCUMENT } from "../fixtures/sampleDocument";
import { startApiServer, type ApiServer } from "./apiServer.mjs";

/**
 * La interfaz real, en jsdom, contra la API real, BusinessConfig v1 y SQLite. Ninguna parte se sustituye: lo guardado se
 * comprueba además preguntándole directamente a la API, que se reinicia de verdad. Los datos de los negocios son ficticios.
 */

// Aquí cada espera incluye peticiones reales (importar nueve negocios, la primera tras un reinicio): un segundo no alcanza.
configure({ asyncUtilTimeout: 20_000 });

let server: ApiServer;
const setItem = vi.spyOn(Storage.prototype, "setItem");

beforeAll(async () => {
  server = await startApiServer();
});

afterAll(async () => {
  await server?.stop();
});

const LOADING = /Abriendo tu panel…|Cargando tu configuración…|Cargando negocios…/;

async function openPanel(path: string) {
  cleanup();
  window.history.pushState({}, "", path);
  const user = userEvent.setup({ applyAccept: false });
  render(<App services={createLocalServices(server.apiUrl)} />);
  await waitFor(() => {
    expect(screen.queryByText(LOADING)).not.toBeInTheDocument();
    expect(screen.getAllByRole("heading", { level: 1 }).length).toBeGreaterThan(0);
  });
  return user;
}

/** Todo el texto visible de la página. */
const document_text = () => document.body.textContent ?? "";

/** Escribe de una vez: aquí importa lo que llega al servidor, no cada tecla (eso lo prueba `App.test.tsx`). */
function fill(field: HTMLElement, value: string) {
  fireEvent.change(field, { target: { value } });
}

/** Publicar se habilita cuando llega la revisión del servidor: pulsarlo antes no haría nada. */
async function publishInPanel(user: ReturnType<typeof userEvent.setup>, version: number) {
  const button = await screen.findByRole("button", { name: `Publicar versión ${version}` });
  await waitFor(() => expect(button).toBeEnabled());
  await user.click(button);
  await screen.findByText(`Se publicó la versión ${version}.`);
}

async function saveInPanel(user: ReturnType<typeof userEvent.setup>) {
  await user.click(screen.getByRole("button", { name: "Guardar cambios" }));
  await waitFor(() => {
    expect(screen.getByText(/^Guardado ·/)).toBeInTheDocument();
  });
}

interface ApiConfig {
  slug: string;
  name: string;
  latest_version: number | null;
  draft_version: number | null;
  published_version: number | null;
  document: BusinessDocument | null;
  version: { version: number; status: string } | null;
}

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${server.apiUrl}${path}`, init);
  if (!response.ok) throw new Error(`${path}: ${response.status}`);
  return (response.status === 204 ? undefined : await response.json()) as T;
}

const apiConfig = (slug: string) => api<ApiConfig>(`/businesses/${slug}/config`);

function storedDocument(config: ApiConfig): BusinessDocument {
  if (!config.document) throw new Error(`${config.slug} no tiene documento guardado.`);
  return config.document;
}

function jsonInit(method: string, body: unknown): RequestInit {
  return { method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
}

/** Datos de pago ficticios del documento de ejemplo. */
const SAMPLE_LINK = "https://pagos.example.com/cafe-aroma-link-ficticio";
const SAMPLE_MOBILE = "3009998877";

/** Da de alta por la API un negocio con un documento ya válido, para probar la edición desde el panel. */
async function seedBusiness(slug: string, base: BusinessDocument = SAMPLE_PLANS_DOCUMENT, paymentValues: Record<string, string> = {}) {
  await api("/businesses", jsonInit("POST", { slug, name: base.identity.name }));
  const document = { ...structuredClone(base), tenant_slug: slug };
  return api<ApiConfig>(`/businesses/${slug}/config`, jsonInit("PUT", { document, payment_values: paymentValues, base_version: null }));
}

function seedCatalogBusiness(slug: string) {
  return seedBusiness(slug, SAMPLE_DOCUMENT, {
    "secret_store:principal.link": SAMPLE_LINK,
    "secret_store:principal.transfer.0.number": SAMPLE_MOBILE,
  });
}


/** Abre una pestaña del Asistente IA; si no se está en él, primero entra desde el menú lateral. */
async function openTab(user: ReturnType<typeof userEvent.setup>, name: RegExp) {
  if (!screen.queryByRole("navigation", { name: "Asistente IA" })) {
    await user.click(within(screen.getByRole("navigation", { name: "Menú del negocio" })).getByRole("link", { name: /^Asistente IA/ }));
  }
  await user.click(within(screen.getByRole("navigation", { name: "Asistente IA" })).getByRole("link", { name }));
}

describe("flujo principal: crear, recuperar, editar, guardar y sobrevivir al reinicio", () => {
  it("cumple el recorrido completo con persistencia real", async () => {
    // 1. Crear un negocio.
    let user = await openPanel("/negocios");
    await user.click(screen.getAllByRole("button", { name: "Crear negocio" })[0]!);
    const form = within(screen.getByRole("form", { name: "Crear negocio" }));
    fill(form.getByLabelText(/^Nombre comercial/), "Tienda Integración");
    expect(form.getByLabelText(/^Identificador/)).toHaveValue("tienda_integracion");
    await user.click(form.getByRole("button", { name: "Crear negocio" }));
    await screen.findByRole("heading", { level: 1, name: "Configura tu asistente de ventas" });
    expect(window.location.pathname).toBe("/negocios/tienda_integracion");
    expect((await apiConfig("tienda_integracion")).latest_version).toBeNull();

    // 2. Recuperarlo: otra apertura del panel lo encuentra en la lista.
    user = await openPanel("/negocios");
    const row = within(screen.getByText("Tienda Integración").closest("li") as HTMLElement);
    expect(row.getByText("Sin configurar")).toBeInTheDocument();
    await user.click(row.getByRole("link", { name: "Abrir Tienda Integración" }));
    await screen.findByRole("heading", { level: 1, name: "Configura tu asistente de ventas" });

    // Incompleto todavía: el servidor lo rechaza con sus propios errores y no se guarda nada.
    await openTab(user, /^Mi negocio/);
    fill(screen.getByLabelText(/^¿A qué se dedica tu negocio\?/), "tienda de barrio");
    await user.click(screen.getByRole("button", { name: "Guardar cambios" }));
    await screen.findByText("No se pudo guardar");
    expect(screen.getByText("La configuración tiene datos por corregir.")).toBeInTheDocument();
    expect((await apiConfig("tienda_integracion")).latest_version).toBeNull();
    expect(screen.getByLabelText(/^¿A qué se dedica tu negocio\?/)).toHaveValue("tienda de barrio");

    // 3 y 4. Editar y guardar.
    fill(screen.getByLabelText(/^Descripción del negocio/), "Tienda de barrio con domicilios.");
    fill(screen.getByLabelText(/^Propuesta de valor/), "Todo lo de la despensa en tu puerta.");
    await openTab(user, /^Productos y servicios/);
    await user.click(screen.getAllByRole("button", { name: "Agregar plan o servicio" })[0]!);
    const editor = within(screen.getByRole("form", { name: "Nuevo plan o servicio" }));
    fill(editor.getByLabelText(/^Nombre/), "Mercado mensual");
    fill(editor.getByLabelText(/^Precio mensual/), "120000");
    await user.click(editor.getByRole("button", { name: "Agregar plan a la lista" }));
    await saveInPanel(user);

    const saved = await apiConfig("tienda_integracion");
    expect(saved.latest_version).toBe(1);
    expect(saved.version?.status).toBe("draft");
    expect(storedDocument(saved).identity.industry).toBe("tienda de barrio");
    expect(storedDocument(saved).offer.plans?.[0]).toMatchObject({ name: "Mercado mensual", prices: [{ currency: "COP", monthly: 120000 }] });

    // 5 y 6. Reiniciar el backend y comprobar que los cambios persisten.
    await server.restart();
    expect((await apiConfig("tienda_integracion")).document).toEqual(saved.document);

    user = await openPanel("/negocios/tienda_integracion/negocio");
    expect(screen.getByLabelText(/^¿A qué se dedica tu negocio\?/)).toHaveValue("tienda de barrio");
    expect(screen.getByLabelText(/^Propuesta de valor/)).toHaveValue("Todo lo de la despensa en tu puerta.");
    await openTab(user, /^Productos y servicios/);
    expect(within(screen.getByRole("list", { name: "Productos y servicios" })).getByText("Mercado mensual")).toBeInTheDocument();
    expect(screen.queryByText("Cambios sin guardar")).not.toBeInTheDocument();
  });
});

describe("secciones comerciales guardadas en la API real", () => {
  it("7 y 8. productos, servicios, precios y promociones", async () => {
    await seedCatalogBusiness("catalogo_real");
    const user = await openPanel("/negocios/catalogo_real/productos");

    await user.click(screen.getByRole("button", { name: "Agregar producto" }));
    const editor = within(screen.getByRole("form", { name: "Nuevo producto" }));
    fill(editor.getByLabelText(/^Nombre/), "Jugo de naranja");
    fill(editor.getByLabelText(/^Categoría/), "Bebidas frías");
    fill(editor.getByLabelText(/^Precio/), "7000");
    fill(editor.getByLabelText(/^Descripción/), "Recién exprimido.");
    await user.click(editor.getByRole("button", { name: "Agregar producto a la lista" }));

    const list = within(screen.getByRole("list", { name: "Productos y servicios" }));
    await user.click(list.getByRole("button", { name: "Editar Café americano" }));
    const edit = within(screen.getByRole("form", { name: /^Editar: Café americano/ }));
    fill(edit.getByLabelText(/^Precio/), "6500");
    await user.click(edit.getByRole("button", { name: "Aplicar cambios" }));

    const croissant = within(list.getByText("Croissant de mantequilla").closest("li") as HTMLElement);
    await user.click(croissant.getByRole("button", { name: "Eliminar" }));
    await user.click(croissant.getByRole("button", { name: "Sí, eliminar" }));
    await saveInPanel(user);

    const catalog = storedDocument(await apiConfig("catalogo_real")).offer.catalog;
    expect(catalog?.categories.map((category) => category.id)).toContain("bebidas_frias");
    expect(catalog?.items.find((item) => item.name === "Jugo de naranja")).toMatchObject({ category: "bebidas_frias", description: "Recién exprimido.", prices: [{ currency: "COP", amount: 7000 }] });
    expect(catalog?.items.find((item) => item.id === "sample_cafe_americano")?.prices).toEqual([{ currency: "COP", amount: 6500 }]);
    expect(catalog?.items.some((item) => item.name === "Croissant de mantequilla")).toBe(false);

    await openTab(user, /^Pagos y cierre/);
    await user.click(screen.getByRole("button", { name: "Agregar promoción" }));
    const promotion = within(screen.getByRole("group", { name: "Promoción 2" }));
    fill(promotion.getByLabelText(/^Nombre/), "Dos por uno");
    fill(promotion.getByLabelText(/^Qué incluye y a qué aplica/), "En jugos los martes");
    fill(promotion.getByLabelText(/^Vigente hasta/), "2030-12-31");
    const first = within(screen.getByRole("group", { name: "Promoción 1" }));
    fill(first.getByLabelText(/^Qué incluye y a qué aplica/), "15 % en desayunos los lunes");
    await saveInPanel(user);

    expect(storedDocument(await apiConfig("catalogo_real")).terms?.promotions).toEqual([
      { name: "Desayuno del lunes", details: "15 % en desayunos los lunes" },
      { name: "Dos por uno", details: "En jugos los martes", valid_until: "2030-12-31" },
    ]);
  });

  it("planes y servicios con varias monedas", async () => {
    await seedBusiness("planes_real");
    const user = await openPanel("/negocios/planes_real/productos");
    const list = within(screen.getByRole("list", { name: "Productos y servicios" }));
    await user.click(list.getByRole("button", { name: "Editar Básico" }));
    const edit = within(screen.getByRole("form", { name: /^Editar: Básico/ }));
    fill(edit.getByLabelText(/^Precio mensual/), "65000");
    await user.click(edit.getByRole("button", { name: "Agregar precio en otra moneda" }));
    fill(edit.getAllByLabelText(/^Precio anual/)[1]!, "199");
    fill(edit.getByLabelText("Qué incluye"), "Soporte por correo");
    fireEvent.keyDown(edit.getByLabelText("Qué incluye"), { key: "Enter" });
    await user.click(edit.getByRole("button", { name: "Aplicar cambios" }));
    await saveInPanel(user);

    const plan = storedDocument(await apiConfig("planes_real")).offer.plans?.[0];
    expect(plan?.prices).toEqual([{ currency: "COP", monthly: 65000 }, { currency: "USD", annual: 199 }]);
    expect(plan?.includes).toEqual(["Soporte por chat", "Soporte por correo"]);
  });

  it("9 y 10. personalidad, instrucciones y preguntas frecuentes", async () => {
    await seedBusiness("atencion_real");
    const user = await openPanel("/negocios/atencion_real/atencion");
    fill(screen.getByLabelText(/^Tono de comunicación/), "cercano y claro");
    fill(screen.getByLabelText(/^Personalidad de la marca/), "experta pero sencilla");
    await user.selectOptions(screen.getByLabelText(/^Trato al cliente/), "formal");
    await user.selectOptions(screen.getByLabelText(/^¿Puede usar emojis\?/), "no");
    await user.click(screen.getByRole("radio", { name: /^Equilibradas/ }));
    fill(screen.getByLabelText("Cómo debe vender en este negocio"), "Pregunta primero cuántos empleados tiene.");
    fireEvent.keyDown(screen.getByLabelText("Cómo debe vender en este negocio"), { key: "Enter" });
    fill(screen.getByLabelText(/^Principal razón por la que te compran/), "ahorrar tiempo");

    await user.click(screen.getByRole("button", { name: "Agregar pregunta frecuente" }));
    const added = within(screen.getByRole("group", { name: "Pregunta 2" }));
    fill(added.getByLabelText(/^Pregunta/), "¿Hay periodo de prueba?");
    fill(added.getByLabelText(/^Respuesta/), "Sí, de 15 días.");
    fill(within(screen.getByRole("group", { name: "Pregunta 1" })).getByLabelText(/^Respuesta/), "No, sin permanencia.");
    await saveInPanel(user);

    const stored = storedDocument(await apiConfig("atencion_real"));
    expect(stored.response_style).toMatchObject({ tone: "cercano y claro", voice: "experta pero sencilla", formality: "formal", emojis: false, length: "medium" });
    expect(stored.sales?.instructions).toEqual(["Pregunta primero cuántos empleados tiene."]);
    expect(stored.sales?.buying_motivation?.primary).toBe("ahorrar tiempo");
    expect(stored.knowledge?.faqs).toEqual([
      { question: "¿Tiene permanencia?", answer: "No, sin permanencia." },
      { question: "¿Hay periodo de prueba?", answer: "Sí, de 15 días." },
    ]);

    // Eliminar una pregunta, con su confirmación.
    await user.click(screen.getByRole("button", { name: "Quitar pregunta 2" }));
    await user.click(screen.getByRole("button", { name: "Sí, quitar" }));
    await saveInPanel(user);
    expect(storedDocument(await apiConfig("atencion_real")).knowledge?.faqs).toEqual([{ question: "¿Tiene permanencia?", answer: "No, sin permanencia." }]);
  });

  it("11. políticas y condiciones", async () => {
    await seedBusiness("politicas_real");
    const user = await openPanel("/negocios/politicas_real/pagos");
    fill(screen.getByLabelText(/^Garantía/), "Un año en el software.");
    fill(screen.getByLabelText(/^Cambios y devoluciones/), "Primeros 15 días.");
    fill(screen.getByLabelText(/^Cancelaciones y reembolsos/), "Sin penalidad.");
    fill(screen.getByLabelText("Condiciones de compra"), "Pago anticipado.");
    fireEvent.keyDown(screen.getByLabelText("Condiciones de compra"), { key: "Enter" });
    fill(screen.getByLabelText(/^Aclaración sobre el precio/), "No incluye IVA.");
    await saveInPanel(user);

    const { terms } = storedDocument(await apiConfig("politicas_real"));
    expect(terms?.policies).toEqual({ warranty: "Un año en el software.", returns: "Primeros 15 días.", cancellation: "Sin penalidad." });
    expect(terms?.conditions).toEqual(["Pago anticipado."]);
    expect(terms?.price_note).toBe("No incluye IVA.");
  });

  it("identidad, mensajes, canales y campos generados desde el contrato", async () => {
    await seedBusiness("otros_real");
    const user = await openPanel("/negocios/otros_real/negocio");
    fill(screen.getByLabelText(/^Marca/), "Norte");
    await user.selectOptions(screen.getByLabelText(/^¿Dónde atiendes\?/), "fisico");
    fill(screen.getByLabelText(/^Dirección/), "Calle 1 #2-3");
    fill(screen.getByLabelText(/^Ciudad/), "Ciudad Ejemplo");
    await user.click(screen.getByRole("checkbox", { name: /^Virtual/ }));
    await openTab(user, /^Mensajes y canales/);
    await user.click(screen.getByRole("switch", { name: "Enviar mensaje de bienvenida" }));
    fill(screen.getByLabelText(/^Mensaje/), "Hola, gracias por escribirnos.");
    await user.click(screen.getByRole("checkbox", { name: /^Telegram/ }));
    await openTab(user, /^Productos y servicios/);
    // Domicilio es una tarjeta de opciones avanzadas: se configura desde su propio botón.
    const delivery = within(screen.getByRole("heading", { name: /^Domicilio/ }).closest("details") as HTMLElement);
    await user.click(delivery.getByRole("button", { name: "Configurar" }));
    await user.click(delivery.getByRole("switch", { name: /^Disponible/ }));
    await saveInPanel(user);

    const stored = storedDocument(await apiConfig("otros_real"));
    expect(stored.identity).toMatchObject({ brand_name: "Norte", location: { type: "fisico", address: "Calle 1 #2-3", city: "Ciudad Ejemplo" }, service_modes: ["virtual"] });
    expect(stored.messages.welcome).toEqual({ enabled: true, text: "Hola, gracias por escribirnos." });
    expect(stored.capabilities.service_channels).toEqual(["whatsapp", "telegram"]);
    expect(stored.fulfillment?.delivery?.available).toBe(true);

    // Lo editado desde el formulario generado vuelve a aparecer al abrir de nuevo el panel.
    await openPanel("/negocios/otros_real/productos");
    expect(within(screen.getByRole("heading", { name: /^Domicilio/ }).closest("details") as HTMLElement).getByRole("switch", { name: /^Disponible/ })).toBeChecked();
  });
});

describe("12 y 16. métodos de pago y datos sensibles", () => {
  const LINK = "https://pagos.example.com/valor-ficticio-unico-enlace";
  const MOBILE = "3112223344";
  const ACCOUNT = "987654321012";

  it("guarda los datos cifrados, nunca los devuelve completos y solo permite reemplazarlos", async () => {
    await seedBusiness("pagos_real");
    let user = await openPanel("/negocios/pagos_real/pagos");
    await user.click(screen.getByRole("button", { name: "Configurar medios de pago" }));
    await user.click(screen.getByRole("switch", { name: "Ofrecer pago por enlace" }));
    fill(screen.getByLabelText(/^Enlace de pago/), LINK);
    await user.click(screen.getByRole("switch", { name: "Aceptar transferencias" }));
    await user.click(screen.getByRole("button", { name: "Agregar cuenta" }));
    fill(screen.getByLabelText(/^Número de celular/), MOBILE);
    await user.click(screen.getByRole("button", { name: "Agregar cuenta" }));
    const bank = within(screen.getByRole("group", { name: "Cuenta 2" }));
    await user.selectOptions(bank.getByLabelText("Tipo"), "bank");
    fill(bank.getByLabelText(/^Banco/), "Banco Ejemplo");
    fill(bank.getByLabelText(/^Número de cuenta/), ACCOUNT);
    await saveInPanel(user);

    // En la interfaz ya no están, ni siquiera en un campo.
    expect(screen.getAllByText("Guardado de forma segura")).toHaveLength(3);
    for (const secret of [LINK, MOBILE, ACCOUNT]) expect(screen.queryByDisplayValue(secret)).not.toBeInTheDocument();
    expect(document.body.innerHTML).not.toContain(MOBILE);

    // Ninguna respuesta de la API los contiene.
    const version = (await apiConfig("pagos_real")).latest_version;
    for (const path of ["/businesses", "/businesses/pagos_real/config", "/businesses/pagos_real/versions", "/businesses/pagos_real/review", `/businesses/pagos_real/versions/${version}/restore`]) {
      const response = await fetch(`${server.apiUrl}${path}`, path.endsWith("restore") ? { method: "POST" } : undefined);
      const text = await response.text();
      expect(response.ok, path).toBe(true);
      for (const secret of [LINK, MOBILE, ACCOUNT]) expect(text, path).not.toContain(secret);
    }

    // En disco están cifrados: el archivo no los contiene, y sí contiene el resto del documento.
    expect(server.databaseSize()).toBeGreaterThan(0);
    expect(server.databaseContains("pagos_real")).toBe(true);
    for (const secret of [LINK, MOBILE, ACCOUNT]) expect(server.databaseContains(secret)).toBe(false);

    // Sí se pueden usar: el compilador los resuelve con la clave, y por eso la versión es publicable.
    const review = await api<{ compiles: boolean; compile_error: string | null }>("/businesses/pagos_real/review");
    expect(review).toMatchObject({ compiles: true, compile_error: null });

    // Sobreviven al reinicio y se pueden reemplazar sin ver el anterior.
    await server.restart();
    user = await openPanel("/negocios/pagos_real/pagos");
    expect(screen.getAllByText("Guardado de forma segura")).toHaveLength(3);
    const before = storedDocument(await apiConfig("pagos_real")).payments?.[0]?.link?.secret_ref;
    await user.click(screen.getByRole("button", { name: "Reemplazar Enlace de pago" }));
    expect(screen.getByLabelText(/^Enlace de pago/)).toHaveValue("");
    fill(screen.getByLabelText(/^Enlace de pago/), `${LINK}-nuevo`);
    await saveInPanel(user);
    const after = storedDocument(await apiConfig("pagos_real")).payments?.[0]?.link?.secret_ref;
    expect(after).not.toBe(before);
    expect(server.databaseContains(`${LINK}-nuevo`)).toBe(false);
    expect((await api<{ compiles: boolean }>("/businesses/pagos_real/review")).compiles).toBe(true);
  });

  it("los métodos se reconocen, se editan, se reemplazan, se desactivan y se eliminan, y todo sobrevive al reinicio", async () => {
    const METHOD_LINK = "https://pagos.example.com/metodo-ficticio";
    const METHOD_MOBILE = "3117654321";
    const METHOD_ACCOUNT = "112233445566";
    const NEW_MOBILE = "3129990001";
    const secrets = [METHOD_LINK, METHOD_MOBILE, METHOD_ACCOUNT, NEW_MOBILE];
    const overview = () => within(screen.getByRole("list", { name: "Métodos de pago configurados" }));
    const account = (number: number) => within(screen.getByRole("group", { name: `Cuenta ${number}` }));
    const noSecretsVisible = () => {
      for (const secret of secrets) expect(document.body.innerHTML).not.toContain(secret);
    };

    // Agregar.
    await seedBusiness("metodos_real");
    let user = await openPanel("/negocios/metodos_real/pagos");
    await user.click(screen.getByRole("button", { name: "Configurar medios de pago" }));
    await user.click(screen.getByRole("switch", { name: "Ofrecer pago por enlace" }));
    fill(screen.getByLabelText(/^Enlace de pago/), METHOD_LINK);
    await user.click(screen.getByRole("switch", { name: "Aceptar transferencias" }));
    await user.click(screen.getByRole("button", { name: "Agregar cuenta" }));
    fill(screen.getByLabelText(/^Número de celular/), METHOD_MOBILE);
    await user.click(screen.getByRole("button", { name: "Agregar cuenta" }));
    await user.selectOptions(account(2).getByLabelText("Tipo"), "bank");
    fill(account(2).getByLabelText(/^Banco/), "Banco Ejemplo");
    fill(account(2).getByLabelText(/^Número de cuenta/), METHOD_ACCOUNT);
    await saveInPanel(user);

    // Consultar: se reconocen por el método y la parte visible, nunca por el valor completo.
    expect(overview().getByText("Enlace de pago")).toBeInTheDocument();
    expect(overview().getByText("https://pagos.example.com/••••")).toBeInTheDocument();
    expect(overview().getByText("Nequi")).toBeInTheDocument();
    expect(overview().getByText("••••4321")).toBeInTheDocument();
    expect(overview().getByText("Banco Ejemplo")).toBeInTheDocument();
    expect(overview().getByText("Cuenta ahorros")).toBeInTheDocument();
    expect(overview().getByText("••••5566")).toBeInTheDocument();
    expect(overview().getAllByText("Activo")).toHaveLength(3);
    noSecretsVisible();

    // Reiniciar: lo mismo, y el reemplazo no muestra el valor anterior.
    const saved = await apiConfig("metodos_real");
    await server.restart();
    user = await openPanel("/negocios/metodos_real/pagos");
    expect(overview().getByText("••••4321")).toBeInTheDocument();
    expect(screen.getAllByText("Guardado de forma segura")).toHaveLength(3);
    expect(await apiConfig("metodos_real")).toEqual(saved);

    // Editar sin reemplazar: el dato cifrado no cambia.
    fill(account(2).getByLabelText(/^Banco/), "Banco Otro");
    fill(account(2).getByLabelText(/^Titular o etiqueta/), "Cuenta de la tienda");
    await saveInPanel(user);
    const edited = await apiConfig("metodos_real");
    expect(storedDocument(edited).payments?.[0]?.transfer_methods?.[1]).toMatchObject({ bank: "Banco Otro", label: "Cuenta de la tienda" });
    expect(storedDocument(edited).payments?.[0]?.transfer_methods?.[1]?.account_number).toEqual(storedDocument(saved).payments?.[0]?.transfer_methods?.[1]?.account_number);
    expect(overview().getByText("••••5566")).toBeInTheDocument();

    // Un reemplazo vacío conserva el dato.
    await user.click(screen.getByRole("button", { name: "Reemplazar Número de celular" }));
    fill(account(2).getByLabelText(/^Titular o etiqueta/), "Cuenta principal");
    await saveInPanel(user);
    expect(overview().getByText("••••4321")).toBeInTheDocument();

    // Reemplazar de verdad.
    await user.click(screen.getByRole("button", { name: "Reemplazar Número de celular" }));
    fill(screen.getByLabelText(/^Número de celular/), NEW_MOBILE);
    await saveInPanel(user);
    expect(overview().getByText("••••0001")).toBeInTheDocument();
    expect(overview().queryByText("••••4321")).not.toBeInTheDocument();
    noSecretsVisible();

    // Desactivar y activar: el dato se conserva, y lo inactivo deja de ofrecerse sin impedir publicar.
    await user.click(account(1).getByRole("switch", { name: /^Cuenta activa/ }));
    await user.click(screen.getByRole("switch", { name: "Ofrecer pago por enlace" }));
    await saveInPanel(user);
    expect(overview().getAllByText("Inactivo")).toHaveLength(2);
    expect(overview().getByText("••••0001")).toBeInTheDocument();
    expect(await api<{ compiles: boolean }>("/businesses/metodos_real/review")).toMatchObject({ compiles: true });
    await user.click(account(1).getByRole("switch", { name: /^Cuenta activa/ }));
    await user.click(screen.getByRole("switch", { name: /^Ofrecer pago por enlace/ }));
    await saveInPanel(user);
    expect(overview().getAllByText("Activo")).toHaveLength(3);

    // Eliminar.
    await user.click(account(2).getByRole("button", { name: "Quitar" }));
    await user.click(account(2).getByRole("button", { name: "Sí, quitar" }));
    await saveInPanel(user);
    expect(overview().queryByText("Banco Otro")).not.toBeInTheDocument();
    const afterRemoval = await apiConfig("metodos_real");
    expect(storedDocument(afterRemoval).payments?.[0]?.transfer_methods).toHaveLength(1);

    // Otro negocio no ve nada de esto, y el archivo de la base no contiene ningún valor.
    await seedBusiness("metodos_otro");
    await openPanel("/negocios/metodos_otro/pagos");
    expect(screen.queryByRole("list", { name: "Métodos de pago configurados" })).not.toBeInTheDocument();
    expect(screen.getByText("Todavía no hay medios de pago")).toBeInTheDocument();
    for (const secret of secrets) expect(server.databaseContains(secret)).toBe(false);

    // Recuperar la primera versión con pagos trae también sus datos.
    const restored = await api<ApiConfig & { payment_fields: Record<string, { masked: string | null }> }>(`/businesses/metodos_real/versions/${saved.latest_version}/restore`, { method: "POST" });
    expect(Object.values(restored.payment_fields).map((field) => field.masked).sort()).toEqual(["https://pagos.example.com/••••", "••••4321", "••••5566"].sort());
    for (const secret of secrets) expect(server.output()).not.toContain(secret);
  });

  it("no registra los datos de pago en la salida del servidor", () => {
    for (const secret of [LINK, MOBILE, ACCOUNT, SAMPLE_LINK, SAMPLE_MOBILE]) expect(server.output()).not.toContain(secret);
  });

  it("rechaza un valor de pago dentro del documento y no lo repite en el error", async () => {
    const config = await seedBusiness("pagos_filtrados");
    const document = { ...storedDocument(config), messages: { ...storedDocument(config).messages, after_sale: "ok" }, payments: [{ id: "principal", link: "https://pagos.example.com/valor-en-claro", transfer_enabled: false, transfer_methods: [] }] };
    const response = await fetch(`${server.apiUrl}/businesses/pagos_filtrados/config`, jsonInit("PUT", { document, payment_values: {}, base_version: config.latest_version }));
    expect(response.status).toBe(422);
    expect(await response.text()).not.toContain("valor-en-claro");
    expect(server.databaseContains("valor-en-claro")).toBe(false);
  });
});

describe("13 y 14. validaciones y errores", () => {
  const services = () => createLocalServices(server.apiUrl);

  it("el servidor valida todo documento con el contrato y señala cada campo por su ruta", async () => {
    const { latest_version: baseVersion } = await seedBusiness("validacion_real");
    const repository = services().createConfigRepository("validacion_real");
    const valid = (): BusinessDocument => ({ ...structuredClone(SAMPLE_PLANS_DOCUMENT), tenant_slug: "validacion_real" });

    // Cada caso rompe el documento a propósito: los tipos del panel no lo permitirían.
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const cases: [title: string, change: (document: any) => void, path: string][] = [
      ["campo obligatorio", (document) => delete document.identity.name, "identity.name"],
      ["tipo incorrecto", (document) => (document.offer.plans[0].prices[0].monthly = "caro"), "offer.plans.0.prices.0.monthly"],
      ["valor no permitido", (document) => (document.response_style.length = "gigante"), "response_style.length"],
      ["estructura inválida: campo inventado", (document) => (document.identity.campo_inventado = 1), "identity.campo_inventado"],
      ["relación inconsistente: perfil de pago inexistente", (document) => (document.offer.plans[0].payment_profile = "no_existe"), "(documento)"],
      ["otro negocio", (document) => (document.tenant_slug = "otro_negocio"), "tenant_slug"],
    ];
    for (const [title, change, path] of cases) {
      const document = valid();
      change(document);
      const error = await repository.save({ document, paymentValues: {}, baseVersion }).then(
        () => null,
        (failure: unknown) => failure,
      );
      expect(error, title).toBeInstanceOf(PersistenceError);
      expect((error as PersistenceError).code, title).toBe("invalid");
      if (path === "(documento)") expect((error as PersistenceError).problems.map((problem) => problem.message).join(" "), title).toContain("no_existe");
      else expect((error as PersistenceError).problems.map((problem) => problem.path), title).toContain(path);
    }
    expect((await apiConfig("validacion_real")).latest_version).toBe(baseVersion);
  });

  it("muestra en su campo un error que solo el servidor conoce", async () => {
    await seedBusiness("limite_real");
    const user = await openPanel("/negocios/limite_real/mensajes");
    const field = screen.getByLabelText(/^Después de una compra/);
    fill(field, "x".repeat(801));
    await user.click(screen.getByRole("button", { name: "Guardar cambios" }));
    await screen.findByText("La configuración tiene datos por corregir.");
    expect(screen.getByLabelText(/^Después de una compra/)).toHaveAttribute("aria-invalid", "true");
    expect((await apiConfig("limite_real")).latest_version).toBe(1);
    expect(document.body.innerHTML).toContain("x".repeat(801));

    fill(screen.getByLabelText(/^Después de una compra/), "Gracias por tu compra.");
    await saveInPanel(user);
    expect(storedDocument(await apiConfig("limite_real")).messages.after_sale).toBe("Gracias por tu compra.");
  });

  it("evita identificadores duplicados e inválidos", async () => {
    await seedBusiness("repetido_real");
    const directory = services().directory;
    await expect(directory.create({ slug: "repetido_real", name: "Otro" })).rejects.toMatchObject({ code: "duplicate" });
    await expect(directory.create({ slug: "../fuera", name: "Otro" })).rejects.toMatchObject({ code: "invalid" });
    await expect(directory.create({ slug: "Con Mayusculas", name: "Otro" })).rejects.toMatchObject({ code: "invalid" });
    await expect(directory.create({ slug: "sin_nombre", name: "   " })).rejects.toMatchObject({ code: "invalid" });
    expect(storedDocument(await apiConfig("repetido_real")).identity.name).toBe("Software Norte");

    const user = await openPanel("/negocios");
    await user.click(screen.getAllByRole("button", { name: "Crear negocio" })[0]!);
    const form = within(screen.getByRole("form", { name: "Crear negocio" }));
    fill(form.getByLabelText(/^Nombre comercial/), "Otro más");
    fill(form.getByLabelText(/^Identificador/), "Con Espacios");
    await user.click(form.getByRole("button", { name: "Crear negocio" }));
    expect(await form.findByText(/Usa solo minúsculas, números y guion bajo/)).toBeInTheDocument();
    expect(window.location.pathname).toBe("/negocios");
  });

  it("si el servidor se cae lo informa, conserva lo escrito y guarda al volver", async () => {
    await seedBusiness("caida_real");
    const user = await openPanel("/negocios/caida_real/negocio");
    fill(screen.getByLabelText(/^Nombre comercial/), "Escrito durante la caída");
    await server.halt();
    try {
      await user.click(screen.getByRole("button", { name: "Guardar cambios" }));
      await screen.findByText("No se pudo guardar");
      expect(screen.getAllByText(/No se pudo conectar con el servidor local/).length).toBeGreaterThan(0);
      expect(screen.queryByText(/^Guardado ·/)).not.toBeInTheDocument();
      expect(screen.getByLabelText(/^Nombre comercial/)).toHaveValue("Escrito durante la caída");
    } finally {
      await server.start();
    }
    await user.click(screen.getByRole("button", { name: "Reintentar" }));
    await screen.findByText(/^Guardado ·/);
    expect(storedDocument(await apiConfig("caida_real")).identity.name).toBe("Escrito durante la caída");
  });

  it("detecta que el negocio cambió en otra pestaña y no pisa esos cambios", async () => {
    const seeded = await seedBusiness("pestanas_real");
    const user = await openPanel("/negocios/pestanas_real/negocio");
    const other = { ...storedDocument(seeded), identity: { ...storedDocument(seeded).identity, name: "Desde otra pestaña" } };
    await api("/businesses/pestanas_real/config", jsonInit("PUT", { document: other, payment_values: {}, base_version: seeded.latest_version }));

    fill(screen.getByLabelText(/^Nombre comercial/), "Desde esta pestaña");
    await user.click(screen.getByRole("button", { name: "Guardar cambios" }));
    await screen.findByText(/cambió desde que lo abriste/);
    expect(storedDocument(await apiConfig("pestanas_real")).identity.name).toBe("Desde otra pestaña");
  });

  it("un negocio que no existe se informa, sin crear nada", async () => {
    await openPanel("/negocios/no_existe_real");
    expect(screen.getByRole("heading", { level: 1, name: "Ese negocio no existe" })).toBeInTheDocument();
    const response = await fetch(`${server.apiUrl}/businesses/no_existe_real/config`);
    expect(response.status).toBe(404);
  });

  it("eliminar exige confirmación con el identificador, también en la API", async () => {
    await seedBusiness("borrar_real", { ...SAMPLE_PLANS_DOCUMENT, identity: { ...SAMPLE_PLANS_DOCUMENT.identity, name: "Negocio para borrar" } });
    const response = await fetch(`${server.apiUrl}/businesses/borrar_real`, { method: "DELETE" });
    expect(response.status).toBe(400);
    expect((await apiConfig("borrar_real")).latest_version).toBe(1);

    const user = await openPanel("/negocios");
    await user.click(screen.getByRole("button", { name: "Eliminar Negocio para borrar" }));
    fill(screen.getByLabelText("Para confirmar, escribe borrar_real"), "borrar_real");
    await user.click(screen.getByRole("button", { name: "Eliminar definitivamente" }));
    await screen.findByText('Se eliminó "Negocio para borrar".');
    expect((await fetch(`${server.apiUrl}/businesses/borrar_real/config`)).status).toBe(404);
  });
});

describe("15. aislamiento entre negocios", () => {
  it("una operación sobre un negocio no modifica a otro", async () => {
    await seedCatalogBusiness("aislado_a");
    const seededB = await seedBusiness("aislado_b");
    const user = await openPanel("/negocios/aislado_a/negocio");
    fill(screen.getByLabelText(/^Nombre comercial/), "Solo A cambia");
    await saveInPanel(user);

    const after = await apiConfig("aislado_b");
    expect(after.document).toEqual(seededB.document);
    expect(after.latest_version).toBe(seededB.latest_version);

    // El panel de A no puede guardar un documento de B, y cada ruta sirve su propio documento.
    const documentA = storedDocument(await apiConfig("aislado_a"));
    const crossed = await fetch(`${server.apiUrl}/businesses/aislado_b/config`, jsonInit("PUT", { document: documentA, payment_values: {}, base_version: seededB.latest_version }));
    expect(crossed.status).toBe(422);
    expect((await apiConfig("aislado_b")).latest_version).toBe(seededB.latest_version);
    expect((await apiConfig("aislado_a")).document?.tenant_slug).toBe("aislado_a");

    // B no alcanza los datos de pago de A aunque copie su referencia: no se resuelve y la versión no se puede publicar.
    const borrowed = { ...storedDocument(seededB), payments: documentA.payments };
    const withStolenRefs = { ...borrowed, offer: { ...borrowed.offer, plans: borrowed.offer.plans?.map((plan) => ({ ...plan, payment_profile: "principal" })) } };
    const saved = await api<ApiConfig>("/businesses/aislado_b/config", jsonInit("PUT", { document: withStolenRefs, payment_values: {}, base_version: seededB.latest_version }));
    expect(await api<{ compiles: boolean }>("/businesses/aislado_b/review")).toMatchObject({ compiles: false });
    const stolen = await fetch(`${server.apiUrl}/businesses/aislado_b/publish`, jsonInit("POST", { version: saved.latest_version }));
    expect(stolen.status).toBe(409);
    expect((await apiConfig("aislado_b")).published_version).toBeNull();

    // Publicar y borrar uno tampoco afecta al otro.
    const versionA = (await apiConfig("aislado_a")).latest_version;
    await api("/businesses/aislado_a/publish", jsonInit("POST", { version: versionA }));
    expect((await apiConfig("aislado_b")).published_version).toBeNull();
    await api("/businesses/aislado_a?confirm=aislado_a", { method: "DELETE" });
    expect((await apiConfig("aislado_b")).slug).toBe("aislado_b");
    expect((await fetch(`${server.apiUrl}/businesses/aislado_a/config`)).status).toBe(404);
  });

  it("rechaza rutas que intentan salir del negocio", async () => {
    for (const slug of ["..%2Fotro", "%2e%2e", "a%2Fb", "Mayus", "con%20espacio"]) {
      const response = await fetch(`${server.apiUrl}/businesses/${slug}/config`);
      expect(response.status, slug).toBeGreaterThanOrEqual(404);
      expect(response.ok, slug).toBe(false);
    }
  });
});

describe("17 y 18. persistencia real y contrato", () => {
  it("lo guardado no depende del navegador: se recupera con el almacenamiento vacío", async () => {
    await seedBusiness("navegador_real");
    const user = await openPanel("/negocios/navegador_real/negocio");
    fill(screen.getByLabelText(/^Nombre comercial/), "Guardado en el servidor");
    await saveInPanel(user);

    expect(window.localStorage.length).toBe(0);
    expect(window.sessionStorage.length).toBe(0);
    expect(setItem).not.toHaveBeenCalled();

    window.localStorage.clear();
    window.sessionStorage.clear();
    await openPanel("/negocios/navegador_real/negocio");
    expect(screen.getByLabelText(/^Nombre comercial/)).toHaveValue("Guardado en el servidor");
  });

  it("el panel usa de verdad BusinessConfig v1", async () => {
    // El esquema que usan los formularios es el del contrato publicado, no una copia.
    expect(await api("/contract")).toEqual(publishedSchema);
    expect(SCHEMA_VERSION).toBe(publishedSchema.properties.schema_version.const);

    await seedBusiness("contrato_real");
    const user = await openPanel("/negocios/contrato_real/revision");
    expect(storedDocument(await apiConfig("contrato_real")).schema_version).toBe(SCHEMA_VERSION);

    // El panel publica con el compilador del contrato y lo dice con honestidad.
    expect(screen.getByText("Esto es lo que responde el asistente")).toBeInTheDocument();
    await publishInPanel(user, 1);
    const published = await apiConfig("contrato_real");
    expect(published.published_version).toBe(1);
    expect(published.draft_version).toBeNull();

    // Editar después de publicar crea otra versión y lo publicado no cambia hasta volver a publicar.
    await openTab(user, /^Mi negocio/);
    fill(screen.getByLabelText(/^Nombre comercial/), "Software Norte Dos");
    await saveInPanel(user);
    const edited = await apiConfig("contrato_real");
    expect(edited).toMatchObject({ latest_version: 2, draft_version: 2, published_version: 1 });
    const firstVersion = (await api<{ version: number; status: string }[]>("/businesses/contrato_real/versions")).find((version) => version.version === 1);
    expect(firstVersion?.status).toBe("published");

    // El reinicio conserva también versiones y publicación.
    await server.restart();
    expect(await apiConfig("contrato_real")).toMatchObject({ latest_version: 2, published_version: 1 });

    // Publicar otra vez, volver a la anterior y restaurar, desde el panel y con lo que devuelve el servidor real.
    const again = await openPanel("/negocios/contrato_real/revision");
    await publishInPanel(again, 2);
    expect(await apiConfig("contrato_real")).toMatchObject({ published_version: 2, draft_version: null });

    await again.click(await screen.findByRole("button", { name: "Volver a la versión publicada anterior" }));
    await again.click(screen.getByRole("button", { name: "Sí, volver" }));
    await screen.findByText("Se volvió a publicar la versión anterior.");
    expect(await apiConfig("contrato_real")).toMatchObject({ published_version: 1, latest_version: 2 });

    const history = await screen.findByRole("list", { name: "Historial de versiones" });
    await waitFor(() => expect(within(history).getAllByRole("listitem")).toHaveLength(2));
    const second = (await within(history).findByText(/^Versión 2/)).closest("li") as HTMLElement;
    await again.click(within(second).getByRole("button", { name: "Restaurar" }));
    await again.click(within(second).getByRole("button", { name: "Sí, restaurar" }));
    await screen.findByText("Se creó un borrador con el contenido de la versión 2.");
    const restored = await apiConfig("contrato_real");
    expect(restored).toMatchObject({ latest_version: 3, draft_version: 3, published_version: 1 });
    expect(storedDocument(restored).identity.name).toBe("Software Norte Dos");
    await publishInPanel(again, 3);
    expect(await apiConfig("contrato_real")).toMatchObject({ published_version: 3, draft_version: null });
  });

  it("si falta un dato de pago lo explica sin mostrar referencias internas y no deja publicar", async () => {
    const seeded = await seedBusiness("sin_dato_real");
    const base = storedDocument(seeded);
    const document = {
      ...base,
      // El compilador solo resuelve lo que la oferta usa: los planes tienen que cobrarse con este perfil.
      offer: { ...base.offer, plans: base.offer.plans?.map((plan) => ({ ...plan, payment_profile: "principal" })) },
      payments: [{ id: "principal", link: { secret_ref: "secret_store:principal.link~inexistente" }, transfer_enabled: false, transfer_methods: [] }],
    };
    await api("/businesses/sin_dato_real/config", jsonInit("PUT", { document, payment_values: {}, base_version: seeded.latest_version }));

    await openPanel("/negocios/sin_dato_real/revision");
    await screen.findByText("Esta versión todavía no se puede publicar");
    expect(screen.getByText(/Falta un dato de pago o no se puede leer con la clave actual/)).toBeInTheDocument();
    expect(document_text()).not.toContain("inexistente");
    expect(document_text()).not.toContain("secret_store");
    expect(screen.getByRole("button", { name: "Publicar versión 2" })).toBeDisabled();
  });

  it("importa los negocios existentes y el panel los abre y guarda sin perder nada", async () => {
    const NINE = ["agencia_viajes", "asesor_ai_prod", "clinic", "demo", "ecommerce", "escuela_conduccion", "restaurant", "saas", "tienda_ropa"];
    const user = await openPanel("/negocios");
    await user.click(screen.getByRole("button", { name: "Importar negocios existentes" }));
    await screen.findByText("Se importaron 9 negocios.");
    const slugs = (await api<{ slug: string }[]>("/businesses")).map((business) => business.slug);
    expect(slugs).toEqual(expect.arrayContaining(NINE));

    // Volver a importar no toca nada.
    expect(await api<{ created: string[] }>("/businesses/import", { method: "POST" })).toMatchObject({ created: [] });

    const failures = vi.spyOn(console, "error");
    for (const slug of NINE) {
      const before = await apiConfig(slug);
      const compilesBefore = (await api<{ compiles: boolean }>(`/businesses/${slug}/review`)).compiles;
      const panel = await openPanel(`/negocios/${slug}`);
      for (const link of [/^Productos y servicios/, /^Pagos y cierre/, /^Cómo atiende/, /^Mensajes y canales/, /^Publicar/, /^Mi negocio/]) {
        await openTab(panel, link);
        expect(screen.queryByText("Esta sección no se pudo mostrar"), `${slug} ${link}`).not.toBeInTheDocument();
      }
      // Abrirlo y recorrerlo no lo marca como modificado ni crea versiones.
      expect(screen.queryByText("Cambios sin guardar"), slug).not.toBeInTheDocument();
      expect((await apiConfig(slug)).latest_version, slug).toBe(before.latest_version);

      // Guardar desde el panel conserva todo lo demás, incluidos los campos sin pantalla y las referencias de pago.
      const name = storedDocument(before).identity.name;
      fill(screen.getByLabelText(/^Nombre comercial/), `${name} editado`);
      await saveInPanel(panel);
      const after = storedDocument(await apiConfig(slug));
      expect(after.identity.name, slug).toBe(`${name} editado`);
      expect({ ...after, identity: { ...after.identity, name } }, slug).toEqual(storedDocument(before));
      expect((await api<{ compiles: boolean }>(`/businesses/${slug}/review`)).compiles, slug).toBe(compilesBefore);
    }
    expect(failures).not.toHaveBeenCalled();
    failures.mockRestore();
  });
});
