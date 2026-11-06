import { SAMPLE_DOCUMENT, SAMPLE_PLANS_DOCUMENT } from "../../test/fixtures/sampleDocument";
import { paymentValuesToSend, sameDocument } from "./document";
import { createCatalogItem, createEmptyDocument, createPlan } from "./factories";
import {
  addPaymentProfile,
  addTransferMethod,
  changeTransferMethodType,
  keepStoredPaymentValue,
  removeCategory,
  removeEntry,
  removePaymentLink,
  removePaymentProfile,
  removeTransferMethod,
  renameCategory,
  saveCatalogItem,
  savePlan,
  setEntryAvailability,
  setPaymentLinkEnabled,
  setPaymentValue,
  setRootValue,
  setTransferEnabled,
  setTransferMethodEnabled,
  switchOfferModel,
  updateSection,
  updateTransferMethod,
} from "./operations";
import type { WorkingCopy } from "./types";

const working = (document = SAMPLE_DOCUMENT): WorkingCopy => ({ document, paymentValues: {} });
const firstProfile = (copy: WorkingCopy) => copy.document.payments[0]!;
const methodsOf = (copy: WorkingCopy) => firstProfile(copy).transfer_methods ?? [];

describe("operaciones sobre la oferta", () => {
  it("actualiza una sección sin tocar las demás ni mutar la original", () => {
    const next = updateSection(SAMPLE_DOCUMENT, "identity", { name: "Otro" });
    expect(next.identity.name).toBe("Otro");
    expect(next.identity.industry).toBe(SAMPLE_DOCUMENT.identity.industry);
    expect(next.payments).toBe(SAMPLE_DOCUMENT.payments);
    expect(SAMPLE_DOCUMENT.identity.name).toBe("Café Aroma");
  });

  it("reemplaza una sección completa de nivel superior", () => {
    const next = setRootValue(SAMPLE_DOCUMENT, "features", { multi_plan: true });
    expect(next.features).toEqual({ multi_plan: true });
    expect(next.identity).toBe(SAMPLE_DOCUMENT.identity);
  });

  it("agrega, edita y elimina planes", () => {
    const plan = createPlan({ id: "nuevo", name: "Plan" });
    const added = savePlan(createEmptyDocument("n", ""), plan);
    expect(added.offer.plans).toEqual([plan]);
    const edited = savePlan(added, { ...plan, name: "Plan Pro" });
    expect(edited.offer.plans).toEqual([{ ...plan, name: "Plan Pro" }]);
    expect(removeEntry(edited, "nuevo").offer.plans).toEqual([]);
  });

  it("agrega productos reutilizando la categoría por nombre, sin importar mayúsculas", () => {
    const item = createCatalogItem({ id: "te", name: "Té", prices: [{ currency: "COP", amount: 3000 }] });
    const next = saveCatalogItem(SAMPLE_DOCUMENT, item, "bebidas");
    const catalog = next.offer.catalog!;
    expect(catalog.items.at(-1)?.category).toBe("bebidas");
    expect(catalog.categories).toHaveLength(SAMPLE_DOCUMENT.offer.catalog!.categories.length);
  });

  it("crea la categoría si es nueva y asigna el perfil de pago", () => {
    const item = createCatalogItem({ id: "te", name: "Té" });
    const document = { ...SAMPLE_DOCUMENT, offer: { model: "catalog" as const, catalog: { categories: [], items: [] } } };
    const catalog = saveCatalogItem(document, item, "Infusiones Frías").offer.catalog!;
    expect(catalog.categories).toEqual([{ id: "infusiones_frias", name: "Infusiones Frías" }]);
    expect(catalog.items[0]?.category).toBe("infusiones_frias");
    expect(catalog.payment_profile).toBe("principal");
  });

  it("al editar un producto lo reemplaza en su sitio", () => {
    const [first] = SAMPLE_DOCUMENT.offer.catalog!.items;
    const catalog = saveCatalogItem(SAMPLE_DOCUMENT, { ...first!, name: "Café doble" }, "Bebidas").offer.catalog!;
    expect(catalog.items[0]?.name).toBe("Café doble");
    expect(catalog.items).toHaveLength(SAMPLE_DOCUMENT.offer.catalog!.items.length);
  });

  it("pausa y activa un producto sin cambiar el resto", () => {
    const paused = setEntryAvailability(SAMPLE_DOCUMENT, "sample_croissant", false);
    const items = paused.offer.catalog!.items;
    expect(items.find((item) => item.id === "sample_croissant")?.available).toBe(false);
    expect(items.find((item) => item.id === "sample_cafe_americano")).toBe(SAMPLE_DOCUMENT.offer.catalog!.items.find((item) => item.id === "sample_cafe_americano"));
  });

  it("pausa un plan", () => {
    const paused = setEntryAvailability(SAMPLE_PLANS_DOCUMENT, "basico", false);
    expect(paused.offer.plans?.[0]?.available).toBe(false);
  });

  it("al eliminar un producto se van sus variantes de inventario y las de otros se quedan", () => {
    const document = { ...SAMPLE_DOCUMENT, inventory: { track_stock: true, items: [{ product_id: "sample_croissant", variants: [] }, { product_id: "sample_desayuno", variants: [] }] } };
    const next = removeEntry(document, "sample_croissant");
    expect(next.offer.catalog!.items.map((item) => item.id)).not.toContain("sample_croissant");
    expect(next.inventory.items?.map((item) => item.product_id)).toEqual(["sample_desayuno"]);
    expect(next.inventory.track_stock).toBe(true);
  });

  it("renombra y quita categorías sin cambiar el identificador de las demás", () => {
    const renamed = renameCategory(SAMPLE_DOCUMENT, "bebidas", "Café");
    expect(renamed.offer.catalog!.categories[0]).toEqual({ id: "bebidas", name: "Café" });
    expect(removeCategory(renamed, "panaderia").offer.catalog!.categories.map((category) => category.id)).toEqual(["bebidas", "desayunos"]);
  });
});

describe("cambio de forma de venta", () => {
  it("cambiar a la misma forma no modifica nada", () => {
    expect(switchOfferModel(SAMPLE_DOCUMENT, "catalog")).toBe(SAMPLE_DOCUMENT);
  });

  it("de catálogo a planes: productos pasan a planes con precio único", () => {
    const next = switchOfferModel(SAMPLE_DOCUMENT, "plans");
    expect(next.offer.model).toBe("plans");
    expect(next.offer.catalog).toBeUndefined();
    expect(next.offer.plans?.[0]).toMatchObject({ id: "sample_cafe_americano", name: "Café americano", prices: [{ currency: "COP", price: 6000 }], payment_profile: "principal" });
    expect(next.offer.plans?.[2]?.available).toBe(false);
  });

  it("de planes a catálogo: planes pasan a productos con un solo precio", () => {
    const next = switchOfferModel(SAMPLE_PLANS_DOCUMENT, "catalog");
    expect(next.offer.model).toBe("catalog");
    expect(next.offer.plans).toBeUndefined();
    expect(next.offer.catalog?.categories).toEqual([{ id: "general", name: "General" }]);
    expect(next.offer.catalog?.items[0]).toMatchObject({ id: "basico", category: "general", prices: [{ currency: "COP", amount: 50000 }], features: ["Soporte por chat"] });
  });

  it("al pasar a planes descarta el inventario, que solo existe en catálogo", () => {
    const document = { ...SAMPLE_DOCUMENT, inventory: { items: [{ product_id: "sample_croissant", variants: [] }] } };
    expect(switchOfferModel(document, "plans").inventory.items).toEqual([]);
  });
});

describe("datos de pago", () => {
  it("activar el enlace pide un valor nuevo con referencia propia; desactivarlo lo quita", () => {
    const start = addPaymentProfile(working(SAMPLE_PLANS_DOCUMENT));
    const enabled = setPaymentLinkEnabled(start, "principal", true);
    const ref = firstProfile(enabled).link!.secret_ref;
    expect(ref).toMatch(/^secret_store:principal\.link\./);
    expect(enabled.paymentValues).toEqual({ [ref]: "" });

    const disabled = setPaymentLinkEnabled(setPaymentValue(enabled, ref, "https://x"), "principal", false);
    expect(firstProfile(disabled).link).toBeNull();
    expect(disabled.paymentValues).toEqual({});
  });

  it("activar el enlace cuando ya existe conserva el dato guardado", () => {
    const start = working();
    expect(setPaymentLinkEnabled(start, "principal", true)).toBe(start);
  });

  describe("con datos ya guardados", () => {
    const STORED_LINK = "secret_store:principal.link~guardado";
    const STORED_NUMBER = "secret_store:principal.nequi.number~guardado";
    const profile = SAMPLE_DOCUMENT.payments[0]!;
    const stored = (): WorkingCopy =>
      working({
        ...SAMPLE_DOCUMENT,
        payments: [{ ...profile, link: { secret_ref: STORED_LINK }, transfer_methods: [{ type: "nequi", number: { secret_ref: STORED_NUMBER } }] }],
      });

    it("desactivar el enlace lo conserva y activarlo deja el documento como estaba", () => {
      const start = stored();
      const paused = setPaymentLinkEnabled(start, "principal", false);
      expect(firstProfile(paused).link?.secret_ref).toBe(STORED_LINK);
      expect(firstProfile(paused).link_enabled).toBe(false);
      expect(sameDocument(paused.document, start.document)).toBe(false);
      expect(sameDocument(setPaymentLinkEnabled(paused, "principal", true).document, start.document)).toBe(true);
    });

    it("quitar el enlace es una acción aparte y descarta lo que se estaba escribiendo", () => {
      const removed = removePaymentLink(setPaymentValue(stored(), STORED_LINK, "https://nuevo.example.com"), "principal");
      expect(firstProfile(removed).link).toBeNull();
      expect(removed.paymentValues).toEqual({});
    });

    it("un reemplazo vacío no se envía: se conserva lo guardado", () => {
      for (const empty of ["", "   "]) expect(paymentValuesToSend(setPaymentValue(stored(), STORED_LINK, empty))).toEqual({});
      expect(paymentValuesToSend(setPaymentValue(stored(), STORED_LINK, "https://nuevo.example.com"))).toEqual({ [STORED_LINK]: "https://nuevo.example.com" });
    });

    it("desactivar y activar una cuenta no toca sus datos y deja el documento como estaba", () => {
      const start = stored();
      const paused = setTransferMethodEnabled(start, "principal", 0, false);
      expect(methodsOf(paused)[0]).toEqual({ type: "nequi", number: { secret_ref: STORED_NUMBER }, enabled: false });
      expect(paused.paymentValues).toEqual({});
      expect(sameDocument(setTransferMethodEnabled(paused, "principal", 0, true).document, start.document)).toBe(true);
    });

    it("editar el banco o la etiqueta no toca el dato cifrado", () => {
      const edited = updateTransferMethod(stored(), "principal", 0, { label: "Cuenta de la tienda" });
      expect(methodsOf(edited)[0]).toEqual({ type: "nequi", number: { secret_ref: STORED_NUMBER }, label: "Cuenta de la tienda" });
      expect(edited.paymentValues).toEqual({});
    });

    it("desactivar las transferencias no borra una cuenta guardada aunque su reemplazo esté a medias", () => {
      const replacing = setPaymentValue(stored(), STORED_NUMBER, "");
      const off = setTransferEnabled(replacing, "principal", false);
      expect(methodsOf(off).map((method) => method.number?.secret_ref)).toEqual([STORED_NUMBER]);
      expect(paymentValuesToSend(off)).toEqual({});
    });

    it("cambiar el tipo conserva la etiqueta y el estado, y descarta lo demás", () => {
      const labelled = setTransferMethodEnabled(updateTransferMethod(stored(), "principal", 0, { label: "Cuenta de la tienda" }), "principal", 0, false);
      const [method] = methodsOf(changeTransferMethodType(labelled, "principal", 0, "breb"));
      expect(method).toMatchObject({ type: "breb", label: "Cuenta de la tienda", enabled: false });
      expect(method?.number).toBeUndefined();
    });
  });

  it("los valores viajan aparte del documento y conservar lo guardado deja de enviarlos", () => {
    const ref = SAMPLE_DOCUMENT.payments[0]!.link!.secret_ref;
    const replaced = setPaymentValue(working(), ref, "  https://pagos.example.com  ");
    expect(JSON.stringify(replaced.document)).not.toContain("pagos.example.com");
    expect(sameDocument(replaced.document, SAMPLE_DOCUMENT)).toBe(true);
    expect(paymentValuesToSend(replaced)).toEqual({ [ref]: "https://pagos.example.com" });
    expect(paymentValuesToSend(keepStoredPaymentValue(replaced, ref))).toEqual({});
  });

  it("normaliza celular y cuenta al enviarlos y omite los que ya no están en el documento", () => {
    let copy = addTransferMethod(working(), "principal");
    const mobile = methodsOf(copy).at(-1)!.number!.secret_ref;
    copy = setPaymentValue(copy, mobile, "300 123 4567");
    copy = addTransferMethod(copy, "principal");
    copy = changeTransferMethodType(copy, "principal", 2, "bank");
    const account = methodsOf(copy).at(-1)!.account_number!.secret_ref;
    copy = setPaymentValue(copy, account, "123-456 789");
    const stale = { ...copy, paymentValues: { ...copy.paymentValues, "secret_store:ya_no_existe": "dato" } };
    expect(paymentValuesToSend(stale)).toEqual({ [mobile]: "3001234567", [account]: "123456789" });
  });

  it("agrega, edita y quita cuentas de transferencia", () => {
    const added = addTransferMethod(working(), "principal");
    expect(methodsOf(added)).toHaveLength(2);
    const newRef = methodsOf(added)[1]!.number!.secret_ref;
    expect(added.paymentValues).toEqual({ [newRef]: "" });

    const bank = changeTransferMethodType(added, "principal", 1, "bank");
    const edited = updateTransferMethod(bank, "principal", 1, { bank: "Banco Ejemplo", account_type: "corriente" });
    expect(methodsOf(edited)[1]).toMatchObject({ type: "bank", bank: "Banco Ejemplo", account_type: "corriente" });

    const removed = removeTransferMethod(edited, "principal", 1);
    expect(methodsOf(removed)).toHaveLength(1);
    expect(removed.paymentValues).toEqual({});
  });

  it("al cambiar el tipo de cuenta descarta los datos del tipo anterior", () => {
    const previous = methodsOf(working())[0]!.number!.secret_ref;
    const changed = changeTransferMethodType(setPaymentValue(working(), previous, "3001112222"), "principal", 0, "bank");
    const [method] = methodsOf(changed);
    expect(method).toMatchObject({ type: "bank", bank: "", account_type: "ahorros" });
    expect(method?.number).toBeUndefined();
    expect(Object.keys(changed.paymentValues)).toEqual([method!.account_number!.secret_ref]);

    const breb = changeTransferMethodType(changed, "principal", 0, "breb");
    expect(methodsOf(breb)[0]?.bank).toBeUndefined();
    expect(Object.keys(breb.paymentValues)).toEqual([methodsOf(breb)[0]!.reference!.secret_ref]);
  });

  it("cambiar al mismo tipo no borra nada", () => {
    const start = working();
    expect(changeTransferMethodType(start, "principal", 0, "nequi")).toBe(start);
  });

  it("al desactivar transferencias conserva las cuentas guardadas y descarta las que aún no tienen dato", () => {
    const withNew = addTransferMethod(working(), "principal");
    const off = setTransferEnabled(withNew, "principal", false);
    expect(firstProfile(off).transfer_enabled).toBe(false);
    expect(methodsOf(off)).toEqual(methodsOf(working()));
    expect(off.paymentValues).toEqual({});
  });

  it("crea un perfil, se lo asigna a lo que no tenía y no repite el identificador", () => {
    const first = addPaymentProfile(working(SAMPLE_PLANS_DOCUMENT));
    expect(first.document.payments.map((profile) => profile.id)).toEqual(["principal"]);
    expect(first.document.offer.plans?.every((plan) => plan.payment_profile === "principal")).toBe(true);
    const second = addPaymentProfile(first);
    expect(second.document.payments.map((profile) => profile.id)).toEqual(["principal", "perfil_2"]);
    expect(second.document.offer.plans?.every((plan) => plan.payment_profile === "principal")).toBe(true);
  });

  it("al quitar un perfil lo desasigna y descarta sus valores sin guardar", () => {
    const ref = SAMPLE_DOCUMENT.payments[0]!.link!.secret_ref;
    const removed = removePaymentProfile(setPaymentValue(working(), ref, "https://x"), "principal");
    expect(removed.document.payments).toEqual([]);
    expect(removed.document.offer.catalog?.payment_profile).toBeNull();
    expect(removed.paymentValues).toEqual({});
  });
});

describe("comparación de documentos", () => {
  it("no considera cambio un opcional vacío ni el orden de las claves", () => {
    const { identity, ...rest } = SAMPLE_DOCUMENT;
    const reordered = { identity: { ...identity, positioning: null }, ...rest };
    expect(sameDocument(reordered, SAMPLE_DOCUMENT)).toBe(true);
    expect(sameDocument({ ...reordered, identity: { ...identity, name: "Otro" } }, SAMPLE_DOCUMENT)).toBe(false);
  });
});
