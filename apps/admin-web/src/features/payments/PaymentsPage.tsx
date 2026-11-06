import { Alert } from "../../components/ui/Feedback";
import { PageHeader } from "../../components/ui/Layout";
import { ContractSection } from "../../layout/ContractSection";
import { SectionPager } from "../../layout/SectionPager";
import { stepLabel } from "../../navigation/navItems";
import { useFieldIssue } from "../../state/useConfig";
import { ClosingForm } from "./ClosingForm";
import { PaymentMethodsOverview } from "./PaymentMethodsOverview";
import { PaymentProfilesForm } from "./PaymentProfilesForm";
import { PromotionsForm } from "./PromotionsForm";
import { TermsForm } from "./TermsForm";

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

      <PaymentMethodsOverview />
      <PaymentProfilesForm />
      <PromotionsForm />
      <TermsForm />
      <ClosingForm />
      <ContractSection
        title="Financiación y argumentos de precio"
        description="Opciones avanzadas: financiación disponible y cómo responder si el cliente duda del precio."
        section="terms"
        fields={["financing", "price_framing", "roi_break_even_sales", "roi_break_even_bookings", "roi_hints"]}
      />
      <SectionPager current="payments" />
    </>
  );
}
