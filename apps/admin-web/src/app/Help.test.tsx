import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it } from "vitest";
import { anchorOf, articlesForScreen, helpForPath, helpLink, REFERENCED_ARTICLES, startSteps, type HelpModule } from "../domain/help/help";
import * as nav from "../navigation/navItems";
import { createMemoryBackend, createMemoryHelp, createMemoryQuickReplies, createTestServices, quickReply } from "../test/fakes";
import { SAMPLE_DOCUMENT } from "../test/fixtures/sampleDocument";
import { App } from "./App";

afterEach(cleanup);

const CAFE = SAMPLE_DOCUMENT.tenant_slug;

/** Los artículos reales (`project/content/help`), para revisar que lo que el panel nombra existe. */
const ARTICLES = import.meta.glob<string>("../../../../project/content/help/*/*.md", { query: "?raw", import: "default", eager: true });
const SLUGS = new Set(Object.keys(ARTICLES).map((path) => path.split("/").pop()!.replace(/\.md$/, "")));

/** Las pantallas que existen dentro de un negocio: las de la navegación. */
const isItem = (value: unknown): value is nav.NavItem => typeof value === "object" && value !== null && "path" in value && "key" in value;
const SCREENS = new Set(
  [
    ...Object.values(nav).filter(isItem),
    ...nav.SECTION_ITEMS,
    ...nav.ASSISTANT_TABS.map((tab) => tab.item),
    ...[...nav.SETTINGS_GROUPS, ...nav.ACCOUNT_GROUPS].flatMap((group) => group.entries.map((entry) => entry.item)),
  ].map((item) => item.path),
);

describe("Lo que el panel sabe de la ayuda", () => {
  it("cada pantalla tiene su ayuda, con el artículo que la explica primero", () => {
    expect(helpForPath(`/negocios/${CAFE}/canales`)).toEqual({ module: "canales", article: "conectar-whatsapp" });
    expect(helpForPath(`/negocios/${CAFE}/configuracion/respuestas-rapidas`)).toEqual({ module: "respuestas-rapidas", article: "crear-respuestas-rapidas" });
    expect(helpForPath(`/negocios/${CAFE}/configuracion/facturacion`).module).toBe("cuenta");
    expect(helpForPath(`/negocios/${CAFE}/integraciones/claves/`)).toEqual({ module: "integraciones", article: "claves-de-api" });
    expect(helpForPath(`/negocios/${CAFE}`)).toEqual({ module: "primeros-pasos", article: "empieza-aqui" });
    // «atencion» (Cómo atiende) no es «atencion-humana».
    expect(helpForPath(`/negocios/${CAFE}/atencion`).module).toBe("asistente");
  });

  it("ordena los artículos de un tema con el de la pantalla primero", () => {
    const module: HelpModule = {
      id: "canales",
      name: "Canales",
      description: "",
      articles: ["conectar-whatsapp", "cuidar-tu-numero", "desconectar-whatsapp"].map((slug) => ({ slug, module: "canales", title: slug, summary: "", minutes: 1, updated: "2026-11-12" })),
    };
    expect(articlesForScreen(module, { module: "canales", article: "desconectar-whatsapp" }).map((item) => item.slug)).toEqual(["desconectar-whatsapp", "conectar-whatsapp", "cuidar-tu-numero"]);
    expect(articlesForScreen(undefined, { module: "canales" })).toEqual([]);
  });

  it("sabe a dónde lleva cada enlace y nunca abre algo que no reconoce", () => {
    expect(helpLink("conectar-whatsapp")).toEqual({ kind: "article", slug: "conectar-whatsapp" });
    expect(helpLink("panel:configuracion/inteligencia-artificial")).toEqual({ kind: "screen", path: "configuracion/inteligencia-artificial" });
    expect(helpLink("https://openrouter.ai")).toEqual({ kind: "external", href: "https://openrouter.ai" });
    expect(helpLink("javascript:alert(1)")).toEqual({ kind: "text" });
    expect(helpLink("http://inseguro.com")).toEqual({ kind: "text" });
  });

  it("calcula las anclas como el servidor", () => {
    expect(anchorOf("¿Con qué versión responde?")).toBe("con-que-version-responde");
  });

  it("«Empieza aquí» no marca lo que todavía no sabe", () => {
    const steps = startSteps({ sectionsReady: true, aiKey: null, published: false, whatsapp: true, quickReplies: false });
    expect(steps.map((step) => [step.id, step.done])).toEqual([
      ["sections", true],
      ["ai", null],
      ["publish", false],
      ["whatsapp", true],
      ["quickReplies", false],
    ]);
  });
});

describe("Los artículos reales y el panel", () => {
  it("existen los artículos que nombra el panel", () => {
    expect(SLUGS.size).toBeGreaterThan(30);
    expect(REFERENCED_ARTICLES.filter((slug) => !SLUGS.has(slug))).toEqual([]);
    expect(startSteps({ sectionsReady: false, aiKey: false, published: false, whatsapp: false, quickReplies: false }).filter((step) => !SLUGS.has(step.article))).toEqual([]);
  });

  it("cada enlace a una pantalla («panel:ruta») lleva a una pantalla que existe", () => {
    const broken = Object.entries(ARTICLES).flatMap(([path, source]) =>
      [...source.matchAll(/\]\(panel:([^)]*)\)/g)].map((match) => match[1]!).filter((screen) => !SCREENS.has(screen)).map((screen) => `${path}: panel:${screen}`),
    );
    expect(SCREENS.has("canales") && SCREENS.has("configuracion/respuestas-rapidas")).toBe(true);
    expect(broken).toEqual([]);
  });

  it("las pantallas de «Empieza aquí» existen", () => {
    const steps = startSteps({ sectionsReady: false, aiKey: false, published: false, whatsapp: false, quickReplies: false });
    expect(steps.filter((step) => !SCREENS.has(step.path))).toEqual([]);
  });
});

async function openAt(path: string, overrides: Parameters<typeof createTestServices>[1] = {}) {
  window.history.pushState({}, "", path);
  const user = userEvent.setup();
  const help = createMemoryHelp();
  render(<App services={createTestServices(createMemoryBackend([SAMPLE_DOCUMENT]), { help, ...overrides })} />);
  return { user, help };
}

describe("Centro de ayuda", () => {
  it("está en el menú, con el buscador, «Empieza aquí» y los temas", async () => {
    const quick = createMemoryQuickReplies([quickReply("precios", ["Vale $25.000."])]);
    await openAt(`/negocios/${CAFE}/ayuda`, { createQuickReplies: () => quick });
    expect(await screen.findByRole("heading", { level: 1, name: "¿En qué te ayudamos?" })).toBeInTheDocument();
    const menu = screen.getByRole("navigation", { name: "Menú del negocio" });
    expect(within(menu).getByRole("link", { name: "Ayuda" })).toHaveAttribute("aria-current", "page");
    // En el Centro de ayuda, el botón de la ayuda de la pantalla sobra.
    expect(screen.queryByRole("button", { name: "Ayuda de esta pantalla" })).not.toBeInTheDocument();

    const start = screen.getByRole("region", { name: "Empieza aquí" });
    // Sin clave de IA ni WhatsApp conectado; con una respuesta rápida guardada.
    const quickStep = await within(start).findByRole("link", { name: "Guarda tus respuestas rápidas" });
    await waitFor(() => expect(quickStep.closest("li")).toHaveClass("help-step--done"));
    expect(within(start).getByRole("link", { name: "Pon tu clave de IA" }).closest("li")).not.toHaveClass("help-step--done");
    expect(within(start).getAllByRole("link", { name: "Cómo se hace" })[1]).toHaveAttribute("href", `/negocios/${CAFE}/ayuda/clave-de-openrouter`);

    const topics = screen.getByRole("region", { name: "Temas" });
    expect(within(topics).getByRole("link", { name: /Canales/ })).toHaveAttribute("href", `/negocios/${CAFE}/ayuda?tema=canales`);
  });

  it("muestra los artículos de un tema", async () => {
    const { user } = await openAt(`/negocios/${CAFE}/ayuda`);
    await user.click(await screen.findByRole("link", { name: /Canales.*Conectar tu WhatsApp/ }));
    expect(await screen.findByRole("heading", { level: 1, name: "Canales" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Conecta tu WhatsApp con el código QR/ })).toHaveAttribute("href", `/negocios/${CAFE}/ayuda/conectar-whatsapp`);
    expect(screen.getByRole("link", { name: /Cuida tu número/ })).toBeInTheDocument();
    expect(screen.queryByRole("region", { name: "Empieza aquí" })).not.toBeInTheDocument();
  });

  it("busca cuando dejas de escribir", async () => {
    const { user, help } = await openAt(`/negocios/${CAFE}/ayuda`);
    await user.type(await screen.findByRole("searchbox", { name: "Buscar en la ayuda" }), "whatsapp");
    const results = await screen.findByRole("region", { name: "Resultados de la búsqueda" });
    expect(await within(results).findByText("2 artículos para «whatsapp»")).toBeInTheDocument();
    expect(help.searches).toEqual(["whatsapp"]);

    await user.clear(screen.getByRole("searchbox", { name: "Buscar en la ayuda" }));
    await user.type(screen.getByRole("searchbox", { name: "Buscar en la ayuda" }), "zzz");
    expect(await screen.findByText(/No encontramos nada con «zzz»/)).toBeInTheDocument();
  });

  it("muestra un artículo con su texto, sus enlaces y lo relacionado", async () => {
    await openAt(`/negocios/${CAFE}/ayuda/conectar-whatsapp`);
    expect(await screen.findByRole("heading", { level: 1, name: "Conecta tu WhatsApp con el código QR" })).toBeInTheDocument();
    const crumbs = screen.getByRole("navigation", { name: "Ruta" });
    expect(within(crumbs).getByRole("link", { name: "Canales" })).toHaveAttribute("href", `/negocios/${CAFE}/ayuda?tema=canales`);

    const article = screen.getByRole("article");
    expect(within(article).getByRole("heading", { level: 2, name: "Si el código venció" })).toHaveAttribute("id", "si-el-codigo-vencio");
    expect(within(article).getByRole("link", { name: "Canales" })).toHaveAttribute("href", `/negocios/${CAFE}/canales`);
    expect(within(article).getByText("Conectar WhatsApp").tagName).toBe("STRONG");
    expect(within(article).getByText("Generar otro código").tagName).toBe("CODE");
    expect(within(article).getByRole("table")).toHaveTextContent("Dispositivos vinculados");

    expect(within(screen.getByRole("navigation", { name: "Anterior y siguiente" })).getByRole("link", { name: /Siguiente/ })).toHaveTextContent("Cuida tu número");
    const index = screen.getByRole("navigation", { name: "En este artículo" });
    expect(within(index).getByRole("link", { name: "Conectar" })).toHaveAttribute("href", "#conectar");
    expect(within(screen.getByRole("navigation", { name: "Relacionados" })).getByRole("link", { name: /Empieza aquí/ })).toHaveAttribute("href", `/negocios/${CAFE}/ayuda/empieza-aqui`);
    expect(within(screen.getByRole("navigation", { name: "Más de Canales" })).getByRole("link", { name: /Cuida tu número/ })).toBeInTheDocument();
  });

  it("abre los enlaces de afuera en otra pestaña y pinta los avisos", async () => {
    await openAt(`/negocios/${CAFE}/ayuda/clave-de-openrouter`);
    const external = await screen.findByRole("link", { name: "openrouter.ai" });
    expect(external).toHaveAttribute("target", "_blank");
    expect(external).toHaveAttribute("rel", "noreferrer");
    expect(screen.getByText("Importante").closest("aside")).toHaveClass("help-callout--warning");
  });

  it("dice qué hacer con un artículo que no existe", async () => {
    await openAt(`/negocios/${CAFE}/ayuda/no-existe`);
    expect(await screen.findByText("Este artículo no existe")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Búscalo en el Centro de ayuda" })).toHaveAttribute("href", `/negocios/${CAFE}/ayuda`);
  });

  it("si la ayuda no carga, deja reintentar", async () => {
    const help = createMemoryHelp();
    help.failIndex = true;
    const { user } = await openAt(`/negocios/${CAFE}/ayuda`, { help });
    expect(await screen.findByText("No se pudo cargar la ayuda.")).toBeInTheDocument();
    help.failIndex = false;
    await user.click(screen.getByRole("button", { name: "Reintentar" }));
    expect(await screen.findByRole("heading", { level: 1, name: "¿En qué te ayudamos?" })).toBeInTheDocument();
  });
});

describe("Ayuda de esta pantalla", () => {
  it("se abre junto a los avisos con los artículos de la pantalla, y se cierra al abrir uno", async () => {
    const { user } = await openAt(`/negocios/${CAFE}/canales`);
    await user.click(await screen.findByRole("button", { name: "Ayuda de esta pantalla" }));
    const panel = screen.getByRole("dialog", { name: "Ayuda de esta pantalla" });
    expect(await within(panel).findByText("Estás en Canales")).toBeInTheDocument();
    const links = within(panel).getAllByRole("link");
    expect(links[0]).toHaveTextContent("Conecta tu WhatsApp con el código QR");
    expect(within(panel).getByRole("link", { name: "Toda la ayuda de Canales" })).toHaveAttribute("href", `/negocios/${CAFE}/ayuda?tema=canales`);
    expect(within(panel).getByRole("searchbox", { name: "Buscar en la ayuda" })).toHaveFocus();

    await user.click(links[0]!);
    expect(await screen.findByRole("heading", { level: 1, name: "Conecta tu WhatsApp con el código QR" })).toBeInTheDocument();
    expect(screen.queryByRole("dialog", { name: "Ayuda de esta pantalla" })).not.toBeInTheDocument();
  });

  it("busca dentro del panel y se cierra con Escape", async () => {
    const { user } = await openAt(`/negocios/${CAFE}/conversaciones`);
    await user.click(await screen.findByRole("button", { name: "Ayuda de esta pantalla" }));
    const panel = screen.getByRole("dialog", { name: "Ayuda de esta pantalla" });
    await user.type(within(panel).getByRole("searchbox", { name: "Buscar en la ayuda" }), "masivos");
    expect(await within(panel).findByText("1 resultado")).toBeInTheDocument();
    expect(within(panel).getByRole("link", { name: /Cuida tu número/ })).toBeInTheDocument();
    await user.keyboard("{Escape}");
    expect(screen.queryByRole("dialog", { name: "Ayuda de esta pantalla" })).not.toBeInTheDocument();
  });
});
