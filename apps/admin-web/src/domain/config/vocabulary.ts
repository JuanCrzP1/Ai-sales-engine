/**
 * Los identificadores que guarda el contrato (`detect_pain`, `license_type`, `price`) dichos en español para el negocio. Son los
 * mismos que el motor dice a la IA (`project/app/infrastructure/ai/prompting/vocabulary.py`): el panel muestra lo que el asistente
 * entiende. Un valor que no esté aquí se puede usar igual: el motor lo dice tal cual.
 */

/** Pasos de la conversación, en su orden natural de venta. */
export const CONVERSATION_STEPS: Record<string, string> = {
  detect_pain: "Entender qué necesita",
  amplify_impact: "Mostrarle lo que le cuesta no resolverlo",
  present_solution: "Presentarle la opción que lo resuelve",
  validate_requirements: "Revisar que cumpla los requisitos",
  guide_next_step: "Guiarlo al siguiente paso",
};

/** Lo que el negocio no quiere que haga el asistente. */
export const FORBIDDEN_ACTIONS: Record<string, string> = {
  responder_sin_direccion: "Responder sin llevar a un siguiente paso",
  responder_sin_solucion: "Responder sin ofrecer una solución",
};

/** Temas de objeción frecuentes. */
export const OBJECTION_TOPICS: Record<string, string> = {
  price: "El precio",
  time: "El tiempo",
  trust: "La confianza",
  competition: "La competencia",
};

/** Datos que se piden para cerrar una venta. */
export const CLOSING_DATA: Record<string, string> = {
  name: "Nombre",
  phone: "Teléfono",
  address: "Dirección",
  email: "Correo",
  city: "Ciudad",
  document: "Documento",
  day: "Día",
  hour: "Hora",
  dates: "Fechas",
  destination: "Destino",
  license_type: "Tipo de licencia",
};

/** Campos del contrato que son listas de identificadores con un vocabulario conocido. */
export const VOCABULARY_BY_FIELD: Record<string, Record<string, string>> = {
  steps: CONVERSATION_STEPS,
  required_flow: CONVERSATION_STEPS,
  forbid: FORBIDDEN_ACTIONS,
  required_data: CLOSING_DATA,
};
