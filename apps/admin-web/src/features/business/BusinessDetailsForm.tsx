import { CheckboxGroup } from "../../components/ui/ChoiceGroup";
import { SelectField, TextField } from "../../components/ui/FormFields";
import { SettingsCard } from "../../components/ui/SettingsCard";
import { ListEditor } from "../../components/ui/ListEditor";
import type { Identity, Location } from "../../domain/config/types";
import { optionalList, optionalText } from "../../domain/config/document";
import { COVERAGE_TYPES, LOCATION_TYPES, SERVICE_MODES } from "../../domain/config/options";
import { useFieldIssue, useSection } from "../../state/useConfig";

/** Por qué elegir este negocio: sus diferenciadores y sus pruebas de confianza. */
export function BusinessTrustForm() {
  const [identity, update] = useSection("identity");
  const differentiatorsIssue = useFieldIssue("identity.differentiators");
  return (
    <SettingsCard icon="shield" tone="emerald" title="Por qué elegirte" description="Lo que te diferencia y lo que da confianza.">
      <ListEditor
        label="Por qué elegirte"
        items={identity.differentiators ?? []}
        onChange={(items) => update({ differentiators: optionalList(items) })}
        placeholder="Ej.: Entregas en menos de 30 minutos"
        addLabel="Agregar diferenciador"
      />
      {differentiatorsIssue && <p className={`field__message field__message--${differentiatorsIssue.severity}`}>{differentiatorsIssue.message}</p>}
      <ListEditor
        label="Pruebas de confianza"
        items={identity.credibility ?? []}
        onChange={(items) => update({ credibility: optionalList(items) })}
        placeholder="Ej.: Más de 500 clientes atendidos"
        addLabel="Agregar prueba"
        hint="Casos, resultados o trayectoria."
      />
    </SettingsCard>
  );
}

/** Dónde está el negocio, a qué zonas llega y cómo recibe el cliente lo que compra. */
export function BusinessDetailsForm() {
  const [identity, update] = useSection("identity");
  const addressIssue = useFieldIssue("identity.location.address");
  const location = identity.location;

  const changeLocation = (patch: Partial<Location>) => {
    if (location) update({ location: { ...location, ...patch } });
  };
  const changeType = (type: "" | Location["type"]) => {
    update({ location: type === "" ? null : { coverage: { type: "local", zones: [] }, ...location, type } });
  };

  return (
    <SettingsCard icon="mapPin" tone="sky" title="Dónde y cómo atiendes" description="Tu ubicación, las zonas a las que llegas y cómo recibe el cliente.">
      <div className="grid-2">
        <SelectField label="¿Dónde atiendes?" value={location?.type ?? ""} options={LOCATION_TYPES} onChange={changeType} />
        {location && location.type !== "virtual" && (
          <TextField label="Dirección" value={location.address ?? ""} onChange={(address) => changeLocation({ address: optionalText(address) })} issue={addressIssue} />
        )}
        {location && <TextField label="Ciudad" value={location.city ?? ""} onChange={(city) => changeLocation({ city: optionalText(city) })} />}
        {location && (
          <SelectField
            label="Cobertura"
            value={location.coverage?.type ?? "local"}
            options={COVERAGE_TYPES}
            onChange={(type) => changeLocation({ coverage: { zones: [], ...location.coverage, type } })}
          />
        )}
      </div>
      {location && (
        <ListEditor
          label="Zonas de cobertura"
          items={location.coverage?.zones ?? []}
          onChange={(zones) => changeLocation({ coverage: { type: "local", ...location.coverage, zones } })}
          placeholder="Ej.: Chapinero"
          addLabel="Agregar zona"
          hint="Barrios, ciudades o países a los que atiendes o envías."
        />
      )}

      <CheckboxGroup<NonNullable<Identity["service_modes"]>[number]>
        legend="Cómo recibe el cliente el servicio o producto"
        name="service-modes"
        options={SERVICE_MODES}
        values={identity.service_modes ?? []}
        onChange={(modes) => update({ service_modes: optionalList(modes) })}
      />
    </SettingsCard>
  );
}
