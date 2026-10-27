import { Route, Routes } from "react-router-dom";
import { AssistantPage } from "../features/assistant/AssistantPage";
import { AuthLayout } from "../features/auth/AuthLayout";
import { SignInPage } from "../features/auth/SignInPage";
import { SignUpPage } from "../features/auth/SignUpPage";
import { BusinessPage } from "../features/business/BusinessPage";
import { CatalogPage } from "../features/catalog/CatalogPage";
import { HomePage } from "../features/home/HomePage";
import { MessagesPage } from "../features/messages/MessagesPage";
import { PaymentsPage } from "../features/payments/PaymentsPage";
import { ProfilePage } from "../features/profile/ProfilePage";
import { ReviewPage } from "../features/review/ReviewPage";
import { AppShell } from "../layout/AppShell";
import { ACCOUNT_PATHS } from "../navigation/accountPaths";
import { HOME_ITEM, REVIEW_ITEM, sectionPath } from "../navigation/navItems";
import { AccountWorkspace } from "./AccountWorkspace";
import { GuestOnly } from "./GuestOnly";
import { NotFoundPage } from "./NotFoundPage";
import { RequireAuth } from "./RequireAuth";

/** Tabla de rutas: pantallas de cuenta (públicas) y panel (requiere sesión). */
export function AppRoutes() {
  return (
    <Routes>
      <Route element={<GuestOnly />}>
        <Route element={<AuthLayout />}>
          <Route path={ACCOUNT_PATHS.signIn} element={<SignInPage />} />
          <Route path={ACCOUNT_PATHS.signUp} element={<SignUpPage />} />
        </Route>
      </Route>

      <Route element={<RequireAuth />}>
        <Route element={<AccountWorkspace />}>
          <Route element={<AppShell />}>
            <Route path={HOME_ITEM.path} element={<HomePage />} />
            <Route path={sectionPath("business")} element={<BusinessPage />} />
            <Route path={sectionPath("catalog")} element={<CatalogPage />} />
            <Route path={sectionPath("payments")} element={<PaymentsPage />} />
            <Route path={sectionPath("assistant")} element={<AssistantPage />} />
            <Route path={sectionPath("messages")} element={<MessagesPage />} />
            <Route path={REVIEW_ITEM.path} element={<ReviewPage />} />
            <Route path={ACCOUNT_PATHS.profile} element={<ProfilePage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Route>
      </Route>
    </Routes>
  );
}
