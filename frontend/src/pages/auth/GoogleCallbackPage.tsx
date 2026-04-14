import { useEffect, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Loader2, AlertCircle } from "lucide-react";
import { toast } from "sonner";
import { getApiErrorMessage } from "@/lib/api";
import { useAuthStore } from "@/store/auth.store";
import { authService } from "@/services/auth.service";

export function GoogleCallbackPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { setAuth } = useAuthStore();
  const handled = useRef(false);

  useEffect(() => {
    if (handled.current) return;
    handled.current = true;

    const code = searchParams.get("code");
    const error = searchParams.get("error");

    if (error || !code) {
      toast.error(error === "access_denied" ? "Acesso negado pelo Google" : "Autenticação com Google falhou");
      navigate("/login", { replace: true });
      return;
    }

    authService
      .exchangeGoogleCode(code)
      .then((data) => {
        setAuth(data.user, data.access_token, data.refresh_token);
        toast.success(`Bem-vindo, ${data.user.name}!`);
        navigate("/dashboard", { replace: true });
      })
      .catch((error) => {
        toast.error(getApiErrorMessage(error));
        navigate("/login", { replace: true });
      });
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center space-y-4">
        <Loader2 className="h-8 w-8 animate-spin text-primary mx-auto" />
        <p className="text-muted-foreground">Autenticando com Google...</p>
      </div>
    </div>
  );
}
