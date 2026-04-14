import { useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ExternalLink, Loader2, ArrowLeft, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { contentService } from "@/services/content.service";
import { getApiErrorMessage } from "@/lib/api";

export function ContentViewerPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const openedRef = useRef(false);

  const { data: access, isLoading, isError, error } = useQuery({
    queryKey: ["content-access", id],
    queryFn: () => contentService.getAccess(id!),
    enabled: !!id,
    retry: false,
  });

  useEffect(() => {
    if (!access || access.type !== "project" || openedRef.current) return;
    openedRef.current = true;

    // Abre o projeto em nova aba para não abandonar a SPA
    window.open(access.access_url, "_blank", "noopener,noreferrer");

    // Volta para o dashboard — o usuário nunca "sai" da plataforma
    navigate("/dashboard", { replace: true });
  }, [access, navigate]);

  if (isLoading) {
    return (
      <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center">
        <div className="text-center space-y-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary mx-auto" />
          <p className="text-muted-foreground">Carregando conteúdo...</p>
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center">
        <div className="text-center space-y-4 max-w-sm">
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-destructive/10 mx-auto">
            <AlertCircle className="h-7 w-7 text-destructive" />
          </div>
          <h2 className="text-xl font-semibold">Acesso negado</h2>
          <p className="text-muted-foreground text-sm">{getApiErrorMessage(error)}</p>
          <Button onClick={() => navigate("/dashboard")} variant="outline">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Voltar ao dashboard
          </Button>
        </div>
      </div>
    );
  }

  if (!access || access.type === "project") return null;

  return (
    <div className="space-y-4 -mx-4 -my-8 sm:-mx-8">
      <div className="flex items-center gap-2 px-4 py-2 border-b bg-background sticky top-16 z-10">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate("/dashboard")}
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Voltar
        </Button>
        <div className="flex-1" />
        <Button variant="outline" size="sm" asChild>
          <a href={access.access_url} target="_blank" rel="noopener noreferrer">
            <ExternalLink className="mr-2 h-4 w-4" />
            Abrir em nova aba
          </a>
        </Button>
      </div>

      <iframe
        src={access.access_url}
        className="w-full border-0"
        style={{ height: "calc(100vh - 8rem)" }}
        title="Conteúdo"
        sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
        loading="lazy"
      />
    </div>
  );
}
