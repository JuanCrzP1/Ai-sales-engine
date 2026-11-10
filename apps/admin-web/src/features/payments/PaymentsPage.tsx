import { Alert } from "../../components/ui/Feedback";
import { Badge } from "../../components/ui/Feedback";
import { PageHeader } from "../../components/ui/Layout";
import { SettingsGroup } from "../../components/ui/SettingsCard";
import { ContractSection } from "../../layout/ContractSection";
import { SectionPager } from "../../layout/SectionPager";
import { stepLabel } from "../../navigation/navItems";
import { useFieldIssue } from "../../state/useConfig";
import { ClosingForm } from "./ClosingForm";
import { PaymentMethodsOverview } from "./PaymentMethodsOverview";
import { PaymentProfilesForm } from "./PaymentProfilesForm";
import { PromotionsForm } from "./PromotionsForm";
import { PoliciesForm, TermsForm } from "./TermsForm";

export function PaymentsPage() {
  const noPaymentIssue = useFieldIssue("payments");

  return (
    <>
      <PageHeader
        eyebrow={stepLabel("payments")}
        title="Pagos y cierre de ventas"
        description="Indica cómo pueden pagarte tus clientes, tus promociones y tus políticas. El asistente solo comparte los datos de pago cuando el cliente elige cómo pagar."
      />

      <Alert tone="info">
        <p>Este panel no procesa pagos ni confirma transacciones. Los enlaces, números y cuentas se guardan cifrados: aquí solo ves una parte para reconocerlos y, si cambian, puedes reemplazarlos.</p>
      </Alert>

      {noPaymentIssue && <Alert tone="warning">{noPaymentIssue.message}</Alert>}

      <SettingsGroup title="Cómo te pagan" description="Los medios de pago que el asistente ofrece cuando el cliente quiere comprar.">
        <PaymentMethodsOverview />
        <PaymentProfilesForm />
      </SettingsGroup>
      <SettingsGroup title="Venta y condiciones" description="Cómo se cierra una venta, tus promociones y lo que el asistente debe respetar.">
        <ClosingForm />
        <PromotionsForm />
        <TermsForm />
        <PoliciesForm />
      </SettingsGroup>
      <SettingsGroup title="Para afinar" description="Opcional. Ábrelas cuando quieras darle más detalle al asistente.">
        <ContractSection
          title="Financiación"
          description="Si ofreces pagar a cuotas o con una entidad aliada. Si no la ofreces, el asistente lo dice claro."
          section="terms"
          fields={["financing"]}
          icon="card"
          tone="emerald"
          badge={<Badge tone="neutral">Opcional</Badge>}
        />
        <ContractSection
          title="Argumentos de precio"
          description="Cómo responder si el cliente duda del precio y cuánto tarda en recuperar lo que paga (para quien vende a otros negocios)."
          section="terms"
          fields={["price_framing", "roi_break_even_sales", "roi_break_even_bookings", "roi_hints"]}
          icon="lightbulb"
          tone="amber"
          badge={<Badge tone="neutral">Avanzado</Badge>}
        />
      </SettingsGroup>
      <SectionPager current="payments" />
    </>
  );
}
