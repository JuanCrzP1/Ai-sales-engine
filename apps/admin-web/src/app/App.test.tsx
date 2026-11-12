import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { BusinessDocument } from "../domain/config/types";
import { PersistenceError } from "../repositories/persistenceError";
import { createMemoryBackend, createMemoryWhatsApp, createTestServices, createVerifyingAuthService, TEST_ACCOUNT, type MemoryBackend } from "../test/fakes";
import { SAMPLE_DOCUMENT, SAMPLE_PLANS_DOCUMENT } from "../test/fixtures/sampleDocument";
import { App } from "./App";
import type { ApplicationServices } from "./compositionRoot";
import { PLATFORM_FALLBACK_REPLY } from "../domain/assistant/fallback";

const LOADING = /Abriendo tu panel…|Cargando tu configuración…|Cargando negocios…/;
const CAFE = `/negocios/${SAMPLE_DOCUMENT.tenant_slug}`;

/** Renderiza la app en una ruta y espera a que terminen las cargas. */
async function renderAt(path: string, services: ApplicationServices) {
  window.history.pushState({}, "", path);
  const user = userEvent.setup({ applyAccept: false });
  render(<App services={services} />);
  // Espera contenido real: sin pantalla de carga y con un título de página (las redirecciones dibujan null un instante).
  await waitFor(() => {
    expect(screen.queryByText(LOADING)).not.toBeInTheDocument();
    expect(screen.getAllByRole("heading", { level: 1 }).length).toBeGreaterThan(0);
  });
  return user;
}

/** Abre un negocio guardado del backend en memoria. */
async function renderWorkspace(path: string, seed: BusinessDocument[] = [SAMPLE_DOCUMENT]) {
  const backend = createMemoryBackend(seed);
  const user = await renderAt(`${CAFE}${path}`, createTestServices(backend));
  return { user, backend };
}

const sidebarNav = () => screen.getByRole("navigation", { name: "Menú del negocio" });

/** Abre una pestaña del Asistente IA; si no se está en él, primero entra desde el menú lateral. */
async function openTab(user: ReturnType<typeof userEvent.setup>, name: RegExp) {
  if (!screen.queryByRole("navigation", { name: "Asistente IA" })) await user.click(within(sidebarNav()).getByRole("link", { name: /^Asistente IA/ }));
  await user.click(within(screen.getByRole("navigation", { name: "Asistente IA" })).getByRole("link", { name }));
}

/** Cambia de negocio con el selector de arriba del menú. */
async function switchTo(user: ReturnType<typeof userEvent.setup>, name: string | RegExp) {
  await user.click(screen.getByRole("button", { name: /^Negocio/ }));
  await user.click(await screen.findByRole("menuitem", { name }));
}
const saveButton = () => screen.getByRole("button", { name: "Guardar cambios" });

async function saveAndWait(user: ReturnType<typeof userEvent.setup>) {
  await user.click(saveButton());
  expect(await screen.findByText(/^Guardado ·/)).toBeInTheDocument();
}

/** Publicar se habilita cuando llega la revisión del servidor: pulsarlo antes no haría nada. */
async function publishButton(version: number) {
  const button = await screen.findByRole("button", { name: `Publicar versión ${version}` });
  await waitFor(() => expect(button).toBeEnabled());
  return button;
}

function storedOf(backend: MemoryBackend, slug = SAMPLE_DOCUMENT.tenant_slug): BusinessDocument {
  const document = backend.stored(slug);
  if (!document) throw new Error(`Sin documento guardado para ${slug}.`);
  return document;
}

describe("Acceso local", () => {
  it("muestra una pantalla de carga mientras abre el panel", () => {
    render(<App services={createTestServices()} />);
    expect(screen.getByText("Abriendo tu panel…")).toBeInTheDocument();
  });

  it("entra directo al panel del primer negocio, sin pedir acceso ni mostrar una cuenta", async () => {
    await renderAt("/", createTestServices(createMemoryBackend([SAMPLE_DOCUMENT])));
    expect(await screen.findByRole("heading", { level: 1, name: "Café Aroma" })).toBeInTheDocument();
    expect(window.location.pathname).toBe(CAFE);
    expect(screen.queryByRole("button", { name: /^Cuenta de/ })).not.toBeInTheDocument();
  });

  it("sin negocios da la bienvenida para crear el primero", async () => {
    await renderAt("/", createTestServices());
    expect(await screen.findByRole("heading", { level: 1, name: "Crea tu negocio" })).toBeInTheDocument();
    expect(window.location.pathname).toBe("/nuevo-negocio");
  });

  it("la administración de negocios avisa que solo funciona en este equipo", async () => {
    await renderAt("/negocios", createTestServices());
    expect(screen.getByRole("heading", { level: 1, name: "Tus negocios" })).toBeInTheDocument();
    expect(screen.getByText("Solo en este equipo")).toBeInTheDocument();
    expect(screen.queryByText(/\b(demo|demostración|prototipo)\b/i)).not.toBeInTheDocument();
  });

  it("las pantallas de cuenta no aplican: llevan al panel", async () => {
    for (const path of ["/perfil", "/iniciar-sesion", "/crear-cuenta"]) {
      await renderAt(path, createTestServices());
      expect(await screen.findByRole("heading", { level: 1, name: "Crea tu negocio" })).toBeInTheDocument();
      expect(window.location.pathname).toBe("/nuevo-negocio");
      cleanup();
    }
  });
});

describe("Administración de negocios", () => {
  it("invita a crear el primero cuando no hay ninguno", async () => {
    await renderAt("/negocios", createTestServices());
    expect(screen.getByText("Aún no hay negocios")).toBeInTheDocument();
  });

  it("lista los negocios con su estado", async () => {
    await renderAt("/negocios", createTestServices(createMemoryBackend([SAMPLE_DOCUMENT, SAMPLE_PLANS_DOCUMENT])));
    const list = screen.getByRole("list", { name: "Negocios" });
    expect(within(list).getAllByRole("listitem")).toHaveLength(2);
    expect(within(list).getByText("Café Aroma")).toBeInTheDocument();
    expect(within(list).getByText("Identificador: software_norte · Versión 1")).toBeInTheDocument();
    expect(within(list).getAllByText("Sin publicar")).toHaveLength(2);
  });

  it("crea un negocio con identificador deducido del nombre y abre su espacio de trabajo", async () => {
    const backend = createMemoryBackend();
    const user = await renderAt("/negocios", createTestServices(backend));
    await user.click(screen.getAllByRole("button", { name: "Crear negocio" })[0]!);
    const form = screen.getByRole("form", { name: "Crear negocio" });
    expect(within(form).getByRole("button", { name: "Crear negocio" })).toBeDisabled();

    await user.type(within(form).getByLabelText(/^Nombre comercial/), "Panadería La Esquina");
    expect(within(form).getByLabelText(/^Identificador/)).toHaveValue("panaderia_la_esquina");
    await user.click(within(form).getByRole("button", { name: "Crear negocio" }));

    expect(await screen.findByRole("heading", { level: 1, name: "Configura tu asistente de ventas" })).toBeInTheDocument();
    expect(window.location.pathname).toBe("/negocios/panaderia_la_esquina");
    expect(screen.getByText("Este negocio aún no se ha guardado")).toBeInTheDocument();
    expect(screen.getByText("Panadería La Esquina", { selector: ".switcher__name" })).toBeInTheDocument();
    // Registrar el negocio no crea ninguna versión: todavía no cumple el contrato.
    expect(backend.stored("panaderia_la_esquina")).toBeNull();
  });

  it("ofrece empezar de cero primero y, con una plantilla, crea un borrador con sus ejemplos y avisa que hay que cambiarlos", async () => {
    const backend = createMemoryBackend();
    const user = await renderAt("/negocios", createTestServices(backend));
    await user.click(screen.getAllByRole("button", { name: "Crear negocio" })[0]!);
    const form = screen.getByRole("form", { name: "Crear negocio" });
    const options = await within(form).findAllByRole("radio");
    expect(options.map((option) => option.closest("label")?.querySelector(".template-option__title")?.textContent)).toEqual([
      "Empezar de cero",
      "Restaurante o comida a domicilio",
      "Software o servicio por suscripción",
    ]);
    expect(options[0]).toBeChecked();

    await user.click(within(form).getByRole("radio", { name: /^Restaurante o comida a domicilio/ }));
    expect(within(form).getByText(/Tu negocio empezará con los ejemplos de/)).toBeInTheDocument();
    await user.type(within(form).getByLabelText(/^Nombre comercial/), "Sabor Casero");
    await user.click(within(form).getByRole("button", { name: "Crear negocio" }));

    expect(await screen.findByRole("heading", { level: 1, name: "Tu asistente, sección por sección" })).toBeInTheDocument();
    expect(window.location.pathname).toBe("/negocios/sabor_casero/asistente");
    expect(screen.getByText("Empezaste con la plantilla «Restaurante o comida a domicilio»")).toBeInTheDocument();
    // La plantilla quedó como borrador con el nombre del negocio y sin datos de pago; nada se publicó.
    expect(backend.stored("sabor_casero")).toMatchObject({ tenant_slug: "sabor_casero", identity: { name: "Sabor Casero" }, payments: [] });
    expect((await backend.directory.list()).find((business) => business.slug === "sabor_casero")).toMatchObject({ draftVersion: 1, publishedVersion: null });
  });

  it("si no puede cargar las plantillas, igual deja empezar de cero", async () => {
    const backend = createMemoryBackend();
    backend.failNext("templates", new PersistenceError("unavailable"));
    const user = await renderAt("/negocios", createTestServices(backend));
    await user.click(screen.getAllByRole("button", { name: "Crear negocio" })[0]!);
    const form = screen.getByRole("form", { name: "Crear negocio" });
    expect(await within(form).findByText("No se pudieron cargar las plantillas: puedes empezar de cero.")).toBeInTheDocument();
    expect(within(form).getByRole("radio", { name: /^Empezar de cero/ })).toBeChecked();
    await user.type(within(form).getByLabelText(/^Nombre comercial/), "Panadería Sol");
    await user.click(within(form).getByRole("button", { name: "Crear negocio" }));
    expect(await screen.findByRole("heading", { level: 1, name: "Configura tu asistente de ventas" })).toBeInTheDocument();
  });

  it("no permite repetir un identificador que ya está en la lista", async () => {
    const user = await renderAt("/negocios", createTestServices(createMemoryBackend([SAMPLE_DOCUMENT])));
    await user.click(screen.getByRole("button", { name: "Crear negocio" }));
    const form = screen.getByRole("form", { name: "Crear negocio" });
    await user.type(within(form).getByLabelText(/^Nombre comercial/), "Cafe Aroma");
    expect(within(form).getByText("Ya existe un negocio con ese identificador.")).toBeInTheDocument();
    expect(within(form).getByRole("button", { name: "Crear negocio" })).toBeDisabled();
  });

  it("muestra en su campo el error del servidor al crear, sin salir del formulario", async () => {
    const backend = createMemoryBackend();
    const user = await renderAt("/negocios", createTestServices(backend));
    await user.click(screen.getAllByRole("button", { name: "Crear negocio" })[0]!);
    const form = screen.getByRole("form", { name: "Crear negocio" });
    await user.type(within(form).getByLabelText(/^Nombre comercial/), "Otro");
    backend.failNext("create", new PersistenceError("invalid", { message: "Datos inválidos", problems: [{ path: "slug", message: "Usa solo minúsculas, números y guion bajo." }] }));
    await user.click(within(form).getByRole("button", { name: "Crear negocio" }));
    expect(await within(form).findByText("Usa solo minúsculas, números y guion bajo.")).toBeInTheDocument();
    expect(window.location.pathname).toBe("/negocios");
  });

  it("eliminar exige escribir el identificador y no toca los demás negocios", async () => {
    const backend = createMemoryBackend([SAMPLE_DOCUMENT, SAMPLE_PLANS_DOCUMENT]);
    const user = await renderAt("/negocios", createTestServices(backend));
    await user.click(screen.getByRole("button", { name: "Eliminar Café Aroma" }));
    const confirm = screen.getByRole("button", { name: "Eliminar definitivamente" });
    expect(confirm).toBeDisabled();

    await user.type(screen.getByLabelText(`Para confirmar, escribe ${SAMPLE_DOCUMENT.tenant_slug}`), SAMPLE_DOCUMENT.tenant_slug);
    expect(confirm).toBeEnabled();
    await user.click(confirm);

    expect(await screen.findByText('Se eliminó "Café Aroma".')).toBeInTheDocument();
    expect(backend.stored(SAMPLE_DOCUMENT.tenant_slug)).toBeNull();
    expect(backend.stored(SAMPLE_PLANS_DOCUMENT.tenant_slug)).not.toBeNull();
    expect(within(screen.getByRole("list", { name: "Negocios" })).getAllByRole("listitem")).toHaveLength(1);
  });

  it("informa si no hay nada nuevo que importar", async () => {
    const user = await renderAt("/negocios", createTestServices(createMemoryBackend([SAMPLE_DOCUMENT])));
    await user.click(screen.getByRole("button", { name: "Importar negocios de ejemplo" }));
    expect(await screen.findByText("No había nada nuevo: todos los negocios ya estaban importados.")).toBeInTheDocument();
  });

  it("si no puede cargar los negocios lo informa y permite reintentar", async () => {
    const backend = createMemoryBackend([SAMPLE_DOCUMENT]);
    backend.failNext("list", new PersistenceError("unavailable"));
    const user = await renderAt("/negocios", createTestServices(backend));
    expect(screen.getByText("No se pudieron cargar los negocios")).toBeInTheDocument();
    expect(screen.getByText(/No se pudo conectar con el servidor/)).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Reintentar" }));
    expect(await screen.findByText("Café Aroma")).toBeInTheDocument();
  });

  it("un negocio inexistente se informa sin crear nada", async () => {
    const backend = createMemoryBackend();
    await renderAt("/negocios/no_existe", createTestServices(backend));
    expect(screen.getByRole("heading", { level: 1, name: "Ese negocio no existe" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Volver al panel" })).toBeInTheDocument();
    expect(backend.stored("no_existe")).toBeNull();
  });

  it("si falla la carga de un negocio lo informa sin afirmar que está vacío", async () => {
    const backend = createMemoryBackend([SAMPLE_DOCUMENT]);
    backend.failNext("load", new PersistenceError("unavailable"));
    const user = await renderAt(CAFE, createTestServices(backend));
    expect(screen.getByRole("heading", { level: 1, name: "No se pudo cargar tu configuración" })).toBeInTheDocument();
    expect(screen.getByText(/No se ha borrado nada/)).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Reintentar" }));
    expect(await screen.findByRole("heading", { level: 1, name: "Café Aroma" })).toBeInTheDocument();
  });

  it("cada negocio abre su propia configuración y editar uno no toca el otro", async () => {
    const backend = createMemoryBackend([SAMPLE_DOCUMENT, SAMPLE_PLANS_DOCUMENT]);
    const user = await renderAt(`${CAFE}/negocio`, createTestServices(backend));
    const name = screen.getByLabelText(/^Nombre comercial/);
    await user.clear(name);
    await user.type(name, "Café Nuevo");
    await saveAndWait(user);

    await switchTo(user, "Software Norte");
    expect(await screen.findByText("Software Norte", { selector: ".switcher__name" })).toBeInTheDocument();
    expect(storedOf(backend, SAMPLE_PLANS_DOCUMENT.tenant_slug).identity.name).toBe("Software Norte");
    expect(storedOf(backend).identity.name).toBe("Café Nuevo");
    expect(storedOf(backend).tenant_slug).toBe(SAMPLE_DOCUMENT.tenant_slug);
  });
});

describe("Cuenta (servicio que verifica credenciales)", () => {
  const verifying = (auth: ReturnType<typeof createVerifyingAuthService>) => createTestServices(createMemoryBackend([SAMPLE_DOCUMENT]), { auth });

  it("pide contraseña, rechaza credenciales incorrectas y entra con las correctas", async () => {
    const auth = createVerifyingAuthService();
    await auth.signUp({ ...TEST_ACCOUNT });
    await auth.signOut();
    const user = await renderAt("/", verifying(auth));

    expect(screen.queryByRole("note")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Iniciar sesión" }));
    expect(screen.getByText("Escribe tu contraseña.")).toBeInTheDocument();

    await user.type(screen.getByLabelText(/^Correo electrónico/), TEST_ACCOUNT.email);
    await user.type(screen.getByLabelText(/^Contraseña/), "equivocada1");
    await user.click(screen.getByRole("button", { name: "Iniciar sesión" }));
    expect(await screen.findByText("El correo o la contraseña no son correctos.")).toBeInTheDocument();

    await user.clear(screen.getByLabelText(/^Contraseña/));
    await user.type(screen.getByLabelText(/^Contraseña/), TEST_ACCOUNT.password);
    await user.click(screen.getByRole("button", { name: "Iniciar sesión" }));
    expect(await screen.findByRole("heading", { level: 1, name: "Café Aroma" })).toBeInTheDocument();
  });

  it("sin sesión envía a la entrada y vuelve a la página que se quería abrir", async () => {
    const auth = createVerifyingAuthService();
    await auth.signUp({ ...TEST_ACCOUNT });
    await auth.signOut();
    const user = await renderAt(`${CAFE}/productos`, verifying(auth));
    expect(window.location.pathname).toBe("/iniciar-sesion");

    await user.type(screen.getByLabelText(/^Correo electrónico/), TEST_ACCOUNT.email);
    await user.type(screen.getByLabelText(/^Contraseña/), TEST_ACCOUNT.password);
    await user.click(screen.getByRole("button", { name: "Iniciar sesión" }));
    expect(await screen.findByRole("heading", { level: 1, name: "Productos y servicios" })).toBeInTheDocument();
  });

  it("muestra la contraseña al pedirlo", async () => {
    const user = await renderAt("/iniciar-sesion", verifying(createVerifyingAuthService()));
    const password = screen.getByLabelText(/^Contraseña/);
    expect(password).toHaveAttribute("type", "password");
    await user.click(screen.getByRole("button", { name: "Mostrar contraseña" }));
    expect(password).toHaveAttribute("type", "text");
  });

  it("al crear cuenta exige contraseña segura y su confirmación", async () => {
    const user = await renderAt("/crear-cuenta", verifying(createVerifyingAuthService()));
    await user.type(screen.getByLabelText(/^Tu nombre/), TEST_ACCOUNT.name);
    await user.type(screen.getByLabelText(/^Correo electrónico/), TEST_ACCOUNT.email);
    await user.type(screen.getByLabelText(/^Contraseña/), "corta");
    await user.click(screen.getByRole("button", { name: "Crear cuenta" }));
    expect(screen.getByText(/al menos 8 caracteres/)).toBeInTheDocument();
    expect(screen.getByText("Las contraseñas no coinciden.")).toBeInTheDocument();
  });

  it("muestra el menú de la cuenta en el espacio de trabajo, edita el perfil y cierra sesión", async () => {
    const auth = createVerifyingAuthService();
    await auth.signUp({ ...TEST_ACCOUNT });
    const user = await renderAt(CAFE, verifying(auth));
    const menu = (name = TEST_ACCOUNT.name) => screen.getByRole("button", { name: `Cuenta de ${name}` });

    await user.click(menu());
    await user.keyboard("{Escape}");
    expect(screen.queryByRole("link", { name: "Mi perfil" })).not.toBeInTheDocument();
    expect(menu()).toHaveFocus();

    await user.click(menu());
    // El menú de la foto es solo de la persona; la configuración del negocio está fija abajo en el menú de la izquierda.
    const panel = menu().closest(".user-menu") as HTMLElement;
    expect(within(panel).getAllByRole("link").map((link) => link.textContent)).toEqual(["Mi perfil", "Seguridad", "Notificaciones"]);
    expect(within(panel).queryByRole("link", { name: "Configuración" })).not.toBeInTheDocument();
    expect(within(sidebarNav()).getByRole("link", { name: "Configuración" }).closest(".nav__bottom")).not.toBeNull();
    await user.click(screen.getByRole("link", { name: "Mi perfil" }));
    expect(window.location.pathname).toBe(`${CAFE}/cuenta/perfil`);
    expect(within(screen.getByRole("navigation", { name: "Mi cuenta" })).getByRole("link", { name: /Mi perfil/ })).toHaveAttribute("aria-current", "page");
    const name = await screen.findByLabelText(/^Nombre/);
    await user.clear(name);
    await user.type(name, "Laura Ruiz");
    await user.click(screen.getByRole("button", { name: "Guardar cambios" }));
    expect(await screen.findByText("Tus datos se guardaron.")).toBeInTheDocument();

    await user.upload(screen.getByLabelText("Cambiar foto"), new File(["texto"], "notas.txt", { type: "text/plain" }));
    expect(await screen.findByText("Usa una imagen JPG, PNG, WebP o GIF.")).toBeInTheDocument();
  });
});

describe("Mi cuenta → Seguridad", () => {
  const verifying = (auth: ReturnType<typeof createVerifyingAuthService>) => createTestServices(createMemoryBackend([SAMPLE_DOCUMENT]), { auth });
  it("cambia la contraseña pidiendo la actual y cierra la sesión en los demás equipos", async () => {
    const auth = createVerifyingAuthService() as ReturnType<typeof createVerifyingAuthService> & { readonly otherDevicesSignedOut: number };
    await auth.signUp({ ...TEST_ACCOUNT });
    const user = await renderAt(`${CAFE}/cuenta/seguridad`, verifying(auth));
    expect(await screen.findByRole("heading", { level: 1, name: "Seguridad" })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Cambiar contraseña" }));
    expect(screen.getByText("Escribe tu contraseña actual.")).toBeInTheDocument();

    await user.type(screen.getByLabelText(/^Contraseña actual/), "equivocada1");
    await user.type(screen.getByLabelText(/^Contraseña nueva/), "nueva-clave-9");
    await user.type(screen.getByLabelText(/^Repite la contraseña nueva/), "nueva-clave-9");
    await user.click(screen.getByRole("button", { name: "Cambiar contraseña" }));
    expect(await screen.findByText("La contraseña actual no es correcta.")).toBeInTheDocument();

    await user.clear(screen.getByLabelText(/^Contraseña actual/));
    await user.type(screen.getByLabelText(/^Contraseña actual/), TEST_ACCOUNT.password);
    await user.click(screen.getByRole("button", { name: "Cambiar contraseña" }));
    expect(await screen.findByText("Listo, tu contraseña cambió.")).toBeInTheDocument();
    expect(auth.otherDevicesSignedOut).toBe(1);
    // La nueva sirve para entrar.
    await auth.signOut();
    await expect(auth.signIn({ email: TEST_ACCOUNT.email, password: "nueva-clave-9" })).resolves.toBeTruthy();
  });

  it("cierra la sesión en los demás equipos con confirmación, y el perfil viejo lleva a Mi cuenta", async () => {
    const auth = createVerifyingAuthService() as ReturnType<typeof createVerifyingAuthService> & { readonly otherDevicesSignedOut: number };
    await auth.signUp({ ...TEST_ACCOUNT });
    const user = await renderAt(`${CAFE}/cuenta/seguridad`, verifying(auth));
    await user.click(await screen.findByRole("button", { name: "Cerrar sesión en los demás equipos" }));
    await user.click(screen.getByRole("button", { name: "Sí, cerrarlas" }));
    expect(await screen.findByText(/cerramos tu sesión en los demás equipos/)).toBeInTheDocument();
    expect(auth.otherDevicesSignedOut).toBe(1);
    cleanup();
    await renderAt(`${CAFE}/configuracion/perfil`, verifying(auth));
    expect(await screen.findByRole("heading", { level: 1, name: "Mi perfil" })).toBeInTheDocument();
    expect(window.location.pathname).toBe(`${CAFE}/cuenta/perfil`);
  });
});

describe("Secciones del negocio", () => {
  it("con todo configurado, el inicio pone primero lo del día y el progreso en una franja pequeña", async () => {
    await renderWorkspace("");
    expect(screen.getByRole("heading", { level: 1, name: "Café Aroma" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Configura tu asistente de ventas" })).not.toBeInTheDocument();
    const today = screen.getByRole("region", { name: "Hoy en tu negocio" });
    const ready = screen.getByRole("region", { name: "Estado del asistente" });
    expect(within(ready).getByText("Tu asistente está configurado")).toBeInTheDocument();
    // Las cifras del día van antes que el estado de la configuración.
    expect(today.compareDocumentPosition(ready) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("muestra el inicio con el resumen y el estado real de WhatsApp, sin inventar", async () => {
    await renderWorkspace("");
    expect(screen.getByRole("heading", { level: 2, name: "Café Aroma" })).toBeInTheDocument();
    // El WhatsApp de prueba está sin conectar: el inicio lo dice tal cual.
    expect(await screen.findByText("WhatsApp sin conectar")).toBeInTheDocument();
    expect(screen.queryByText(/desplegado|en producción|conectado al asistente real\./i)).not.toBeInTheDocument();
  });

  it("navega entre todas las secciones desde el menú lateral", async () => {
    const { user } = await renderWorkspace("");
    const expectations: [string, string, string][] = [
      ["Mi negocio", "Mi negocio", "Paso 1"],
      ["Productos y servicios", "Productos y servicios", "Paso 2"],
      ["Pagos y cierre", "Pagos y cierre de ventas", "Paso 3"],
      ["Cómo atiende", "Cómo atiende el asistente", "Paso 4"],
      ["Mensajes y canales", "Mensajes y canales", "Paso 5"],
      ["Publicar", "Revisión y publicación", "Último paso"],
    ];
    for (const [link, heading, step] of expectations) {
      await openTab(user, new RegExp(`^${link}`));
      expect(screen.getByRole("heading", { level: 1, name: heading })).toBeInTheDocument();
      expect(screen.getByText(step)).toBeInTheDocument();
    }
  });

  it("valida los datos del negocio mientras se escriben", async () => {
    const { user } = await renderWorkspace("/negocio");
    const name = screen.getByLabelText(/Nombre comercial/);
    await user.clear(name);
    expect(screen.getByText("Escribe el nombre comercial de tu negocio.")).toBeInTheDocument();
    expect(name).toHaveAttribute("aria-invalid", "true");

    await user.type(name, "Panadería Central");
    expect(screen.queryByText("Escribe el nombre comercial de tu negocio.")).not.toBeInTheDocument();
    expect(screen.getByText("Panadería Central", { selector: ".switcher__name" })).toBeInTheDocument();
  });

  it("guarda identidad, ubicación y lo que hace falta para atender", async () => {
    const { user, backend } = await renderWorkspace("/negocio");
    await user.type(screen.getByLabelText(/^Marca/), "Aroma");
    const address = screen.getByLabelText(/^Dirección/);
    await user.clear(address);
    await user.type(address, "Carrera 5 #10-20");
    await user.type(screen.getByLabelText("Pruebas de confianza"), "Más de 500 clientes{Enter}");
    await user.click(screen.getByRole("checkbox", { name: /^Virtual/ }));
    await saveAndWait(user);

    const { identity } = storedOf(backend);
    expect(identity.brand_name).toBe("Aroma");
    expect(identity.location?.address).toBe("Carrera 5 #10-20");
    expect(identity.credibility).toEqual(["Más de 500 clientes"]);
    expect(identity.service_modes).toContain("virtual");
  });

  it("lo escrito en una lista no se pierde aunque no se pulse «Agregar»", async () => {
    const { user, backend } = await renderWorkspace("/negocio");
    await user.type(screen.getByLabelText("Por qué elegirte"), "Domicilio gratis");
    await user.click(screen.getByLabelText(/^Marca/));
    expect(screen.getByLabelText("Por qué elegirte: elemento 2")).toHaveValue("Domicilio gratis");
    await saveAndWait(user);
    expect(storedOf(backend).identity.differentiators).toEqual(["Pan horneado cada mañana", "Domicilio gratis"]);
  });

  it("agrega, valida, edita, pausa y elimina productos del catálogo", async () => {
    const { user, backend } = await renderWorkspace("/productos");
    const list = () => screen.getByRole("list", { name: "Productos y servicios" });
    expect(within(list()).getAllByRole("listitem")).toHaveLength(3);

    await user.click(screen.getByRole("button", { name: "Agregar producto" }));
    const editor = within(screen.getByRole("form", { name: "Nuevo producto" }));
    await user.click(editor.getByRole("button", { name: "Agregar producto a la lista" }));
    expect(screen.getByText("Cada producto o servicio necesita un nombre.")).toBeInTheDocument();

    await user.type(editor.getByLabelText(/^Nombre/), "Jugo de naranja");
    await user.type(editor.getByLabelText(/^Categoría/), "Bebidas");
    await user.type(editor.getByLabelText(/^Precio/), "7000");
    await user.click(editor.getByRole("button", { name: "Agregar producto a la lista" }));
    expect(within(list()).getAllByRole("listitem")).toHaveLength(4);

    await user.click(within(list()).getByRole("button", { name: "Editar Jugo de naranja" }));
    const nameInput = screen.getByLabelText(/^Nombre/);
    await user.clear(nameInput);
    await user.type(nameInput, "Jugo natural");
    await user.click(screen.getByRole("button", { name: "Aplicar cambios" }));
    expect(within(list()).getByText("Jugo natural")).toBeInTheDocument();

    const row = within(list()).getByText("Jugo natural").closest("li")!;
    await user.click(within(row).getByRole("button", { name: "Pausar" }));
    expect(within(row).getByText("No disponible")).toBeInTheDocument();
    await saveAndWait(user);

    const items = storedOf(backend).offer.catalog?.items ?? [];
    expect(items.find((item) => item.name === "Jugo natural")).toMatchObject({ category: "bebidas", available: false, prices: [{ currency: "COP", amount: 7000 }] });

    const saved = within(list()).getByText("Jugo natural").closest("li")!;
    await user.click(within(saved).getByRole("button", { name: "Eliminar" }));
    await user.click(within(saved).getByRole("button", { name: "Sí, eliminar" }));
    expect(within(list()).getAllByRole("listitem")).toHaveLength(3);
    await saveAndWait(user);
    expect((storedOf(backend).offer.catalog?.items ?? []).some((item) => item.name === "Jugo natural")).toBe(false);
  });

  it("modifica precios de un plan, incluido un precio en otra moneda", async () => {
    const backend = createMemoryBackend([SAMPLE_PLANS_DOCUMENT]);
    const user = await renderAt(`/negocios/${SAMPLE_PLANS_DOCUMENT.tenant_slug}/productos`, createTestServices(backend));
    await user.click(screen.getByRole("button", { name: "Editar Básico" }));
    const monthly = screen.getByLabelText(/^Precio mensual/);
    await user.clear(monthly);
    await user.type(monthly, "65000");
    await user.click(screen.getByRole("button", { name: "Agregar precio en otra moneda" }));
    await user.click(screen.getByRole("button", { name: "Aplicar cambios" }));
    expect(screen.getByText(/indica un precio mayor que cero/)).toBeInTheDocument();

    await user.type(screen.getAllByLabelText(/^Precio mensual/)[1]!, "20");
    await user.click(screen.getByRole("button", { name: "Aplicar cambios" }));
    await saveAndWait(user);
    expect(storedOf(backend, SAMPLE_PLANS_DOCUMENT.tenant_slug).offer.plans?.[0]?.prices).toEqual([
      { currency: "COP", monthly: 65000 },
      { currency: "USD", monthly: 20 },
    ]);
  });

  it("renombrar una categoría no cambia su identificador ni sus productos", async () => {
    const { user, backend } = await renderWorkspace("/productos");
    const category = screen.getByLabelText(/^Categoría 1/);
    await user.clear(category);
    await user.type(category, "Café y bebidas");
    await saveAndWait(user);
    const catalog = storedOf(backend).offer.catalog;
    expect(catalog?.categories[0]).toEqual({ id: "bebidas", name: "Café y bebidas" });
    expect(catalog?.items[0]?.category).toBe("bebidas");
  });

  it("cambiar la forma de venta pide confirmación porque convierte lo que hay", async () => {
    const { user, backend } = await renderWorkspace("/negocio");
    await user.click(screen.getByRole("radio", { name: /^Planes o servicios/ }));
    expect(screen.getByText("Se convertirá lo que ya tienes")).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: /^Catálogo de productos/ })).toBeChecked();
    await user.click(screen.getByRole("button", { name: "Cancelar" }));
    expect(screen.queryByText("Se convertirá lo que ya tienes")).not.toBeInTheDocument();

    await user.click(screen.getByRole("radio", { name: /^Planes o servicios/ }));
    await user.click(screen.getByRole("button", { name: "Sí, convertir" }));
    await saveAndWait(user);
    expect(storedOf(backend).offer.model).toBe("plans");
    expect(storedOf(backend).offer.plans?.map((plan) => plan.name)).toEqual(["Café americano", "Croissant de mantequilla", "Desayuno completo"]);
  });

  it("administra promociones con confirmación al quitar y detecta las vencidas", async () => {
    const { user, backend } = await renderWorkspace("/pagos");
    await user.click(screen.getByRole("button", { name: "Agregar promoción" }));
    const promotion = within(screen.getByRole("group", { name: "Promoción 2" }));
    await user.type(promotion.getByLabelText(/^Nombre/), "Dos por uno");
    expect(screen.getByText("Explica en qué consiste la promoción.")).toBeInTheDocument();
    await user.type(promotion.getByLabelText(/^Qué incluye y a qué aplica/), "En croissants los martes");
    await user.type(promotion.getByLabelText(/^Vigente hasta/), "2020-01-31");
    expect(screen.getByText("Esta promoción ya venció: el asistente no la ofrecerá.")).toBeInTheDocument();
    await saveAndWait(user);
    expect(storedOf(backend).terms.promotions).toEqual([
      { name: "Desayuno del lunes", details: "10 % de descuento en desayunos los lunes", valid_until: null },
      { name: "Dos por uno", details: "En croissants los martes", valid_until: "2020-01-31" },
    ]);

    await user.click(screen.getAllByRole("button", { name: "Quitar promoción" })[0]!);
    await user.click(screen.getByRole("button", { name: "Sí, quitar" }));
    await saveAndWait(user);
    expect(storedOf(backend).terms.promotions?.map((promotion) => promotion.name)).toEqual(["Dos por uno"]);
  });

  it("administra condiciones y políticas", async () => {
    const { user, backend } = await renderWorkspace("/pagos");
    await user.type(screen.getByLabelText(/^Garantía/), "Cambio si llega en mal estado.");
    await user.type(screen.getByLabelText(/^Cancelaciones y reembolsos/), "Hasta una hora antes.");
    await user.click(screen.getByRole("button", { name: "Quitar de Condiciones de compra: elemento 1" }));
    expect(screen.queryByRole("button", { name: "Quitar de Condiciones de compra: elemento 1" })).not.toBeInTheDocument();
    await saveAndWait(user);

    const { terms } = storedOf(backend);
    expect(terms.policies).toMatchObject({ warranty: "Cambio si llega en mal estado.", cancellation: "Hasta una hora antes." });
    expect(terms.conditions ?? []).toEqual([]);
  });

  it("administra personalidad e instrucciones del asistente", async () => {
    const { user, backend } = await renderWorkspace("/atencion");
    const tone = screen.getByLabelText(/^Tono de comunicación/);
    await user.clear(tone);
    await user.type(tone, "formal y claro");
    await user.selectOptions(screen.getByLabelText(/^Trato al cliente/), "formal");
    await user.selectOptions(screen.getByLabelText(/^¿Puede usar emojis\?/), "no");
    await user.click(screen.getByRole("radio", { name: /^Equilibradas/ }));
    await user.type(screen.getByLabelText("Cómo debe expresarse"), "No uses tecnicismos{Enter}");
    await user.type(screen.getByLabelText("Cómo debe vender en este negocio"), "Pregunta para cuántas personas es{Enter}");
    await saveAndWait(user);

    const { response_style: style, sales } = storedOf(backend);
    expect(style).toMatchObject({ tone: "formal y claro", formality: "formal", emojis: false, length: "medium", instructions: ["No uses tecnicismos"] });
    expect(sales.instructions).toEqual(["Confirma la dirección antes de cerrar el pedido.", "Pregunta para cuántas personas es"]);
  });

  it("valida el límite de palabras contra el largo elegido", async () => {
    const { user } = await renderWorkspace("/atencion");
    await user.type(screen.getByLabelText(/^Límite de palabras/), "5");
    expect(screen.getByText(/Con respuestas cortas, el límite debe ser/)).toBeInTheDocument();
  });

  it("edita un problema del cliente conservando sus demás datos", async () => {
    const document = structuredClone(SAMPLE_DOCUMENT);
    document.sales.customer_problems = [{ id: "problema_1", impacts: ["no tienen tiempo", "desayunan mal"], signals: ["voy tarde"] }];
    const { user, backend } = await renderWorkspace("/atencion", [document]);
    const problem = screen.getByLabelText("Problema 1");
    await user.clear(problem);
    await user.type(problem, "salen con prisa");
    await saveAndWait(user);
    expect(storedOf(backend).sales.customer_problems).toEqual([{ id: "problema_1", impacts: ["salen con prisa", "desayunan mal"], signals: ["voy tarde"] }]);
  });

  it("recomienda solo elementos de la oferta y avisa si no están disponibles", async () => {
    const { user, backend } = await renderWorkspace("/atencion");
    const recommend = screen.getByLabelText(/^Recomendar/);
    expect(within(recommend).getByRole("option", { name: "Café americano" })).toBeInTheDocument();
    await user.selectOptions(recommend, "sample_desayuno");
    expect(screen.getByText("Ese elemento no está disponible: el asistente no lo recomendará.")).toBeInTheDocument();
    await saveAndWait(user);
    expect(storedOf(backend).sales.recommendation_rules).toEqual([{ when: "pide café", recommend: "sample_desayuno" }]);
  });

  it("crea, edita y elimina preguntas frecuentes", async () => {
    const { user, backend } = await renderWorkspace("/atencion");
    await user.click(screen.getByRole("button", { name: "Agregar pregunta frecuente" }));
    const second = within(screen.getByRole("group", { name: "Pregunta 2" }));
    expect(screen.getByText("Escribe la pregunta o elimínala.")).toBeInTheDocument();
    await user.type(second.getByLabelText(/^Pregunta/), "¿Tienen opción sin azúcar?");
    await user.type(second.getByLabelText(/^Respuesta/), "Sí, en todas las bebidas.");
    await saveAndWait(user);
    expect(storedOf(backend).knowledge.faqs).toHaveLength(2);

    const first = within(screen.getByRole("group", { name: "Pregunta 1" })).getByLabelText(/^Respuesta/);
    await user.clear(first);
    await user.type(first, "Sí, en todo el barrio.");
    await user.click(screen.getByRole("button", { name: "Quitar pregunta 2" }));
    await user.click(screen.getByRole("button", { name: "Sí, quitar" }));
    await saveAndWait(user);
    expect(storedOf(backend).knowledge.faqs).toEqual([{ question: "¿Hacen domicilios?", answer: "Sí, en todo el barrio." }]);
  });

  it("muestra la vista previa del mensaje de bienvenida y guarda los mensajes", async () => {
    const { user, backend } = await renderWorkspace("/mensajes");
    const welcome = screen.getByLabelText(/^Mensaje/);
    await user.clear(welcome);
    await user.type(welcome, "Hola, soy tu asistente");
    const preview = screen.getAllByRole("figure", { name: "Vista previa de la conversación" })[0]!;
    expect(within(preview).getByText("Hola, soy tu asistente")).toBeInTheDocument();
    await user.type(screen.getByLabelText(/^Después de una compra/), "¡Gracias por tu compra!");
    await saveAndWait(user);
    expect(storedOf(backend).messages).toMatchObject({ welcome: { enabled: true, text: "Hola, soy tu asistente" }, after_sale: "¡Gracias por tu compra!" });
  });

  it("el mensaje para cuando la IA no puede responder se ve en la vista previa y se guarda", async () => {
    const { user, backend } = await renderWorkspace("/mensajes");
    const card = screen.getByRole("heading", { name: "Si el asistente no puede responder" }).closest("section") as HTMLElement;
    const preview = within(card).getByRole("figure", { name: "Vista previa de la conversación" });
    expect(within(preview).getByText(PLATFORM_FALLBACK_REPLY)).toBeInTheDocument();
    await user.type(within(card).getByLabelText(/^Lo que recibe el cliente/), "Ahora no podemos responder. Llámanos al 300 123 4567.");
    expect(within(preview).getByText("Ahora no podemos responder. Llámanos al 300 123 4567.")).toBeInTheDocument();
    await saveAndWait(user);
    expect(storedOf(backend).messages.fallback).toBe("Ahora no podemos responder. Llámanos al 300 123 4567.");
  });

  it("marcar un canal no afirma conectarlo", async () => {
    const { user, backend } = await renderWorkspace("/mensajes");
    expect(screen.getByText(/no lo conecta/)).toBeInTheDocument();
    await user.click(screen.getByRole("checkbox", { name: /^Instagram/ }));
    await saveAndWait(user);
    expect(storedOf(backend).capabilities.service_channels).toEqual(["whatsapp", "instagram"]);
  });

  it("elegir cierres y acciones mantiene cada acción en su lista", async () => {
    const { user, backend } = await renderWorkspace("/pagos");
    await user.click(screen.getByRole("checkbox", { name: /^Hacer seguimiento/ }));
    await user.click(screen.getByRole("checkbox", { name: /^Agendar citas/ }));
    await user.click(screen.getByRole("checkbox", { name: /^Responder dudas/ }));
    await user.click(screen.getByRole("switch", { name: /^Ofrecer atención de una persona/ }));
    expect(screen.queryByText(/aún no avisa a nadie de tu equipo/)).not.toBeInTheDocument();
    await saveAndWait(user);

    const { capabilities } = storedOf(backend);
    expect(capabilities.actions_primary).toEqual(["tomar_pedido", "cerrar_venta", "agendar_cita"]);
    expect(capabilities.actions_support).toEqual(["confirmar_datos", "seguimiento"]);
    expect(capabilities.closing_methods.human_handoff).toBe(true);
  });

  it("exige al menos una forma de cerrar la venta", async () => {
    const { user } = await renderWorkspace("/pagos");
    await user.click(screen.getByRole("switch", { name: /^Compartir datos de pago/ }));
    await user.click(screen.getByRole("switch", { name: /^Pedir datos al cliente/ }));
    expect(screen.getByText("Activa al menos una forma de cerrar la venta.")).toBeInTheDocument();
  });
});

describe("Datos de pago", () => {
  it("nunca muestra un valor guardado y solo permite reemplazarlo", async () => {
    const { user, backend } = await renderWorkspace("/pagos");
    expect(screen.getAllByText("Guardado de forma segura")).toHaveLength(2);
    expect(screen.queryByLabelText(/^Enlace de pago/)).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Reemplazar Enlace de pago" }));
    const link = screen.getByLabelText(/^Enlace de pago/);
    expect(link).toHaveValue("");
    await user.type(link, "pagos-sin-protocolo");
    expect(screen.getByText("El enlace debe ser una dirección web válida (https://…).")).toBeInTheDocument();

    // Con un dato de pago inválido no se envía nada al servidor.
    await user.click(saveButton());
    expect(await screen.findByText("No se pudo guardar")).toBeInTheDocument();
    expect(backend.paymentValuesReceived).toEqual([]);

    await user.clear(link);
    await user.type(link, "https://pagos.example.com/cafe");
    await saveAndWait(user);

    const [values] = backend.paymentValuesReceived;
    expect(Object.values(values ?? {})).toEqual(["https://pagos.example.com/cafe"]);
    // Tras guardar, el valor deja de estar en la interfaz.
    expect(screen.getAllByText("Guardado de forma segura")).toHaveLength(2);
    expect(screen.queryByDisplayValue("https://pagos.example.com/cafe")).not.toBeInTheDocument();
  });

  it("permite arrepentirse de reemplazar y conservar el dato guardado", async () => {
    const { user } = await renderWorkspace("/pagos");
    await user.click(screen.getByRole("button", { name: "Reemplazar Enlace de pago" }));
    await user.click(screen.getByRole("button", { name: "Conservar el dato guardado" }));
    expect(screen.getAllByText("Guardado de forma segura")).toHaveLength(2);
    expect(screen.queryByText("Cambios sin guardar")).not.toBeInTheDocument();
  });

  it("un negocio sin pagos puede crear su perfil, activar un enlace y agregar cuentas", async () => {
    const backend = createMemoryBackend([SAMPLE_PLANS_DOCUMENT]);
    const user = await renderAt(`/negocios/${SAMPLE_PLANS_DOCUMENT.tenant_slug}/pagos`, createTestServices(backend));
    expect(screen.getByText("Todavía no hay medios de pago")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Configurar medios de pago" }));
    await user.click(screen.getByRole("switch", { name: "Ofrecer pago por enlace" }));
    await user.type(screen.getByLabelText(/^Enlace de pago/), "https://pagos.example.com/norte");
    await user.click(screen.getByRole("switch", { name: "Aceptar transferencias" }));
    expect(screen.getByText("Agrega al menos una cuenta o desactiva las transferencias.")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Agregar cuenta" }));
    expect(screen.getByText("Escribe un celular de 10 dígitos que empiece por 3.")).toBeInTheDocument();
    await user.type(screen.getByLabelText(/^Número de celular/), "300 123 4567");
    await saveAndWait(user);

    const [profile] = storedOf(backend, SAMPLE_PLANS_DOCUMENT.tenant_slug).payments;
    expect(profile?.link?.secret_ref).toMatch(/^secret_store:principal\.link\..+~/);
    expect(profile?.transfer_methods?.[0]?.number?.secret_ref).toMatch(/^secret_store:principal\.nequi\.number\..+~/);
    // Los valores viajan aparte del documento y normalizados.
    expect(Object.values(backend.paymentValuesReceived[0] ?? {}).sort()).toEqual(["3001234567", "https://pagos.example.com/norte"]);
    expect(JSON.stringify(storedOf(backend, SAMPLE_PLANS_DOCUMENT.tenant_slug))).not.toContain("3001234567");
  });

  it("al cambiar el tipo de una cuenta descarta los datos del tipo anterior", async () => {
    const { user, backend } = await renderWorkspace("/pagos");
    const account = screen.getByRole("group", { name: "Cuenta 1" });
    await user.selectOptions(within(account).getByLabelText("Tipo"), "bank");
    expect(within(account).queryByLabelText(/^Número de celular/)).not.toBeInTheDocument();
    expect(within(account).getByText("Escribe el nombre del banco.")).toBeInTheDocument();

    await user.type(within(account).getByLabelText(/^Banco/), "Banco Ejemplo");
    await user.type(within(account).getByLabelText(/^Número de cuenta/), "123-456-789");
    await saveAndWait(user);

    const [method] = storedOf(backend).payments[0]?.transfer_methods ?? [];
    expect(method).toMatchObject({ type: "bank", bank: "Banco Ejemplo", account_type: "ahorros" });
    expect(method?.number).toBeUndefined();
    expect(Object.values(backend.paymentValuesReceived[0] ?? {})).toEqual(["123456789"]);
  });

  it("la revisión nunca muestra referencias ni valores de pago", async () => {
    await renderWorkspace("/revision");
    expect(screen.getByText("2 configurados, guardados de forma segura")).toBeInTheDocument();
    expect(document.body.textContent).not.toContain("secret_store");
  });

  const overview = () => within(screen.getByRole("list", { name: "Métodos de pago configurados" }));
  const LINK_REF = "secret_store:principal.link~guardado";
  const NUMBER_REF = "secret_store:principal.transfer.0.number~guardado";

  it("muestra cada método con su estado y solo una parte del dato", async () => {
    const { user } = await renderWorkspace("/pagos");
    expect(overview().getByText("Enlace de pago")).toBeInTheDocument();
    expect(overview().getByText("Nequi")).toBeInTheDocument();
    expect(overview().getAllByText("Activo")).toHaveLength(2);
    expect(overview().getAllByText("••••0000")).toHaveLength(2);

    // Tras reemplazar un dato se ve la parte visible del nuevo, nunca el valor completo.
    await user.click(screen.getByRole("button", { name: "Reemplazar Número de celular" }));
    await user.type(screen.getByLabelText(/^Número de celular/), "3001234567");
    expect(overview().getByText("Sin guardar")).toBeInTheDocument();
    await saveAndWait(user);
    expect(overview().getByText("••••4567")).toBeInTheDocument();
    expect(document.body.textContent).not.toContain("3001234567");
  });

  it("edita los datos descriptivos, desactiva y activa una cuenta sin enviar ningún dato de pago", async () => {
    const { user, backend } = await renderWorkspace("/pagos");
    const account = within(screen.getByRole("group", { name: "Cuenta 1" }));
    await user.type(account.getByLabelText(/^Titular o etiqueta/), "Cuenta de la tienda");
    await user.click(account.getByRole("switch", { name: /^Cuenta activa/ }));
    expect(account.getByText("Inactiva")).toBeInTheDocument();
    expect(overview().getByText("Inactivo")).toBeInTheDocument();
    expect(overview().getByText("Cuenta de la tienda")).toBeInTheDocument();
    await saveAndWait(user);

    expect(backend.paymentValuesReceived).toEqual([{}]);
    expect(storedOf(backend).payments[0]?.transfer_methods?.[0]).toEqual({ type: "nequi", number: { secret_ref: NUMBER_REF }, label: "Cuenta de la tienda", enabled: false });

    await user.click(within(screen.getByRole("group", { name: "Cuenta 1" })).getByRole("switch", { name: /^Cuenta activa/ }));
    await saveAndWait(user);
    expect(storedOf(backend).payments[0]?.transfer_methods?.[0]?.enabled).toBeNull();
    expect(overview().getAllByText("Activo")).toHaveLength(2);
  });

  it("reemplazar sin escribir nada conserva el dato y no cuenta como un cambio", async () => {
    const { user, backend } = await renderWorkspace("/pagos");
    await user.click(screen.getByRole("button", { name: "Reemplazar Enlace de pago" }));
    expect(screen.getByText(/Si lo dejas vacío, se conserva el dato guardado \(••••0000\)/)).toBeInTheDocument();
    expect(screen.queryByText("Cambios sin guardar")).not.toBeInTheDocument();
    expect(screen.queryByText("Pega el enlace de pago o desactiva esta opción.")).not.toBeInTheDocument();

    await user.type(screen.getByLabelText(/^Garantía/), "Un año.");
    await saveAndWait(user);
    expect(backend.paymentValuesReceived).toEqual([{}]);
    expect(storedOf(backend).payments[0]?.link?.secret_ref).toBe(LINK_REF);
    expect(screen.getAllByText("Guardado de forma segura")).toHaveLength(2);
  });

  it("avisa cuando un dato falta o no se puede leer, para que se reemplace", async () => {
    const backend = createMemoryBackend([SAMPLE_DOCUMENT]);
    backend.paymentFieldStates.set(LINK_REF, { status: "missing", masked: null });
    backend.paymentFieldStates.set(NUMBER_REF, { status: "unreadable", masked: null });
    const user = await renderAt(`${CAFE}/pagos`, createTestServices(backend));
    expect(screen.getByText("Falta este dato")).toBeInTheDocument();
    expect(screen.getByText("No se puede leer con la clave actual")).toBeInTheDocument();
    expect(overview().getByText("Falta el dato")).toBeInTheDocument();
    expect(overview().getByText("No se puede leer")).toBeInTheDocument();
    expect(screen.queryByText("Guardado de forma segura")).not.toBeInTheDocument();

    // Aquí no hay nada que conservar, y el formulario no promete lo contrario.
    await user.click(screen.getByRole("button", { name: "Reemplazar Enlace de pago" }));
    expect(screen.queryByText(/Si lo dejas vacío/)).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Conservar el dato guardado" })).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Cancelar" }));
    expect(screen.getByText("Falta este dato")).toBeInTheDocument();
  });

  it("desactivar el enlace guardado lo conserva; quitarlo es otra acción y pide confirmación", async () => {
    const { user, backend } = await renderWorkspace("/pagos");
    await user.click(screen.getByRole("switch", { name: "Ofrecer pago por enlace" }));
    expect(screen.getByText("Desactivado: el enlace se conserva, pero el asistente no lo ofrece.")).toBeInTheDocument();
    expect(screen.getAllByText("Guardado de forma segura")).toHaveLength(2);
    await saveAndWait(user);
    expect(storedOf(backend).payments[0]).toMatchObject({ link: { secret_ref: LINK_REF }, link_enabled: false });

    await user.click(screen.getByRole("switch", { name: /^Ofrecer pago por enlace/ }));
    await saveAndWait(user);
    expect(storedOf(backend).payments[0]?.link_enabled).toBeNull();
    expect(storedOf(backend).payments[0]?.link?.secret_ref).toBe(LINK_REF);

    await user.click(screen.getByRole("button", { name: "Quitar enlace" }));
    expect(storedOf(backend).payments[0]?.link?.secret_ref).toBe(LINK_REF);
    await user.click(screen.getByRole("button", { name: "Sí, quitar" }));
    await saveAndWait(user);
    expect(storedOf(backend).payments[0]?.link).toBeNull();
    expect(overview().queryByText("Enlace de pago")).not.toBeInTheDocument();
  });

  it("con las transferencias apagadas las cuentas se siguen viendo, como inactivas", async () => {
    const { user } = await renderWorkspace("/pagos");
    await user.click(screen.getByRole("switch", { name: "Aceptar transferencias" }));
    expect(screen.getByText(/Las transferencias están desactivadas/)).toBeInTheDocument();
    expect(within(screen.getByRole("group", { name: "Cuenta 1" })).getByText("Inactiva")).toBeInTheDocument();
    expect(overview().getByText("Inactivo")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Agregar cuenta" })).not.toBeInTheDocument();
  });
});

describe("Borrador de un producto o plan", () => {
  it("lo escrito sigue ahí al volver de otra sección y no se guarda sin aplicarlo", async () => {
    const { user, backend } = await renderWorkspace("/productos");
    await user.click(screen.getByRole("button", { name: "Agregar producto" }));
    await user.type(within(screen.getByRole("form", { name: "Nuevo producto" })).getByLabelText(/^Nombre/), "Jugo de mango");

    await openTab(user, /^Mi negocio/);
    expect(screen.getByRole("heading", { level: 1, name: "Mi negocio" })).toBeInTheDocument();
    expect(screen.getByText("Cambios sin guardar")).toBeInTheDocument();
    await openTab(user, /^Productos y servicios/);
    const editor = within(screen.getByRole("form", { name: "Nuevo producto" }));
    expect(editor.getByLabelText(/^Nombre/)).toHaveValue("Jugo de mango");

    // Guardar no lo pierde en silencio: lo explica y no envía nada.
    await user.click(saveButton());
    expect((await screen.findAllByText(/Aplícalo a la lista o cancélalo antes de guardar/)).length).toBeGreaterThan(0);
    expect(backend.paymentValuesReceived).toEqual([]);
    expect(editor.getByLabelText(/^Nombre/)).toHaveValue("Jugo de mango");

    // Cancelarlo deja todo como estaba.
    await user.click(editor.getByRole("button", { name: "Cancelar" }));
    expect(screen.queryByRole("form", { name: "Nuevo producto" })).not.toBeInTheDocument();
    expect(screen.queryByText("Cambios sin guardar")).not.toBeInTheDocument();
    expect(screen.queryByText(/Aplícalo a la lista/)).not.toBeInTheDocument();
  });

  it("aplicado a la lista, se guarda con lo demás", async () => {
    const { user, backend } = await renderWorkspace("/productos");
    await user.click(screen.getByRole("button", { name: "Agregar producto" }));
    const editor = within(screen.getByRole("form", { name: "Nuevo producto" }));
    await user.type(editor.getByLabelText(/^Nombre/), "Jugo de mango");
    await user.type(editor.getByLabelText(/^Categoría/), "Bebidas");
    await user.clear(editor.getByLabelText(/^Precio/));
    await user.type(editor.getByLabelText(/^Precio/), "7000");
    await openTab(user, /^Mi negocio/);
    await openTab(user, /^Productos y servicios/);
    await user.click(screen.getByRole("button", { name: "Agregar producto a la lista" }));
    await saveAndWait(user);
    expect(storedOf(backend).offer.catalog?.items.some((item) => item.name === "Jugo de mango")).toBe(true);
    expect(screen.queryByRole("form", { name: "Nuevo producto" })).not.toBeInTheDocument();
  });

  it("abrirlo sin escribir no cuenta como un cambio", async () => {
    const { user } = await renderWorkspace("/productos");
    await user.click(screen.getByRole("button", { name: "Agregar producto" }));
    expect(screen.queryByText("Cambios sin guardar")).not.toBeInTheDocument();
  });

  it("descartar los cambios también descarta el borrador", async () => {
    const { user } = await renderWorkspace("/productos");
    await user.click(screen.getByRole("button", { name: "Agregar producto" }));
    await user.type(within(screen.getByRole("form", { name: "Nuevo producto" })).getByLabelText(/^Nombre/), "Jugo de mango");
    await user.click(screen.getByRole("button", { name: "Descartar" }));
    await user.click(screen.getByRole("button", { name: "Sí, descartar" }));
    await screen.findByRole("heading", { level: 1, name: "Productos y servicios" });
    expect(screen.queryByRole("form", { name: "Nuevo producto" })).not.toBeInTheDocument();
    expect(screen.queryByText("Cambios sin guardar")).not.toBeInTheDocument();
  });
});

describe("Guardado", () => {
  it("no guarda hasta que se pide y solo entonces indica «Guardado»", async () => {
    const { user, backend } = await renderWorkspace("/negocio");
    const name = screen.getByLabelText(/Nombre comercial/);
    await user.clear(name);
    await user.type(name, "Guardado a petición");
    expect(screen.getByText("Cambios sin guardar")).toBeInTheDocument();
    expect(screen.queryByText(/^Guardado ·/)).not.toBeInTheDocument();
    expect(storedOf(backend).identity.name).toBe("Café Aroma");

    await saveAndWait(user);
    expect(storedOf(backend).identity.name).toBe("Guardado a petición");
    expect(screen.queryByText("Cambios sin guardar")).not.toBeInTheDocument();
  });

  it("los cambios siguen disponibles al pasar de una sección a otra", async () => {
    const { user } = await renderWorkspace("/negocio");
    await user.type(screen.getByLabelText(/Nombre comercial/), " Plus");
    await openTab(user, /^Cómo atiende/);
    expect(screen.getByRole("heading", { level: 1, name: "Cómo atiende el asistente" })).toBeInTheDocument();
    await openTab(user, /^Mi negocio/);
    expect(screen.getByLabelText(/Nombre comercial/)).toHaveValue("Café Aroma Plus");
  });

  it("si el guardado falla no muestra «Guardado», conserva lo escrito y permite reintentar", async () => {
    const { user, backend } = await renderWorkspace("/negocio");
    await user.type(screen.getByLabelText(/Nombre comercial/), " Plus");
    backend.failNext("save", new PersistenceError("unavailable"));
    await user.click(saveButton());

    expect(await screen.findByText("No se pudo guardar")).toBeInTheDocument();
    expect(screen.queryByText(/^Guardado ·/)).not.toBeInTheDocument();
    expect(screen.getAllByText(/No se pudo conectar con el servidor/).length).toBeGreaterThan(0);
    expect(screen.getByLabelText(/Nombre comercial/)).toHaveValue("Café Aroma Plus");
    expect(storedOf(backend).identity.name).toBe("Café Aroma");

    await user.click(screen.getByRole("button", { name: "Reintentar" }));
    expect(await screen.findByText(/^Guardado ·/)).toBeInTheDocument();
    expect(storedOf(backend).identity.name).toBe("Café Aroma Plus");
  });

  it("muestra en su campo los errores que señala el servidor y permite ir a su sección", async () => {
    const { user, backend } = await renderWorkspace("/mensajes");
    await user.type(screen.getByLabelText(/^Mensaje/), " más");
    backend.failNext(
      "save",
      new PersistenceError("invalid", {
        message: "La configuración tiene datos por corregir.",
        problems: [
          { path: "messages.welcome.text", message: "El mensaje es demasiado largo." },
          { path: "identity.name", message: "El nombre no es válido." },
        ],
      }),
    );
    await user.click(saveButton());

    expect(await screen.findByText("La configuración tiene datos por corregir.")).toBeInTheDocument();
    expect(screen.getAllByText("El mensaje es demasiado largo.").length).toBeGreaterThan(0);
    expect(screen.getByLabelText(/^Mensaje/)).toHaveAttribute("aria-invalid", "true");

    await user.click(within(screen.getByText(/El nombre no es válido\./).closest("li")!).getByRole("link", { name: "Mi negocio" }));
    expect(screen.getByRole("heading", { level: 1, name: "Mi negocio" })).toBeInTheDocument();
    expect(screen.getByLabelText(/Nombre comercial/)).toHaveAttribute("aria-invalid", "true");

    // Al volver a editar se deja atrás el resultado del intento anterior.
    await user.type(screen.getByLabelText(/Nombre comercial/), " Plus");
    expect(screen.queryByText("La configuración tiene datos por corregir.")).not.toBeInTheDocument();
  });

  it("dice a qué campo se refiere cada error del servidor y no tapa el mensaje propio del campo", async () => {
    const document = structuredClone(SAMPLE_DOCUMENT);
    document.identity.description = "";
    const { user, backend } = await renderWorkspace("/negocio", [document]);
    await user.type(screen.getByLabelText(/^Marca/), "x");
    backend.failNext(
      "save",
      new PersistenceError("invalid", {
        message: "La configuración tiene datos por corregir.",
        problems: [
          { path: "identity.description", message: "No puede estar vacío." },
          { path: "identity.value_proposition", message: "No puede estar vacío." },
        ],
      }),
    );
    await user.click(saveButton());
    const summary = (await screen.findByText("La configuración tiene datos por corregir.")).closest("[role=alert]") as HTMLElement;
    expect(within(summary).getByText(/Descripción: No puede estar vacío\./)).toBeInTheDocument();
    expect(within(summary).getByText(/Propuesta de valor: No puede estar vacío\./)).toBeInTheDocument();
    // El campo con validación propia muestra el mensaje escrito para el negocio; el otro, el del servidor.
    expect(screen.getByText("Describe brevemente tu negocio.")).toBeInTheDocument();
    expect(screen.getByLabelText(/^Propuesta de valor/)).toHaveAttribute("aria-invalid", "true");
  });

  it("si el negocio cambió en otra pestaña no pisa esos cambios", async () => {
    const { user, backend } = await renderWorkspace("/negocio");
    const other = backend.createConfigRepository(SAMPLE_DOCUMENT.tenant_slug);
    const opened = await other.load();
    await other.save({ document: { ...opened.document!, identity: { ...opened.document!.identity, name: "Desde otra pestaña" } }, paymentValues: {}, baseVersion: opened.latestVersion });

    await user.type(screen.getByLabelText(/Nombre comercial/), " Plus");
    await user.click(saveButton());
    expect(await screen.findByText("No se pudo guardar")).toBeInTheDocument();
    expect(screen.getAllByText(/cambió desde que lo abriste/).length).toBeGreaterThan(0);
    expect(storedOf(backend).identity.name).toBe("Desde otra pestaña");
  });

  it("descartar vuelve a lo último guardado", async () => {
    const { user } = await renderWorkspace("/negocio");
    await user.type(screen.getByLabelText(/Nombre comercial/), " Plus");
    await user.click(screen.getByRole("button", { name: "Descartar" }));
    await user.click(screen.getByRole("button", { name: "Sí, descartar" }));
    expect(await screen.findByLabelText(/Nombre comercial/)).toHaveValue("Café Aroma");
    expect(screen.queryByText("Cambios sin guardar")).not.toBeInTheDocument();
  });

  it("al salir del negocio con cambios sin guardar pregunta qué hacer", async () => {
    const { user, backend } = await renderWorkspace("/negocio");
    await user.type(screen.getByLabelText(/Nombre comercial/), " Plus");

    await switchTo(user, "Crear negocio");
    expect(await screen.findByText("Tienes cambios sin guardar")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Seguir editando" }));
    expect(screen.queryByText("Tienes cambios sin guardar")).not.toBeInTheDocument();
    expect(screen.getByLabelText(/Nombre comercial/)).toHaveValue("Café Aroma Plus");

    await switchTo(user, "Crear negocio");
    await user.click(await screen.findByRole("button", { name: "Guardar y salir" }));
    expect(await screen.findByRole("heading", { level: 1, name: "Crea tu negocio" })).toBeInTheDocument();
    expect(storedOf(backend).identity.name).toBe("Café Aroma Plus");
  });

  it("salir sin guardar pierde los cambios, como se avisa", async () => {
    const { user, backend } = await renderWorkspace("/negocio");
    await user.type(screen.getByLabelText(/Nombre comercial/), " Plus");
    await switchTo(user, "Crear negocio");
    await user.click(await screen.findByRole("button", { name: "Salir sin guardar" }));
    expect(await screen.findByRole("heading", { level: 1, name: "Crea tu negocio" })).toBeInTheDocument();
    expect(storedOf(backend).identity.name).toBe("Café Aroma");
  });

  it("avisa al cerrar la pestaña solo si hay cambios sin guardar", async () => {
    const { user } = await renderWorkspace("/negocio");
    const leave = () => {
      const event = new Event("beforeunload", { cancelable: true });
      window.dispatchEvent(event);
      return event.defaultPrevented;
    };
    expect(leave()).toBe(false);
    await user.type(screen.getByLabelText(/Nombre comercial/), " Plus");
    expect(leave()).toBe(true);
    await saveAndWait(user);
    expect(leave()).toBe(false);
  });

  it("conserva al guardar lo que no tiene campo en pantalla", async () => {
    const document = structuredClone(SAMPLE_DOCUMENT);
    document.sales.objections = [{ topic: "precio", acknowledge: ["Entiendo"], reframe: ["Vale la pena"] }];
    document.fulfillment = { delivery: { available: true, zones: ["Centro"] } } as BusinessDocument["fulfillment"];
    const { user, backend } = await renderWorkspace("/negocio", [document]);
    const before = storedOf(backend);
    await user.type(screen.getByLabelText(/Nombre comercial/), " Plus");
    await saveAndWait(user);

    const after = storedOf(backend);
    expect(after.identity.name).toBe("Café Aroma Plus");
    expect({ ...after, identity: before.identity }).toEqual(before);
  });

  it("no usa el almacenamiento del navegador para nada", async () => {
    const { user } = await renderWorkspace("/negocio");
    await user.type(screen.getByLabelText(/Nombre comercial/), " Plus");
    await saveAndWait(user);
    expect(window.localStorage.length).toBe(0);
    expect(window.sessionStorage.length).toBe(0);
  });
});

/** La tarjeta de opciones avanzadas con ese título (plegable: su contenido está en la página aunque esté cerrada). */
function advancedCard(title: string): HTMLElement {
  return screen.getByRole("heading", { name: new RegExp(`^${title}`) }).closest("details") as HTMLElement;
}

describe("Formularios generados desde el contrato", () => {
  it("edita un objeto del contrato sin pantalla propia", async () => {
    const { user, backend } = await renderWorkspace("/productos");
    const delivery = advancedCard("Domicilio");
    await user.click(within(delivery).getByRole("button", { name: "Configurar" }));
    await user.click(within(delivery).getByRole("switch", { name: /^Disponible/ }));
    await user.type(within(delivery).getByLabelText("Zonas"), "Centro{Enter}");
    await saveAndWait(user);
    expect(storedOf(backend).fulfillment?.delivery).toMatchObject({ available: true, zones: ["Centro"] });
  });

  it("agrega y quita elementos de una lista del contrato, con sus opciones cerradas", async () => {
    const { user, backend } = await renderWorkspace("/atencion");
    const objections = advancedCard("Cuando el cliente duda");
    await user.click(within(objections).getByRole("button", { name: "Agregar" }));
    await user.selectOptions(within(objections).getByLabelText(/^Cuando el cliente duda por/), "price");
    await saveAndWait(user);
    expect(storedOf(backend).sales.objections?.[0]).toMatchObject({ topic: "price" });

    await user.selectOptions(screen.getByLabelText(/^Tipo de negocio/), "saas");
    await saveAndWait(user);
    expect(storedOf(backend).features?.business_model).toBe("saas");

    const objection = screen.getByRole("heading", { name: "Objeciones: el precio" }).closest(".subcard") as HTMLElement;
    await user.click(within(objection).getByRole("button", { name: "Quitar" }));
    await user.click(within(objection).getByRole("button", { name: "Sí, quitar" }));
    await saveAndWait(user);
    expect(storedOf(backend).sales.objections ?? []).toEqual([]);
  });

  it("señala en el campo generado el error que devuelve el servidor", async () => {
    const { user, backend } = await renderWorkspace("/atencion");
    await user.click(within(advancedCard("Cuando el cliente duda")).getByRole("button", { name: "Agregar" }));
    backend.failNext("save", new PersistenceError("invalid", { message: "Hay datos por corregir.", problems: [{ path: "sales.objections.0.topic", message: "Escribe la objeción." }] }));
    await user.click(saveButton());
    expect(await screen.findByLabelText(/^Cuando el cliente duda por/)).toHaveAttribute("aria-invalid", "true");
    expect(screen.getAllByText("Escribe la objeción.").length).toBeGreaterThan(0);
  });

  it("si no puede leer el contrato lo informa en vez de abrir un formulario incompleto", async () => {
    const backend = createMemoryBackend([SAMPLE_DOCUMENT]);
    backend.failNext("contractSchema", new PersistenceError("unavailable"));
    const user = await renderAt(CAFE, createTestServices(backend));
    expect(screen.getByRole("heading", { level: 1, name: "No se pudo cargar tu configuración" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Reintentar" }));
    expect(await screen.findByRole("heading", { level: 1, name: "Café Aroma" })).toBeInTheDocument();
  });
});

describe("Revisión y publicación", () => {
  it("resume lo configurado y avisa que lo publicado es lo que responde el asistente", async () => {
    await renderWorkspace("/revision");
    expect(screen.getByText("Todos los datos obligatorios están completos")).toBeInTheDocument();
    expect(screen.getByText("Esto es lo que responde el asistente")).toBeInTheDocument();
    expect(screen.getByText("Café Aroma", { selector: "dd" })).toBeInTheDocument();
    await publishButton(1);
  });

  it("lista lo que falta y lo enlaza con su sección", async () => {
    const document = structuredClone(SAMPLE_DOCUMENT);
    document.identity.name = "";
    const { user } = await renderWorkspace("/revision", [document]);
    expect(screen.getByText(/Falta 1 dato obligatorio/)).toBeInTheDocument();
    await user.click(within(screen.getByText(/Escribe el nombre comercial de tu negocio\./).closest("li")!).getByRole("link", { name: "Mi negocio" }));
    expect(screen.getByRole("heading", { level: 1, name: "Mi negocio" })).toBeInTheDocument();
  });

  it("publica la versión guardada, muestra el historial y permite volver atrás", async () => {
    const { user, backend } = await renderWorkspace("/revision");
    await user.click(await publishButton(1));
    expect(await screen.findByText("Se publicó la versión 1.")).toBeInTheDocument();
    expect(await screen.findByRole("button", { name: "Esta versión ya está publicada" })).toBeDisabled();

    await openTab(user, /^Mi negocio/);
    await user.type(screen.getByLabelText(/Nombre comercial/), " Dos");
    await saveAndWait(user);
    await openTab(user, /^Publicar/);
    await user.click(await publishButton(2));
    expect(await screen.findByText("Se publicó la versión 2.")).toBeInTheDocument();

    const history = await screen.findByRole("list", { name: "Historial de versiones" });
    await waitFor(() => expect(within(history).getAllByRole("listitem")).toHaveLength(2));

    await user.click(screen.getByRole("button", { name: "Volver a la versión publicada anterior" }));
    await user.click(screen.getByRole("button", { name: "Sí, volver" }));
    expect(await screen.findByText("Se volvió a publicar la versión anterior.")).toBeInTheDocument();
    expect(storedOf(backend).identity.name).toBe("Café Aroma Dos");
    expect(await screen.findByText("Café Aroma", { selector: "dd" })).toBeInTheDocument();
  });

  it("restaurar crea un borrador con el contenido anterior sin publicar", async () => {
    const { user, backend } = await renderWorkspace("/negocio");
    await user.type(screen.getByLabelText(/Nombre comercial/), " Dos");
    await saveAndWait(user);
    await openTab(user, /^Publicar/);

    const history = await screen.findByRole("list", { name: "Historial de versiones" });
    const first = (await within(history).findByText(/^Versión 1/)).closest("li")!;
    await user.click(within(first).getByRole("button", { name: "Restaurar" }));
    await user.click(within(first).getByRole("button", { name: "Sí, restaurar" }));
    expect(await screen.findByText("Se creó un borrador con el contenido de la versión 1.")).toBeInTheDocument();
    expect(storedOf(backend).identity.name).toBe("Café Aroma");
    expect(await screen.findByText("Café Aroma", { selector: "dd" })).toBeInTheDocument();
  });

  it("no deja publicar con cambios sin guardar", async () => {
    const { user } = await renderWorkspace("/negocio");
    await user.type(screen.getByLabelText(/Nombre comercial/), " Dos");
    await openTab(user, /^Publicar/);
    expect(screen.getByText("Tienes cambios sin guardar: guárdalos para poder publicarlos.")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /^Publicar versión/ })).not.toBeInTheDocument();
  });

  it("muestra por qué no se puede publicar y los avisos del servidor", async () => {
    const backend = createMemoryBackend([SAMPLE_DOCUMENT]);
    backend.review.compileError = "Falta el dato de pago del enlace.";
    backend.review.diagnostics = [{ code: "faq_vacia", kind: "aviso", path: "knowledge", message: "Conviene agregar preguntas frecuentes." }];
    await renderAt(`${CAFE}/revision`, createTestServices(backend));
    expect(await screen.findByText("Esta versión todavía no se puede publicar")).toBeInTheDocument();
    expect(screen.getByText("Falta el dato de pago del enlace.")).toBeInTheDocument();
    expect(screen.getByText("Conviene agregar preguntas frecuentes.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Publicar versión 1" })).toBeDisabled();
  });

  it("si la publicación falla lo informa y lo publicado no cambia", async () => {
    const backend = createMemoryBackend([SAMPLE_DOCUMENT]);
    const user = await renderAt(`${CAFE}/revision`, createTestServices(backend));
    backend.failNext("publish", new PersistenceError("conflict", { message: "No se puede publicar: falta un dato de pago." }));
    await user.click(await publishButton(1));
    expect(await screen.findByText("No se puede publicar: falta un dato de pago.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Publicar versión 1" })).toBeEnabled();
  });
});

describe("Canales: WhatsApp por código QR", () => {
  async function renderChannels(options: { available?: boolean } = {}) {
    const whatsapp = createMemoryWhatsApp(options);
    const user = await renderAt(`${CAFE}/canales`, createTestServices(createMemoryBackend([SAMPLE_DOCUMENT]), { createChannels: () => whatsapp.channels }));
    await screen.findByRole("heading", { name: /^WhatsApp/ });
    return { user, whatsapp };
  }

  it("ofrece el código QR, deja la API oficial para después y ya no muestra Instagram", async () => {
    await renderChannels();
    expect(screen.getByRole("radio", { name: /^Código QR/ })).toBeChecked();
    expect(screen.getByRole("radio", { name: /^API oficial de Meta/ })).toBeDisabled();
    expect(screen.queryByText("Instagram")).not.toBeInTheDocument();
    expect(screen.getByText("Telegram")).toBeInTheDocument();
  });

  it("el negocio no ve servidores ni tokens: solo conecta, escanea y queda conectado", async () => {
    const { user, whatsapp } = await renderChannels();
    expect(await screen.findByRole("button", { name: /Conectar WhatsApp/ })).toBeEnabled();
    expect(screen.queryByLabelText(/Token/)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/Servidor/)).not.toBeInTheDocument();
    expect(screen.queryByText(/uazapi/)).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /Conectar WhatsApp/ }));
    expect(await screen.findByRole("img", { name: "Código QR para vincular WhatsApp" })).toBeInTheDocument();
    expect(screen.getByText("Esperando el escaneo")).toBeInTheDocument();

    whatsapp.scan();
    expect(await screen.findByText(/Conectado al \+573001112233/, {}, { timeout: 4500 })).toBeInTheDocument();
    expect(screen.queryByRole("img", { name: "Código QR para vincular WhatsApp" })).not.toBeInTheDocument();
  }, 10000);

  it("si la plataforma todavía no activó la conexión, lo dice sin detalles técnicos", async () => {
    await renderChannels({ available: false });
    expect(await screen.findByText(/todavía no está activa/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Conectar WhatsApp/ })).not.toBeInTheDocument();
  });
});

describe("Celular", () => {
  /** Simula una pantalla de celular: el panel usa `matchMedia` para saber si muestra la barra superior con ☰. */
  function onAPhone() {
    const original = window.matchMedia;
    window.matchMedia = ((query: string) => ({
      matches: true,
      media: query,
      onchange: null,
      addEventListener: () => undefined,
      removeEventListener: () => undefined,
      addListener: () => undefined,
      removeListener: () => undefined,
      dispatchEvent: () => false,
    })) as typeof window.matchMedia;
    return () => {
      window.matchMedia = original;
    };
  }

  it("el menú ☰ se abre como un panel, bloquea la página de atrás y se cierra con la X, con Escape o al elegir una opción", async () => {
    const restore = onAPhone();
    try {
      const { user } = await renderWorkspace("");
      const menu = screen.getByRole("dialog", { name: "Menú principal" });
      const hamburger = screen.getByRole("button", { name: "Abrir menú" });
      expect(menu).not.toHaveClass("sidebar--open");
      // La barra superior dice dónde estás y de qué negocio, y tiene los avisos a mano.
      const bar = hamburger.closest("header") as HTMLElement;
      expect(within(bar).getByText("Inicio")).toBeInTheDocument();
      expect(within(bar).getByText(SAMPLE_DOCUMENT.identity.name)).toBeInTheDocument();
      expect(within(bar).getByRole("button", { name: /Avisos|Notificaciones/ })).toBeInTheDocument();

      await user.click(hamburger);
      expect(menu).toHaveClass("sidebar--open");
      expect(hamburger).toHaveAttribute("aria-expanded", "true");
      expect(document.documentElement.style.overflow).toBe("hidden");
      expect(menu).toContainElement(document.activeElement as HTMLElement);

      await user.click(within(menu).getByRole("button", { name: "Cerrar menú" }));
      expect(menu).not.toHaveClass("sidebar--open");
      expect(document.documentElement.style.overflow).toBe("");
      expect(screen.getByRole("button", { name: "Abrir menú" })).toHaveFocus();

      await user.click(screen.getByRole("button", { name: "Abrir menú" }));
      await user.keyboard("{Escape}");
      expect(menu).not.toHaveClass("sidebar--open");

      await user.click(screen.getByRole("button", { name: "Abrir menú" }));
      await user.click(within(sidebarNav()).getByRole("link", { name: "Clientes" }));
      expect(menu).not.toHaveClass("sidebar--open");
      expect(within(bar).getByText("Clientes")).toBeInTheDocument();
    } finally {
      restore();
    }
  });
});
