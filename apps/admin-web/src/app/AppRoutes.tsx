import { AssistantOverviewPage } from "../features/overview/AssistantOverviewPage";
import { Navigate, Route } from "react-router-dom";
import { AISettingsPage } from "../features/ai/AISettingsPage";
import { AttentionSettingsPage } from "../features/attention/AttentionSettingsPage";
import { AssistantPage } from "../features/assistant/AssistantPage";
import { AuthLayout } from "../features/auth/AuthLayout";
import { SignInPage } from "../features/auth/SignInPage";
import { SignUpPage } from "../features/auth/SignUpPage";
import { BusinessesPage } from "../features/businesses/BusinessesPage";
import { WelcomePage } from "../features/businesses/WelcomePage";
import { ChannelsPage } from "../features/channels/ChannelsPage";
import { ConversationsPage } from "../features/conversations/ConversationsPage";
import { CustomersPage } from "../features/commerce/CustomersPage";
import { ReportsPage } from "../features/commerce/ReportsPage";
import { SalesPage } from "../features/commerce/SalesPage";
import { BusinessPage } from "../features/business/BusinessPage";
import { CatalogPage } from "../features/catalog/CatalogPage";
import { HomePage } from "../features/home/HomePage";
import { MessagesPage } from "../features/messages/MessagesPage";
import { PaymentsPage } from "../features/payments/PaymentsPage";
import { PlaygroundPage } from "../features/playground/PlaygroundPage";
import { ProfilePage, ProfileSettingsPage } from "../features/profile/ProfilePage";
import { BillingPage, QuickRepliesPage } from "../features/settings/ComingSoonPages";
import { ReviewPage } from "../features/review/ReviewPage";
import { AppShell } from "../layout/AppShell";
import { SettingsLayout } from "../layout/SettingsLayout";
import { ACCOUNT_PATHS } from "../navigation/accountPaths";
import {
  AI_ITEM,
  ATTENTION_ITEM,
  BILLING_ITEM,
  BUSINESSES_PATH,
  CHANNELS_ITEM,
  CONVERSATIONS_ITEM,
  CUSTOMERS_ITEM,
  ENTRY_PATH,
  NEW_BUSINESS_PATH,
  OVERVIEW_ITEM,
  PLAYGROUND_ITEM,
  PROFILE_SETTINGS_ITEM,
  QUICK_REPLIES_ITEM,
  REPORTS_ITEM,
  REVIEW_ITEM,
  SALES_ITEM,
  SETTINGS_BASE,
  sectionPath,
} from "../navigation/navItems";
import { BusinessWorkspace } from "./BusinessWorkspace";
import { EntryRedirect } from "./EntryRedirect";
import { GuestOnly } from "./GuestOnly";
import { NotFoundPage } from "./NotFoundPage";
import { RequireAuth } from "./RequireAuth";

/**
 * Tabla de rutas: la entrada lleva directo al panel del negocio (o a crear el primero), y cada negocio tiene su espacio de
 * trabajo: atención y ventas arriba, configuración abajo. Las pantallas de cuenta y las guardas de sesión
 * siguen conectadas al contrato `AuthService`: con el acceso local nunca se muestran, porque siempre hay sesión.
 */
export const appRoutes = (
  <>
    <Route element={<GuestOnly />}>
      <Route element={<AuthLayout />}>
        <Route path={ACCOUNT_PATHS.signIn} element={<SignInPage />} />
        <Route path={ACCOUNT_PATHS.signUp} element={<SignUpPage />} />
      </Route>
    </Route>

    <Route element={<RequireAuth />}>
      <Route path={ENTRY_PATH} element={<EntryRedirect />} />
      <Route path={BUSINESSES_PATH} element={<BusinessesPage />} />
      <Route path={NEW_BUSINESS_PATH} element={<WelcomePage />} />
      <Route path={ACCOUNT_PATHS.profile} element={<ProfilePage />} />
      <Route path="/negocios/:slug" element={<BusinessWorkspace />}>
        <Route element={<AppShell />}>
          <Route index element={<HomePage />} />
          <Route path={CONVERSATIONS_ITEM.path} element={<ConversationsPage />} />
          <Route path={CUSTOMERS_ITEM.path} element={<CustomersPage />} />
          <Route path={SALES_ITEM.path} element={<SalesPage />} />
          <Route path={REPORTS_ITEM.path} element={<ReportsPage />} />
          <Route path={CHANNELS_ITEM.path} element={<ChannelsPage />} />
          <Route path={OVERVIEW_ITEM.path} element={<AssistantOverviewPage />} />
          <Route path={sectionPath("business")} element={<BusinessPage />} />
          <Route path={sectionPath("catalog")} element={<CatalogPage />} />
          <Route path={sectionPath("payments")} element={<PaymentsPage />} />
          <Route path={sectionPath("assistant")} element={<AssistantPage />} />
          <Route path={sectionPath("messages")} element={<MessagesPage />} />
          <Route path={REVIEW_ITEM.path} element={<ReviewPage />} />
          <Route element={<SettingsLayout />}>
            <Route path={PROFILE_SETTINGS_ITEM.path} element={<ProfileSettingsPage />} />
            <Route path={AI_ITEM.path} element={<AISettingsPage />} />
            <Route path={ATTENTION_ITEM.path} element={<AttentionSettingsPage />} />
            <Route path={QUICK_REPLIES_ITEM.path} element={<QuickRepliesPage />} />
            <Route path={BILLING_ITEM.path} element={<BillingPage />} />
          </Route>
          <Route path={SETTINGS_BASE} element={<Navigate to={AI_ITEM.path.split("/").pop()!} replace />} />
          {/* Las direcciones de antes de Configuración siguen funcionando. */}
          <Route path="ia" element={<Navigate to={`../${AI_ITEM.path}`} replace />} />
          <Route path="atencion-humana" element={<Navigate to={`../${ATTENTION_ITEM.path}`} replace />} />
          <Route path={PLAYGROUND_ITEM.path} element={<PlaygroundPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Route>
  </>
);
