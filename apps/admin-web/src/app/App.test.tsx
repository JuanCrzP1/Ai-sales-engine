import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { AssistantConfig } from "../domain/config/types";
import { configStorageKey, createLocalConfigRepository } from "../infrastructure/local/localConfigRepository";
import { createTestServices, createVerifyingAuthService, flakyConfigRepository, signedInServices, TEST_ACCOUNT } from "../test/fakes";
import { SAMPLE_CONFIG } from "../test/fixtures/sampleConfig";
import { App } from "./App";
import type { ApplicationServices } from "./compositionRoot";

const LOADING = /Abriendo tu panel…|Cargando tu configuración…/;

/** Renderiza la app en una ruta y espera a que terminen la carga de sesión y de configuración. */
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

/** Sesión iniciada y, opcionalmente, una configuración ya guardada en la cuenta. */
async function renderSignedIn(path: string, config: AssistantConfig | null = SAMPLE_CONFIG, overrides: Partial<ApplicationServices> = {}) {
  const { services, session } = await signedInServices(overrides);
  if (config) await createLocalConfigRepository(session.user.id).save(config);
  return { user: await renderAt(path, services), session };
}

const storedConfig = (accountId: string) => JSON.parse(window.localStorage.getItem(configStorageKey(accountId)) ?? "{}");
const sidebarNav = () => screen.getByRole("navigation", { name: "Secciones de configuración" });
const userMenuButton = (name = TEST_ACCOUNT.name) => screen.getByRole("button", { name: `Cuenta de ${name}` });

describe("Cuenta y sesión (acceso local sin verificación)", () => {
  it("muestra una pantalla de carga mientras recupera la sesión", () => {
    render(<App services={createTestServices()} />);
    expect(screen.getByText("Abriendo tu panel…")).toBeInTheDocument();
  });

  it("sin sesión envía a la entrada, que avisa que el acceso no está verificado", async () => {
    await renderAt("/productos", createTestServices());
    expect(screen.getByRole("heading", { level: 1, name: "Bienvenido de nuevo" })).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "AI Sales Engine" })).toBeInTheDocument();
    expect(screen.getByRole("note")).toHaveTextContent("Acceso local sin verificación");
    expect(screen.queryByLabelText(/^Contraseña/)).not.toBeInTheDocument();
  });

  it("crea una cuenta nueva sin contraseña que empieza con la configuración vacía", async () => {
    const user = await renderAt("/", createTestServices());
    await user.click(screen.getByRole("link", { name: "Crear cuenta" }));
    expect(screen.getByRole("note")).toHaveTextContent("Acceso local sin verificación");
    expect(screen.queryByLabelText(/^Contraseña/)).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Crear cuenta" }));
    expect(screen.getByText("Escribe tu nombre.")).toBeInTheDocument();

    await user.type(screen.getByLabelText(/^Tu nombre/), TEST_ACCOUNT.name);
    await user.type(screen.getByLabelText(/^Correo electrónico/), TEST_ACCOUNT.email);
    await user.click(screen.getByRole("button", { name: "Crear cuenta" }));

    expect(await screen.findByRole("heading", { level: 1, name: "Configura tu asistente de ventas" })).toBeInTheDocument();
    expect(screen.getByText("Hola, Laura")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Tu negocio" })).toBeInTheDocument();
    expect(screen.queryByText(/\b(demo|demostración|prueba|prototipo)\b/i)).not.toBeInTheDocument();
  });

  it("entra con solo el correo y vuelve a la página que se quería abrir", async () => {
    const services = createTestServices();
    await services.auth.signUp(TEST_ACCOUNT);
    await services.auth.signOut();
    const user = await renderAt("/productos", services);

    await user.click(screen.getByRole("button", { name: "Entrar" }));
    expect(screen.getByText("Escribe tu correo electrónico.")).toBeInTheDocument();

    await user.type(screen.getByLabelText(/^Correo electrónico/), TEST_ACCOUNT.email);
    await user.click(screen.getByRole("button", { name: "Entrar" }));
    expect(await screen.findByRole("heading", { level: 1, name: "Productos y servicios" })).toBeInTheDocument();
  });

  it("un correo nuevo crea su cuenta al entrar", async () => {
    const user = await renderAt("/", createTestServices());
    await user.type(screen.getByLabelText(/^Correo electrónico/), "ana.perez@tienda.co");
    await user.click(screen.getByRole("button", { name: "Entrar" }));
    expect(await screen.findByText("Hola, Ana")).toBeInTheDocument();
    expect(userMenuButton("Ana Perez")).toBeInTheDocument();
  });

  it("cierra sesión desde el menú de la cuenta", async () => {
    const { user } = await renderSignedIn("/");
    await user.click(userMenuButton());
    expect(screen.getByText(TEST_ACCOUNT.email)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Cerrar sesión" }));
    expect(await screen.findByRole("heading", { level: 1, name: "Bienvenido de nuevo" })).toBeInTheDocument();
  });

  it("el menú de la cuenta se cierra con Escape y devuelve el foco al botón", async () => {
    const { user } = await renderSignedIn("/");
    await user.click(userMenuButton());
    expect(screen.getByRole("link", { name: "Mi perfil" })).toBeInTheDocument();
    await user.keyboard("{Escape}");
    expect(screen.queryByRole("link", { name: "Mi perfil" })).not.toBeInTheDocument();
    expect(userMenuButton()).toHaveFocus();
  });

  it("edita el perfil y valida la foto", async () => {
    const { user } = await renderSignedIn("/");
    await user.click(userMenuButton());
    await user.click(screen.getByRole("link", { name: "Mi perfil" }));
    expect(screen.getByRole("heading", { level: 1, name: "Mi perfil" })).toBeInTheDocument();

    const name = screen.getByLabelText(/^Nombre/);
    await user.clear(name);
    await user.type(name, "Laura Ruiz");
    await user.click(screen.getByRole("button", { name: "Guardar cambios" }));
    expect(await screen.findByText("Tus datos se guardaron.")).toBeInTheDocument();
    expect(userMenuButton("Laura Ruiz")).toBeInTheDocument();

    await user.upload(screen.getByLabelText("Cambiar foto"), new File(["texto"], "notas.txt", { type: "text/plain" }));
    expect(await screen.findByText("Usa una imagen JPG, PNG, WebP o GIF.")).toBeInTheDocument();
  });

  it("informa datos de cuentas dañados al entrar, sin sobrescribirlos", async () => {
    window.localStorage.setItem("ai-sales-engine.admin-web.open-accounts.v1", "{no es json");
    const user = await renderAt("/", createTestServices());
    await user.type(screen.getByLabelText(/^Correo electrónico/), TEST_ACCOUNT.email);
    await user.click(screen.getByRole("button", { name: "Entrar" }));
    expect(await screen.findByText(/están dañados/)).toBeInTheDocument();
    expect(window.localStorage.getItem("ai-sales-engine.admin-web.open-accounts.v1")).toBe("{no es json");
  });

  it("si la sesión apunta a cuentas dañadas, muestra un error en vez de abrir el panel", async () => {
    window.localStorage.setItem("ai-sales-engine.admin-web.open-session.v1", JSON.stringify({ userId: "x", startedAt: "2026-01-01" }));
    window.localStorage.setItem("ai-sales-engine.admin-web.open-accounts.v1", "{no es json");
    await renderAt("/", createTestServices());
    expect(screen.getByRole("heading", { level: 1, name: "No se pudo abrir tu sesión" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reintentar" })).toBeInTheDocument();
  });
});

describe("Cuenta y sesión (servicio que verifica credenciales)", () => {
  it("pide contraseña, rechaza credenciales incorrectas y no muestra el aviso de acceso local", async () => {
    const auth = createVerifyingAuthService();
    await auth.signUp({ ...TEST_ACCOUNT });
    await auth.signOut();
    const user = await renderAt("/", createTestServices({ auth }));

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
    expect(await screen.findByText("Hola, Laura")).toBeInTheDocument();
  });

  it("muestra la contraseña al pedirlo", async () => {
    const user = await renderAt("/iniciar-sesion", createTestServices({ auth: createVerifyingAuthService() }));
    const password = screen.getByLabelText(/^Contraseña/);
    expect(password).toHaveAttribute("type", "password");
    await user.click(screen.getByRole("button", { name: "Mostrar contraseña" }));
    expect(password).toHaveAttribute("type", "text");
  });

  it("al crear cuenta exige contraseña segura y su confirmación", async () => {
    const user = await renderAt("/crear-cuenta", createTestServices({ auth: createVerifyingAuthService() }));
    await user.type(screen.getByLabelText(/^Tu nombre/), TEST_ACCOUNT.name);
    await user.type(screen.getByLabelText(/^Correo electrónico/), TEST_ACCOUNT.email);
    await user.type(screen.getByLabelText(/^Contraseña/), "corta");
    await user.click(screen.getByRole("button", { name: "Crear cuenta" }));
    expect(screen.getByText(/al menos 8 caracteres/)).toBeInTheDocument();
    expect(screen.getByText("Las contraseñas no coinciden.")).toBeInTheDocument();
  });
});

describe("Panel de configuración", () => {
  it("muestra el inicio con el resumen sin afirmar que está conectado", async () => {
    await renderSignedIn("/");
    expect(screen.getByRole("heading", { level: 1, name: "Configura tu asistente de ventas" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Café Aroma" })).toBeInTheDocument();
    expect(screen.getAllByText("Sin conectar").length).toBeGreaterThan(0);
    expect(screen.queryByText(/desplegado|en producción|conectado al asistente real\./i)).not.toBeInTheDocument();
  });

  it("navega entre todas las secciones desde el menú lateral", async () => {
    const { user } = await renderSignedIn("/");
    const expectations: [string, string, string][] = [
      ["Mi negocio", "Mi negocio", "Paso 1"],
      ["Productos y servicios", "Productos y servicios", "Paso 2"],
      ["Pagos y cierre", "Pagos y cierre de ventas", "Paso 3"],
      ["Cómo atiende", "Cómo atiende el asistente", "Paso 4"],
      ["Mensajes y canales", "Mensajes y canales", "Paso 5"],
      ["Revisión", "Revisión de la configuración", "Último paso"],
    ];
    for (const [link, heading, step] of expectations) {
      await user.click(within(sidebarNav()).getByRole("link", { name: new RegExp(`^${link}`) }));
      expect(screen.getByRole("heading", { level: 1, name: heading })).toBeInTheDocument();
      expect(screen.getByText(step)).toBeInTheDocument();
    }
  });

  it("valida y actualiza los datos del negocio", async () => {
    const { user } = await renderSignedIn("/negocio");
    const name = screen.getByLabelText(/Nombre comercial/);
    await user.clear(name);
    expect(screen.getByText("Escribe el nombre comercial de tu negocio.")).toBeInTheDocument();
    expect(name).toHaveAttribute("aria-invalid", "true");

    await user.type(name, "Panadería Central");
    expect(screen.queryByText("Escribe el nombre comercial de tu negocio.")).not.toBeInTheDocument();
    expect(screen.getByText("Panadería Central", { selector: ".sidebar__brand-sub" })).toBeInTheDocument();
  });

  it("agrega, valida, edita y elimina productos del catálogo", async () => {
    const { user } = await renderSignedIn("/productos");
    const list = () => screen.getByRole("list", { name: "Productos y servicios" });
    expect(within(list()).getAllByRole("listitem")).toHaveLength(3);

    await user.click(screen.getAllByRole("button", { name: "Agregar producto" })[0]!);
    await user.click(screen.getByRole("button", { name: "Guardar producto" }));
    expect(screen.getByText("Cada producto o servicio necesita un nombre.")).toBeInTheDocument();

    await user.type(screen.getByLabelText(/^Nombre/), "Jugo de naranja");
    await user.type(screen.getByLabelText(/^Categoría/), "Bebidas");
    await user.type(screen.getByLabelText(/^Precio/), "7000");
    await user.click(screen.getByRole("button", { name: "Guardar producto" }));
    expect(within(list()).getAllByRole("listitem")).toHaveLength(4);
    expect(within(list()).getByText("Jugo de naranja")).toBeInTheDocument();

    await user.click(within(list()).getByRole("button", { name: "Editar Jugo de naranja" }));
    const nameInput = screen.getByLabelText(/^Nombre/);
    await user.clear(nameInput);
    await user.type(nameInput, "Jugo natural");
    await user.click(screen.getByRole("button", { name: "Guardar cambios" }));
    expect(within(list()).getByText("Jugo natural")).toBeInTheDocument();

    const row = within(list()).getByText("Jugo natural").closest("li")!;
    await user.click(within(row).getByRole("button", { name: "Pausar" }));
    expect(within(row).getByText("No disponible")).toBeInTheDocument();
    await user.click(within(row).getByRole("button", { name: "Eliminar" }));
    await user.click(within(row).getByRole("button", { name: "Sí, eliminar" }));
    expect(within(list()).getAllByRole("listitem")).toHaveLength(3);
  });

  it("detecta configuraciones de pago incompletas", async () => {
    const { user } = await renderSignedIn("/pagos");
    const link = screen.getByLabelText(/^Enlace de pago/);
    await user.clear(link);
    await user.type(link, "pagos-sin-protocolo");
    expect(screen.getByText("El enlace debe ser una dirección web válida (https://…).")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Agregar cuenta" }));
    expect(screen.getAllByText("Escribe un celular de 10 dígitos que empiece por 3.").length).toBeGreaterThan(0);
  });

  it("al cambiar el tipo de una cuenta borra los datos del tipo anterior", async () => {
    const { user, session } = await renderSignedIn("/pagos");
    const account = screen.getByRole("group", { name: "Cuenta 1" });
    expect(within(account).getByLabelText(/^Número de celular/)).toHaveValue("3000000000");

    await user.selectOptions(within(account).getByLabelText("Tipo"), "bank");
    expect(within(account).queryByLabelText(/^Número de celular/)).not.toBeInTheDocument();
    await waitFor(() => expect(storedConfig(session.user.id).config.payments.transferMethods[0]).toMatchObject({ type: "bank", phoneNumber: "" }));
  });

  it("muestra la vista previa del mensaje de bienvenida", async () => {
    const { user } = await renderSignedIn("/mensajes");
    const welcome = screen.getByLabelText(/^Mensaje/);
    await user.clear(welcome);
    await user.type(welcome, "Hola, soy tu asistente");
    const preview = screen.getAllByRole("figure", { name: "Vista previa de la conversación" })[0]!;
    expect(within(preview).getByText("Hola, soy tu asistente")).toBeInTheDocument();
  });

  it("las listas editables nombran la lista en sus botones de quitar", async () => {
    const { user } = await renderSignedIn("/pagos");
    await user.click(screen.getByRole("button", { name: "Quitar de Condiciones: elemento 1" }));
    expect(screen.queryByRole("button", { name: "Quitar de Condiciones: elemento 1" })).not.toBeInTheDocument();
  });

  it("borrar la configuración deja la revisión con los pendientes, sin afirmar que está publicada", async () => {
    const { user } = await renderSignedIn("/perfil");
    await user.click(screen.getByRole("button", { name: "Borrar configuración del asistente" }));
    await user.click(screen.getByRole("button", { name: "Sí, borrar todo" }));
    await user.click(within(sidebarNav()).getByRole("link", { name: /^Revisión/ }));

    expect(screen.getByText("Configuración sin publicar")).toBeInTheDocument();
    expect(screen.getByText(/Faltan \d+ datos obligatorios/)).toBeInTheDocument();
    expect(screen.getAllByText(/Escribe el nombre comercial de tu negocio\./).length).toBeGreaterThan(0);
  });
});

describe("Guardado y carga de la configuración", () => {
  it("guarda los cambios en la cuenta activa y solo entonces indica «Guardado»", async () => {
    const { user, session } = await renderSignedIn("/negocio");
    expect(screen.queryByText("No se pudo guardar")).not.toBeInTheDocument();
    const name = screen.getByLabelText(/Nombre comercial/);
    await user.clear(name);
    await user.type(name, "Guardado en la cuenta");
    await waitFor(() => expect(storedConfig(session.user.id).config.business.name).toBe("Guardado en la cuenta"));
    expect(await screen.findByText(/^Guardado ·/)).toBeInTheDocument();
  });

  it("si el guardado falla no muestra «Guardado», lo informa y permite reintentar", async () => {
    const failing = { current: true };
    const { user, session } = await renderSignedIn("/negocio", SAMPLE_CONFIG, {
      createConfigRepository: (accountId) => flakyConfigRepository(createLocalConfigRepository(accountId), failing),
    });
    await user.type(screen.getByLabelText(/Nombre comercial/), " Plus");

    expect(await screen.findByText("No se pudo guardar")).toBeInTheDocument();
    expect(screen.queryByText(/^Guardado ·/)).not.toBeInTheDocument();
    expect(screen.getByText("El almacenamiento de este navegador está lleno.")).toBeInTheDocument();
    expect(storedConfig(session.user.id).config.business.name).toBe("Café Aroma");

    failing.current = false;
    await user.click(screen.getByRole("button", { name: "Reintentar" }));
    expect(await screen.findByText(/^Guardado ·/)).toBeInTheDocument();
    expect(storedConfig(session.user.id).config.business.name).toBe("Café Aroma Plus");
  });

  it("si la configuración guardada está dañada, lo informa sin sobrescribirla", async () => {
    const { services, session } = await signedInServices();
    window.localStorage.setItem(configStorageKey(session.user.id), "{dañado");
    const user = await renderAt("/", services);

    expect(screen.getByRole("heading", { level: 1, name: "No se pudo cargar tu configuración" })).toBeInTheDocument();
    expect(screen.getByText(/están dañados.*No se ha borrado nada/)).toBeInTheDocument();
    expect(window.localStorage.getItem(configStorageKey(session.user.id))).toBe("{dañado");

    await user.click(screen.getByRole("button", { name: "Descartar lo guardado" }));
    await user.click(screen.getByRole("button", { name: "Sí, descartar y empezar de cero" }));
    expect(await screen.findByRole("heading", { level: 1, name: "Configura tu asistente de ventas" })).toBeInTheDocument();
  });
});
