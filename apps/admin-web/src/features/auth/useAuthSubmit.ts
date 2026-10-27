import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { authErrorMessage } from "../../domain/auth/messages";
import { redirectTarget } from "../../navigation/accountPaths";

/** Envío de un formulario de cuenta: estado de carga, error general y redirección al terminar. */
export function useAuthSubmit() {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const location = useLocation();

  const submit = async (action: () => Promise<void>) => {
    setPending(true);
    setError(null);
    try {
      await action();
      navigate(redirectTarget(location.state), { replace: true });
    } catch (caught) {
      setError(authErrorMessage(caught));
      setPending(false);
    }
  };

  return { pending, error, submit };
}
