/**
 * Forma de las cinco secciones por negocio que espera el motor actual
 * (`project/config/tenants/<slug>/{business,sales,pricing,inventory,config}.yaml`,
 * contenido bajo su clave raíz). Solo se declaran las claves que el adaptador escribe.
 */

export interface EngineTransferMethod {
  type: "nequi" | "daviplata" | "bank" | "breb";
  number?: string;
  bank?: string;
  account_type?: string;
  account_number?: string;
  reference?: string;
}

export interface EnginePaymentBlock {
  link: string;
  transfer: { enabled: boolean; methods: EngineTransferMethod[] };
}

export type EnginePriceValues = Partial<Record<"implementation" | "monthly" | "price", number>>;

export interface EnginePlan {
  id: string;
  name: string;
  description: string;
  pricing: Record<string, EnginePriceValues>;
  includes: string[];
  not_included: string[];
  payment: EnginePaymentBlock;
}

export interface EngineCatalog {
  categories: { id: string; name: string }[];
  items: { id: string; name: string; category: string; description: string; price: Record<string, number> }[];
  payment: EnginePaymentBlock;
}

export interface EngineBusinessSection {
  name: string;
  brand_name: string;
  industry: string;
  description: string;
  promise: string;
  tone: string;
  buying_motivation?: { primary: string; secondary: string };
}

export interface EngineSalesSection {
  pain: { clusters: Record<string, { impacts: string[] }> };
  discovery: { questions: string[] };
  closing: { hard_rules: string[] };
  offer: { recommendation_rules: { condition: string; recommend: string }[] };
}

export interface EnginePricingSection {
  model?: "catalog";
  plans?: EnginePlan[];
  catalog?: EngineCatalog;
  conditions: string[];
}

export interface EngineInventorySection {
  track_stock: boolean;
  items: unknown[];
}

export interface EngineConfigSection {
  initial_message: { enabled: boolean; text: string };
  features: { pricing_enabled: boolean; catalog_mode: boolean; business_model?: "catalog" };
  response: { length: "short" | "medium" | "long"; max_words: number };
  post_payment: {
    on_user_report: { message: string };
    on_payment_confirmed: { message: string };
  };
  capabilities: {
    channels: string[];
    business_channels: { allowed: string[] };
    system_channels: { allowed: string[] };
    actions: { primary: string[]; support: string[] };
    closing_methods: {
      link_payment: { enabled: boolean };
      human_handoff: { enabled: boolean };
      data_collection: { enabled: boolean };
    };
    data_collection: { enabled: boolean; fields: string[] };
  };
}

export interface EngineTenantSections {
  business: EngineBusinessSection;
  sales: EngineSalesSection;
  pricing: EnginePricingSection;
  inventory: EngineInventorySection;
  config: EngineConfigSection;
}
