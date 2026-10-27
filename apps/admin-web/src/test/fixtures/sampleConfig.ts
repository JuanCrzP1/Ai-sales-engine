import type { AssistantConfig } from "../../domain/config/types";

/**
 * Configuración completa de un negocio ficticio, solo para pruebas automatizadas.
 * La aplicación no la carga: cada cuenta empieza con una configuración vacía.
 * Los números de pago son marcadores y el enlace usa el dominio reservado `example.com`.
 */
export const SAMPLE_CONFIG: AssistantConfig = {
  version: 1,
  business: {
    name: "Café Aroma",
    businessType: "cafetería con domicilios",
    description: "Cafetería de barrio que vende café, panadería y desayunos para llevar.",
    valueProposition: "Tu desayuno listo en minutos, pedido directo por chat y sin filas.",
    salesMode: "catalog",
  },
  offerings: [
    {
      id: "sample_cafe_americano",
      name: "Café americano",
      description: "Café filtrado de 12 oz.",
      category: "Bebidas",
      price: 6000,
      setupFee: null,
      currency: "COP",
      billing: "one_time",
      features: ["Tamaño 12 oz"],
      notIncluded: [],
      available: true,
    },
    {
      id: "sample_croissant",
      name: "Croissant de mantequilla",
      description: "Horneado cada mañana.",
      category: "Panadería",
      price: 5500,
      setupFee: null,
      currency: "COP",
      billing: "one_time",
      features: [],
      notIncluded: [],
      available: true,
    },
    {
      id: "sample_desayuno",
      name: "Desayuno completo",
      description: "Huevos, pan, fruta y bebida caliente.",
      category: "Desayunos",
      price: 18000,
      setupFee: null,
      currency: "COP",
      billing: "one_time",
      features: ["Incluye bebida caliente"],
      notIncluded: [],
      available: false,
    },
  ],
  payments: {
    paymentLinkEnabled: true,
    paymentLink: "https://pagos.example.com/cafe-aroma",
    transferEnabled: true,
    transferMethods: [
      {
        id: "sample_nequi",
        type: "nequi",
        phoneNumber: "3000000000",
        bankName: "",
        accountType: "ahorros",
        accountNumber: "",
        reference: "",
      },
    ],
    conditions: ["Domicilios solo dentro del barrio."],
  },
  closing: {
    sendPaymentLink: true,
    humanHandoff: false,
    collectCustomerData: true,
    customerDataFields: ["nombre", "telefono", "direccion"],
    actions: ["tomar_pedido", "cerrar_venta", "responder_dudas", "confirmar_datos"],
  },
  behavior: {
    tone: "cercano",
    responseLength: "short",
    primaryMotivation: "ahorrar tiempo en la mañana",
    secondaryMotivation: "comer bien sin salir",
    customerProblems: ["no tienen tiempo de desayunar antes del trabajo"],
    salesRules: ["Confirmar la dirección antes de cerrar el pedido."],
    discoveryQuestions: ["¿Para cuántas personas es el pedido?"],
    recommendationNotes: "Si piden café, sugerir un acompañamiento de panadería.",
  },
  messages: {
    welcomeEnabled: true,
    welcomeText: "¡Hola! Bienvenido a Café Aroma. ¿Quieres hacer un pedido?",
    paymentReportedText: "Gracias, ya reviso tu pago y te confirmo en un momento.",
    paymentConfirmedText: "Listo, tu pago quedó confirmado. Preparamos tu pedido.",
    serviceChannels: ["whatsapp"],
  },
};
