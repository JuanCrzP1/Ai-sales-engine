import { Alert } from "../../components/ui/Feedback";
import { Card, PageHeader } from "../../components/ui/Layout";
import { ListEditor } from "../../components/ui/ListEditor";
import { SectionPager } from "../../layout/SectionPager";
import { stepLabel } from "../../navigation/navItems";
import { useFieldIssue, useSection } from "../../state/useConfig";
import { ClosingForm } from "./ClosingForm";
import { PaymentLinkForm } from "./PaymentLinkForm";
import { TransferMethodsForm } from "./TransferMethodsForm";

export function PaymentsPage() {
  const [payments, update] = useSection("payments");
  const noPaymentIssue = useFieldIssue("payments");

  return (
    <>
      <PageHeader
        eyebrow={stepLabel("payments")}
        title="Pagos y cierre de ventas"
        description="Indica cómo pueden pagarte tus clientes. El asistente solo comparte estos datos cuando el cliente elige cómo pagar."
      />

      <Alert tone="info">
        <p>
          Este panel no procesa pagos ni confirma transacciones. El asistente solo comparte la información de pago que
          configures aquí.
        </p>
      </Alert>

      {noPaymentIssue && <Alert tone="warning">{noPaymentIssue.message}</Alert>}

      <PaymentLinkForm />
      <TransferMethodsForm />

      <Card title="Condiciones comerciales" description="Políticas que el asistente debe tener presentes al hablar de precios.">
        <ListEditor
          label="Condiciones"
          items={payments.conditions}
          onChange={(conditions) => update({ conditions })}
          placeholder="Ej.: Domicilio gratis en compras superiores a $50.000"
          addLabel="Agregar condición"
          emptyText="Sin condiciones por ahora."
        />
      </Card>

      <ClosingForm />
      <SectionPager current="payments" />
    </>
  );
}
