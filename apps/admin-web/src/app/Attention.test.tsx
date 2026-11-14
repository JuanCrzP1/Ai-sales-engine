import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it } from "vitest";
import { effectiveHours, hoursText, waitNotice, waitText } from "../domain/attention/types";
import type { ConversationThread, Notification } from "../domain/inbox/types";
import { applicationServerKey, deviceLabel } from "../infrastructure/browser/browserPush";
import { createMemoryAttention, createMemoryBackend, createMemoryDevicePush, createMemoryInbox, createTestServices } from "../test/fakes";
import { SAMPLE_DOCUMENT } from "../test/fixtures/sampleDocument";
import { App } from "./App";

afterEach(cleanup);

const CAFE = SAMPLE_DOCUMENT.tenant_slug;
const ago = (minutes: number) => new Date(Date.now() - minutes * 60_000).toISOString();

async function openAttention(options: { attention?: ReturnType<typeof createMemoryAttention>; push?: ReturnType<typeof createMemoryDevicePush> } = {}) {
  window.history.pushState({}, "", `/negocios/${CAFE}/configuracion/atencion-humana`);
  const user = userEvent.setup();
  const attention = options.attention ?? createMemoryAttention();
  const push = options.push ?? createMemoryDevicePush();
  render(<App services={createTestServices(createMemoryBackend([SAMPLE_DOCUMENT]), { createAttention: () => attention, devicePush: push })} />);
  await screen.findByRole("heading", { level: 1, name: "Atención humana" });
  return { user, attention, push };
}

describe("Configuración → Atención humana", () => {
  it("vive en Configuración junto a la inteligencia artificial y dice si hay alguien ahora", async () => {
    await openAttention();
    const tabs = screen.getByRole("navigation", { name: "Configuración" });
    expect(within(tabs).getByRole("link", { name: /Inteligencia artificial/ })).toBeInTheDocument();
    expect(within(tabs).getByRole("link", { name: /Atención humana/ })).toHaveAttribute("aria-current", "page");
    expect(screen.getByText("Ahora hay alguien de tu equipo")).toBeInTheDocument();
    expect(screen.getByText("De lunes a viernes de 8:00 a. m. a 6:00 p. m.")).toBeInTheDocument();
  });

  it("guarda un horario propio del equipo con sus días y horas", async () => {
    const { user, attention } = await openAttention();
    await user.click(screen.getByRole("radio", { name: /Otro horario para el equipo/ }));
    // Empieza con el horario del negocio para no partir de cero; se le quita el viernes y se agrega el sábado.
    await user.click(screen.getByRole("button", { name: "Viernes" }));
    await user.click(screen.getByRole("button", { name: "Sábado" }));
    await user.click(screen.getByRole("button", { name: "Guardar" }));

    expect(await screen.findByText("Guardado. Ya se aplica en tus chats.")).toBeInTheDocument();
    expect(attention.view.hoursMode).toBe("custom");
    expect(attention.view.teamHours).toEqual([{ days: ["lunes", "martes", "miercoles", "jueves", "sabado"], opens: "08:00", closes: "18:00" }]);
  });

  it("muestra el problema del servidor junto al horario", async () => {
    const { user } = await openAttention();
    await user.click(screen.getByRole("radio", { name: /Otro horario para el equipo/ }));
    await user.click(screen.getByRole("button", { name: "Quitar la franja 1" }));
    await user.click(screen.getByRole("button", { name: "Guardar" }));
    expect(await screen.findByText("Agrega al menos una franja, o elige otro horario.")).toBeInTheDocument();
    expect(screen.getByText("Revisa los campos marcados.")).toBeInTheDocument();
  });

  it("muestra lo que recibirá el cliente y guarda cuándo retoma la IA", async () => {
    const { user, attention } = await openAttention();
    expect(screen.getByText("Una persona de nuestro equipo te responderá en unos 10 minutos.")).toBeInTheDocument();
    await user.selectOptions(screen.getByLabelText("Le decimos que le responden en…"), "60");
    expect(screen.getByText("Una persona de nuestro equipo te responderá en una hora.")).toBeInTheDocument();
    await user.selectOptions(screen.getByLabelText("La IA retoma el chat si el cliente espera más de…"), "nunca");
    await user.click(screen.getByRole("button", { name: "Guardar" }));
    await screen.findByText("Guardado. Ya se aplica en tus chats.");
    expect([attention.view.replyMinutes, attention.view.resumeAfterMinutes]).toEqual([60, null]);
  });

  it("envía un correo de prueba y dice adónde llegó o por qué no", async () => {
    const { user, attention } = await openAttention();
    await user.click(screen.getByRole("button", { name: "Enviar correo de prueba" }));
    expect(await screen.findByText(/Te enviamos un correo de prueba a laura@empresa.com/)).toBeInTheDocument();
    attention.failEmail = true;
    await user.click(screen.getByRole("button", { name: "Enviar correo de prueba" }));
    expect(await screen.findByText("El correo de avisos aún no está activado en la plataforma.")).toBeInTheDocument();
  });

  it("es honesto si la plataforma todavía no tiene el correo activado", async () => {
    await openAttention({ attention: createMemoryAttention({ emailAvailable: false, teamAvailableNow: false, nextOpening: null }) });
    expect(screen.getByText("El correo de avisos aún no está activado en la plataforma.")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Enviar correo de prueba" })).not.toBeInTheDocument();
    expect(screen.getByText("Ahora estás fuera del horario")).toBeInTheDocument();
  });

  it("las notificaciones del celular se activan en Mi cuenta, porque son de cada persona", async () => {
    const { user } = await openAttention();
    await user.click(screen.getByRole("link", { name: "Activarlas en Mi cuenta" }));
    expect(await screen.findByRole("heading", { level: 1, name: "Notificaciones" })).toBeInTheDocument();
    expect(window.location.pathname).toBe(`/negocios/${CAFE}/cuenta/notificaciones`);
  });
});

async function openNotifications(push = createMemoryDevicePush()) {
  window.history.pushState({}, "", `/negocios/${CAFE}/cuenta/notificaciones`);
  const user = userEvent.setup();
  render(<App services={createTestServices(createMemoryBackend([SAMPLE_DOCUMENT]), { devicePush: push })} />);
  await screen.findByRole("heading", { level: 1, name: "Notificaciones" });
  return { user, push };
}

describe("Mi cuenta → Notificaciones", () => {
  it("activa, prueba y quita las notificaciones de este dispositivo", async () => {
    const { user, push } = await openNotifications();
    // Con el acceso local no hay perfil ni contraseña: Mi cuenta solo tiene las notificaciones.
    const nav = screen.getByRole("navigation", { name: "Mi cuenta" });
    expect(within(nav).getAllByRole("link").map((link) => link.textContent)).toEqual(["NotificacionesAvisos en tu celular y computador"]);
    await user.click(await screen.findByRole("button", { name: "Activar notificaciones" }));
    expect(await screen.findByText("Activadas en este dispositivo")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Enviar una prueba" }));
    await waitFor(() => expect(push.state.tests).toBe(1));
    await user.click(screen.getByRole("button", { name: "Desactivar aquí" }));
    expect(await screen.findByRole("button", { name: "Activar notificaciones" })).toBeInTheDocument();
    // Los correos son de cada negocio: se configuran en su Atención humana.
    expect(screen.getByRole("link", { name: "Configurar en Atención humana" })).toHaveAttribute("href", `/negocios/${CAFE}/configuracion/atencion-humana`);
  });

  it("explica qué hacer si el navegador las bloquea o si es un iPhone sin instalar el panel", async () => {
    const push = createMemoryDevicePush();
    push.state.denyNext = true;
    const { user } = await openNotifications(push);
    await user.click(await screen.findByRole("button", { name: "Activar notificaciones" }));
    expect(await screen.findByText("Bloqueaste las notificaciones para este sitio.")).toBeInTheDocument();
    cleanup();
    await openNotifications(createMemoryDevicePush({ support: "install" }));
    expect(screen.getByText("En iPhone y iPad, primero instala el panel")).toBeInTheDocument();
  });
});

describe("Configuración", () => {
  it("solo tiene lo del negocio (el asistente, la facturación y eliminarlo) y anuncia lo que viene", async () => {
    window.history.pushState({}, "", `/negocios/${CAFE}/configuracion`);
    const user = userEvent.setup();
    render(<App services={createTestServices(createMemoryBackend([SAMPLE_DOCUMENT]))} />);
    // Sin ruta concreta, abre la inteligencia artificial.
    await screen.findByRole("heading", { level: 1, name: "Inteligencia artificial" });
    const nav = screen.getByRole("navigation", { name: "Configuración" });
    // Lo personal (Mi perfil) no está aquí: es de Mi cuenta.
    expect(within(nav).queryByRole("link", { name: /Mi perfil/ })).not.toBeInTheDocument();
    expect(within(nav).getAllByRole("link").map((link) => link.textContent)).toEqual([
      "Inteligencia artificialProveedor, clave y modelo",
      "Atención humanaHorario del equipo y avisos",
      "Respuestas rápidasMensajes guardados para responder rápido",
      "Pagos y suscripcionesProntoTu plan, pagos y facturas",
      "Eliminar negocioBorrarlo con todo lo suyo",
    ]);
    await user.click(within(nav).getByRole("link", { name: /Respuestas rápidas/ }));
    expect(await screen.findByRole("heading", { level: 1, name: "Respuestas rápidas" })).toBeInTheDocument();
    expect(await screen.findByText("Responde en segundos, sin copiar y pegar")).toBeInTheDocument();
    // Cada sección se dibuja de nuevo al cambiar de ruta: el menú se vuelve a buscar.
    await user.click(within(screen.getByRole("navigation", { name: "Configuración" })).getByRole("link", { name: /Pagos y suscripciones/ }));
    expect(await screen.findByText("Hoy la plataforma no te cobra nada.")).toBeInTheDocument();
    expect(screen.getByText("Próximamente")).toBeInTheDocument();
    // No se confunde con la pestaña «Pagos» del Asistente IA.
    expect(screen.queryByRole("navigation", { name: "Asistente IA" })).not.toBeInTheDocument();
    expect(window.location.pathname).toBe(`/negocios/${CAFE}/configuracion/facturacion`);
  });
});

describe("Mensajes del asistente para la atención humana", () => {
  it("se escriben en Asistente IA → Mensajes y van al borrador", async () => {
    window.history.pushState({}, "", `/negocios/${CAFE}/mensajes`);
    const user = userEvent.setup();
    render(<App services={createTestServices(createMemoryBackend([SAMPLE_DOCUMENT]))} />);
    const afterHours = await screen.findByLabelText("Fuera del horario del equipo");
    await user.type(afterHours, "Te escribimos mañana a las 8.");
    expect(screen.getByLabelText("Cuando la IA retoma el chat")).toBeInTheDocument();
    expect(afterHours).toHaveValue("Te escribimos mañana a las 8.");
  });
});

describe("Avisos y chats", () => {
  const notification = (overrides: Partial<Notification>): Notification => ({
    id: "n1", business: { slug: CAFE, name: "Café Aroma" }, conversationId: "c1", kind: "handoff", title: "Laura pidió hablar con una persona",
    body: "Quiero hablar con alguien", createdAt: ago(3), read: false, ...overrides,
  });

  it("la campana ofrece activar las notificaciones y muestra cuando la IA retomó un chat", async () => {
    window.history.pushState({}, "", `/negocios/${CAFE}`);
    const user = userEvent.setup();
    const inbox = createMemoryInbox([], [
      notification({}),
      notification({ id: "n2", kind: "ai_resumed", title: "La IA retomó el chat con Pedro", body: "Nadie le respondió en 30 minutos." }),
    ]);
    const push = createMemoryDevicePush();
    render(<App services={createTestServices(createMemoryBackend([SAMPLE_DOCUMENT]), { inbox, devicePush: push })} />);
    await user.click(await screen.findByRole("button", { name: /Notificaciones: 2 sin leer/ }));
    const panel = screen.getByRole("dialog", { name: "Notificaciones" });
    expect(within(panel).getByText("«Quiero hablar con alguien»")).toBeInTheDocument();
    expect(within(panel).getByText("Nadie le respondió en 30 minutos.")).toBeInTheDocument();
    await user.click(within(panel).getByRole("button", { name: "Activar notificaciones" }));
    await waitFor(() => expect(push.state.subscribed).toBe(true));
    expect(within(panel).queryByRole("button", { name: "Activar notificaciones" })).not.toBeInTheDocument();
  });

  it("la nota de la IA para el equipo no va entre comillas: no son palabras del cliente", async () => {
    window.history.pushState({}, "", `/negocios/${CAFE}`);
    const user = userEvent.setup();
    const note = "Laura quiere el combo familiar y pidió hablar con alguien para pagar en efectivo.";
    const inbox = createMemoryInbox([], [notification({ body: note, bodyIsNote: true })]);
    render(<App services={createTestServices(createMemoryBackend([SAMPLE_DOCUMENT]), { inbox, devicePush: createMemoryDevicePush() })} />);
    await user.click(await screen.findByRole("button", { name: /Notificaciones: 1 sin leer/ }));
    const panel = screen.getByRole("dialog", { name: "Notificaciones" });
    expect(within(panel).getByText(note)).toBeInTheDocument();
    expect(within(panel).queryByText(`«${note}»`)).not.toBeInTheDocument();
  });

  it("el chat dice si la IA lo retomó o si llegó fuera del horario", async () => {
    const thread = (id: string, overrides: Partial<ConversationThread["conversation"]>): ConversationThread => ({
      conversation: {
        id, business: { slug: CAFE, name: "Café Aroma" }, channel: "whatsapp", contactName: id === "c1" ? "Laura" : "Pedro", status: "open",
        startedAt: ago(90), lastMessageAt: ago(2), lastMessagePreview: "Hola", messageCount: 2, needsHuman: true, handoffRequestedAt: ago(40),
        handoffReason: "human_request", canReply: true, ...overrides,
      },
      messages: [],
    });
    const inbox = createMemoryInbox([thread("c1", { aiPaused: false, aiResumedAt: ago(5) }), thread("c2", { aiPaused: false, aiResumedAt: null })]);
    window.history.pushState({}, "", `/negocios/${CAFE}/conversaciones?c=c1`);
    render(<App services={createTestServices(createMemoryBackend([SAMPLE_DOCUMENT]), { inbox })} />);
    expect(await screen.findByText(/Nadie respondió a tiempo, así que la IA retomó el chat hace 5 min/)).toBeInTheDocument();
    cleanup();
    window.history.pushState({}, "", `/negocios/${CAFE}/conversaciones?c=c2`);
    render(<App services={createTestServices(createMemoryBackend([SAMPLE_DOCUMENT]), { inbox })} />);
    expect(await screen.findByText(/Llegó fuera del horario de tu equipo: la IA sigue ayudándole mientras tanto/)).toBeInTheDocument();
  });
});

describe("Textos y piezas de la atención humana", () => {
  it("dice el horario y la espera como el asistente", () => {
    expect(hoursText([{ days: ["lunes", "miercoles", "viernes"], opens: "13:00", closes: "17:30" }, { days: ["sabado"], opens: "09:00", closes: "12:00" }])).toBe(
      "lunes, miércoles y viernes de 1:00 p. m. a 5:30 p. m. y el sábado de 9:00 a. m. a 12:00 m.",
    );
    expect([waitText(5), waitText(60), waitText(120)]).toEqual(["unos 5 minutos", "una hora", "unas 2 horas"]);
    expect(waitNotice(0)).toBeNull();
    const business = [{ days: ["lunes" as const], opens: "08:00", closes: "12:00" }];
    expect(effectiveHours({ hoursMode: "always", teamHours: [] }, business)).toEqual([]);
    expect(effectiveHours({ hoursMode: "business", teamHours: [] }, business)).toEqual(business);
  });

  it("convierte la clave de la plataforma y nombra el dispositivo", () => {
    expect(Array.from(applicationServerKey("AQIDBA"))).toEqual([1, 2, 3, 4]);
    expect(deviceLabel("Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/131.0 Mobile Safari/537.36")).toBe("Chrome en Android");
    expect(deviceLabel("Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 Version/18.0 Mobile/15E148 Safari/604.1")).toBe("Safari en iPhone");
  });
});
