import { Route } from "react-router-dom";
import { AssistantPage } from "../features/assistant/AssistantPage";
import { AuthLayout } from "../features/auth/AuthLayout";
import { SignInPage } from "../features/auth/SignInPage";
import { SignUpPage } from "../features/auth/SignUpPage";
import { BusinessesPage } from "../features/businesses/BusinessesPage";
import { BusinessPage } from "../features/business/BusinessPage";
import { CatalogPage } from "../features/catalog/CatalogPage";
import { HomePage } from "../features/home/HomePage";
import { MessagesPage } from "../features/messages/MessagesPage";
import { PaymentsPage } from "../features/payments/PaymentsPage";
import { ProfilePage } from "../features/profile/ProfilePage";
import { ReviewPage } from "../features/review/ReviewPage";
import { AppShell } from "../layout/AppShell";
import { ACCOUNT_PATHS } from "../navigation/accountPaths";
import { BUSINESSES_PATH, REVIEW_ITEM, sectionPath } from "../navigation/navItems";
import { BusinessWorkspace } from "./BusinessWorkspace";
import { GuestOnly } from "./GuestOnly";
import { NotFoundPage } from "./NotFoundPage";
import { RequireAuth } from "./RequireAuth";

/**
 * Tabla de rutas: lista de negocios y espacio de trabajo de cada uno. Las pantallas de cuenta y las guardas de sesión
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
      <Route path={BUSINESSES_PATH} element={<BusinessesPage />} />
      <Route path={ACCOUNT_PATHS.profile} element={<ProfilePage />} />
      <Route path="/negocios/:slug" element={<BusinessWorkspace />}>
        <Route element={<AppShell />}>
          <Route index element={<HomePage />} />
          <Route path={sectionPath("business")} element={<BusinessPage />} />
          <Route path={sectionPath("catalog")} element={<CatalogPage />} />
          <Route path={sectionPath("payments")} element={<PaymentsPage />} />
          <Route path={sectionPath("assistant")} element={<AssistantPage />} />
          <Route path={sectionPath("messages")} element={<MessagesPage />} />
          <Route path={REVIEW_ITEM.path} element={<ReviewPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Route>
  </>
);
