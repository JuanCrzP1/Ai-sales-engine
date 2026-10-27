import { RadioGroup } from "../../components/ui/ChoiceGroup";
import { Card } from "../../components/ui/Layout";
import { SALES_MODES } from "../../domain/config/options";
import { useSection } from "../../state/useConfig";

export function SalesModeForm() {
  const [business, update] = useSection("business");

  return (
    <Card title="¿Cómo vendes?" description="Define cómo se presentan tus productos o servicios al cliente.">
      <RadioGroup
        legend="Forma de venta"
        name="sales-mode"
        options={SALES_MODES}
        value={business.salesMode}
        onChange={(salesMode) => update({ salesMode })}
      />
    </Card>
  );
}
