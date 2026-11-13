// El teléfono de prueba: hace de cliente frente al negocio. Lee el estado del simulador cada segundo y escribe por `/_sim/*`.
// Todo el texto que viene del simulador se pone con textContent: nunca como HTML.

const $ = (id) => document.getElementById(id);
const selected = { instance: null, phone: null };
let pendingFile = null;

async function api(path, options = {}) {
  const response = await fetch(path, { headers: { "Content-Type": "application/json" }, ...options });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(typeof body.detail === "string" ? body.detail : "El simulador no pudo hacerlo.");
  return body;
}

function toast(text) {
  const element = $("toast");
  element.textContent = text;
  element.hidden = false;
  setTimeout(() => (element.hidden = true), 3500);
}

function el(tag, attributes = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attributes)) {
    // Un atributo sin valor (por ejemplo, `disabled` cuando no aplica) no se pone: si no, quedaría escrito «null».
    if (value === null || value === undefined || value === false) continue;
    if (key === "class") node.className = value;
    else if (key.startsWith("on")) node.addEventListener(key.slice(2), value);
    else node.setAttribute(key, value);
  }
  for (const child of children) if (child !== null && child !== undefined) node.append(child);
  return node;
}

const STATUS = { connected: "Conectado", connecting: "Esperando el QR", disconnected: "Desconectado" };

function renderNumbers(instances) {
  const list = $("numbers");
  list.replaceChildren(
    ...instances.map((instance) => {
      const item = el("li", { class: `item${selected.instance === instance.token ? " item--active" : ""}` },
        el("div", { class: "item__row" },
          el("strong", {}, instance.name),
          el("span", { class: `badge badge--${instance.status}` }, STATUS[instance.status] ?? instance.status)),
        instance.phone ? el("span", { class: "muted small" }, `+${instance.phone}${instance.profile_name ? ` · ${instance.profile_name}` : ""}`) : null,
        instance.webhook_url ? null : el("span", { class: "muted small" }, "El panel todavía no registró su aviso."),
      );
      if (instance.status === "connecting") {
        const phone = el("input", { placeholder: "Número del negocio (opcional)", "aria-label": "Número del negocio", inputmode: "tel" });
        item.append(
          el("img", { class: "qr", src: "/qr.png", alt: "Código QR de prueba" }),
          phone,
          el("button", { type: "button", onclick: () => scan(instance.token, phone.value) }, "Escanear QR"),
        );
      }
      if (instance.status === "connected") {
        item.append(el("button", { type: "button", class: "ghost", onclick: () => { selected.instance = instance.token; refresh(); } }, selected.instance === instance.token ? "Usando este número" : "Usar este número"));
      }
      return item;
    }),
  );
  if (!instances.length) list.append(el("li", { class: "muted small" }, "Todavía no hay números."));
}

function renderClients(clients) {
  $("clients").replaceChildren(
    ...clients.map((client) =>
      el("li", { class: `item${selected.phone === client.phone ? " item--active" : ""}` },
        el("div", { class: "item__row" },
          el("span", {}, `${client.name} · +${client.phone}`),
          el("button", { type: "button", class: "ghost", disabled: selected.instance ? null : "disabled", onclick: () => openChat(client.phone) }, "Abrir chat"))),
    ),
  );
}

function ticks(message) {
  if (message.author !== "business") return "";
  return message.status === "sent" ? "✓" : "✓✓";
}

function renderMessages(messages) {
  const list = $("messages");
  const atBottom = list.scrollHeight - list.scrollTop - list.clientHeight < 40;
  list.replaceChildren(
    ...messages.map((message) => {
      const bubble = el("li", { class: `bubble bubble--${message.author}` });
      if (message.author === "phone") bubble.append(el("span", { class: "bubble__who" }, "El negocio, desde su celular"));
      if (message.media) {
        if (message.media.mime_type.startsWith("image/")) bubble.append(el("img", { src: message.media.data_url, alt: message.media.file_name || "Foto" }));
        else if (message.media.mime_type.startsWith("audio/")) bubble.append(el("audio", { controls: "controls", src: message.media.data_url }));
        else bubble.append(el("a", { href: message.media.data_url, download: message.media.file_name || "archivo" }, `📄 ${message.media.file_name || "Documento"}`));
      }
      if (message.text) bubble.append(message.text);
      const time = new Date(message.at * 1000).toLocaleTimeString("es-CO", { hour: "2-digit", minute: "2-digit" });
      bubble.append(el("span", { class: "bubble__meta" }, `${time} `, el("span", { class: message.status === "read" ? "ticks--read" : "" }, ticks(message))));
      return bubble;
    }),
  );
  if (atBottom) list.scrollTop = list.scrollHeight;
}

async function refresh() {
  try {
    const state = await api("/_sim/state");
    const connected = state.instances.filter((instance) => instance.status === "connected");
    if (!selected.instance && connected.length) selected.instance = connected[0].token;
    renderNumbers(state.instances);
    renderClients(state.clients);
    if (selected.instance && selected.phone) {
      const client = state.clients.find((item) => item.phone === selected.phone);
      const instance = state.instances.find((item) => item.token === selected.instance);
      $("chat-empty").hidden = true;
      $("chat").hidden = false;
      $("chat-title").textContent = instance?.profile_name || instance?.name || "Negocio";
      $("chat-subtitle").textContent = `Hablas como ${client?.name ?? "cliente"} (+${selected.phone})`;
      $("chat-typing").hidden = !state.typing.includes(`${selected.instance}:${selected.phone}`);
      const chat = await api(`/_sim/chats/${selected.instance}/${selected.phone}`);
      renderMessages(chat.messages);
      // Con el chat abierto y la página a la vista, lo del negocio queda leído (azul), como en WhatsApp.
      if (document.visibilityState === "visible" && chat.messages.some((message) => message.author === "business" && message.status !== "read")) {
        await api(`/_sim/chats/${selected.instance}/${selected.phone}/open`, { method: "POST" });
      }
    }
  } catch (error) {
    toast(error.message);
  }
}

async function scan(token, phone) {
  try {
    await api(`/_sim/instances/${token}/scan`, { method: "POST", body: JSON.stringify({ phone }) });
    selected.instance = token;
    toast("Conectado. El panel lo muestra en unos segundos.");
    refresh();
  } catch (error) {
    toast(error.message);
  }
}

function openChat(phone) {
  selected.phone = phone;
  refresh();
}

$("client-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const client = await api("/_sim/clients", { method: "POST", body: JSON.stringify({ name: $("client-name").value, phone: $("client-phone").value }) });
    $("client-name").value = "";
    $("client-phone").value = "";
    if (selected.instance) openChat(client.phone);
    else refresh();
  } catch (error) {
    toast(error.message);
  }
});

$("file").addEventListener("change", () => {
  const file = $("file").files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    const kind = file.type.startsWith("image/") ? "image" : file.type.startsWith("audio/") ? "audio" : file.type.startsWith("video/") ? "video" : "document";
    pendingFile = { kind, file_base64: String(reader.result), mime_type: file.type || "application/octet-stream", file_name: file.name };
    $("file-chip").textContent = `Adjunto: ${file.name} (escribe un texto si quieres y toca Enviar)`;
    $("file-chip").hidden = false;
  };
  reader.readAsDataURL(file);
});

$("composer").addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = $("text").value.trim();
  if (!text && !pendingFile) return;
  const body = { text, from_business_phone: $("as-business").checked, ...(pendingFile ?? {}) };
  try {
    await api(`/_sim/chats/${selected.instance}/${selected.phone}/write`, { method: "POST", body: JSON.stringify(body) });
    $("text").value = "";
    pendingFile = null;
    $("file").value = "";
    $("file-chip").hidden = true;
    refresh();
  } catch (error) {
    toast(error.message);
  }
});

$("show-log").addEventListener("click", async () => {
  const { items } = await api("/_sim/log");
  $("log").replaceChildren(
    ...items.map((item) =>
      el("li", { class: item.status && item.status >= 400 ? "error" : "" },
        `${new Date(item.at * 1000).toLocaleTimeString("es-CO")} · ${item.kind}: ${item.summary}${item.status ? ` (${item.status})` : ""}`,
        item.detail && item.status && item.status >= 400 ? el("div", { class: "muted small" }, item.detail) : null)),
  );
  $("log-dialog").showModal();
});
$("close-log").addEventListener("click", () => $("log-dialog").close());

$("reset").addEventListener("click", async () => {
  if (!confirm("¿Borrar números, clientes y mensajes del simulador? En el panel tendrás que volver a conectar.")) return;
  await api("/_sim/reset", { method: "POST" });
  selected.instance = null;
  selected.phone = null;
  $("chat").hidden = true;
  $("chat-empty").hidden = false;
  refresh();
});

refresh();
setInterval(refresh, 1000);
