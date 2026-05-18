import { useRouteError, isRouteErrorResponse, useNavigate } from "react-router-dom";
import {
  AlertTriangle,
  ArrowLeft,
  Home,
  Lock,
  ServerCrash,
  SearchX,
  WifiOff,
} from "lucide-react";
import { Button } from "@/components/ui/button";

interface ErrorConfig {
  icon: React.ComponentType<{ className?: string }>;
  code: string;
  title: string;
  description: string;
}

function getErrorConfig(error: unknown): ErrorConfig {
  if (isRouteErrorResponse(error)) {
    switch (error.status) {
      case 404:
        return {
          icon: SearchX,
          code: "404",
          title: "Página não encontrada",
          description:
            "A página que você está procurando não existe ou foi movida para outro endereço.",
        };
      case 403:
        return {
          icon: Lock,
          code: "403",
          title: "Acesso negado",
          description:
            "Você não tem permissão para visualizar este conteúdo. Entre em contato com um administrador.",
        };
      case 401:
        return {
          icon: Lock,
          code: "401",
          title: "Não autenticado",
          description:
            "Sua sessão expirou ou você precisa fazer login para acessar esta página.",
        };
      case 500:
        return {
          icon: ServerCrash,
          code: "500",
          title: "Erro interno do servidor",
          description:
            "Ocorreu um erro inesperado no servidor. Tente novamente em alguns instantes.",
        };
      default:
        return {
          icon: AlertTriangle,
          code: String(error.status),
          title: "Algo deu errado",
          description: error.statusText || "Ocorreu um erro inesperado.",
        };
    }
  }

  if (error instanceof Error) {
    const isNetwork =
      error.message.toLowerCase().includes("failed to fetch") ||
      error.message.toLowerCase().includes("networkerror") ||
      error.message.toLowerCase().includes("network error");

    if (isNetwork) {
      return {
        icon: WifiOff,
        code: "–",
        title: "Sem conexão",
        description:
          "Não foi possível conectar ao servidor. Verifique sua conexão e tente novamente.",
      };
    }

    return {
      icon: ServerCrash,
      code: "–",
      title: "Algo deu errado",
      description: "Ocorreu um erro inesperado. Se o problema persistir, contate o suporte.",
    };
  }

  return {
    icon: SearchX,
    code: "404",
    title: "Página não encontrada",
    description:
      "A página que você está procurando não existe ou foi movida para outro endereço.",
  };
}

export function ErrorPage() {
  const error = useRouteError();
  const navigate = useNavigate();
  const config = getErrorConfig(error);
  const Icon = config.icon;

  const is401 = isRouteErrorResponse(error) && error.status === 401;

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-ada-50 to-ada-100 p-4">
      <div className="w-full max-w-md animate-fade-in text-center">
        {/* Brand mark */}
        <div className="mx-auto mb-6 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary shadow-lg">
          <span className="text-2xl font-bold text-primary-foreground">A</span>
        </div>

        {/* Icon card */}
        <div className="relative mx-auto mb-6 flex h-24 w-24 items-center justify-center rounded-3xl bg-white shadow-lg ring-1 ring-border">
          <Icon className="h-10 w-10 text-primary" />
          {config.code !== "–" && (
            <span className="absolute -bottom-3 left-1/2 -translate-x-1/2 rounded-full bg-primary px-2.5 py-0.5 text-xs font-bold text-primary-foreground shadow">
              {config.code}
            </span>
          )}
        </div>

        {/* Text */}
        <h1 className="mb-2 text-2xl font-bold text-foreground">{config.title}</h1>
        <p className="mb-8 text-sm leading-relaxed text-muted-foreground">
          {config.description}
        </p>

        {/* Actions */}
        <div className="flex flex-col gap-3 sm:flex-row sm:justify-center">
          <Button
            variant="outline"
            className="gap-2 bg-white/80 hover:bg-white"
            onClick={() => navigate(-1)}
          >
            <ArrowLeft className="h-4 w-4" />
            Voltar
          </Button>

          {is401 ? (
            <Button className="gap-2" onClick={() => navigate("/login", { replace: true })}>
              <Home className="h-4 w-4" />
              Fazer login
            </Button>
          ) : (
            <Button className="gap-2" onClick={() => navigate("/dashboard", { replace: true })}>
              <Home className="h-4 w-4" />
              Ir para o Dashboard
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
