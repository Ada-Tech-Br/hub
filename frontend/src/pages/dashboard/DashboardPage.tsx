import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search, SlidersHorizontal, PackageOpen, AlertCircle } from "lucide-react";

import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { ContentCard } from "@/components/shared/ContentCard";
import { Pagination } from "@/components/shared/Pagination";
import { contentService } from "@/services/content.service";
import { useAuthStore } from "@/store/auth.store";
import type { ContentType } from "@/types";
import { useDebounce } from "@/hooks/useDebounce";

const PAGE_SIZE = 12;

export function DashboardPage() {
  const { user } = useAuthStore();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<ContentType | "all">("all");
  const debouncedSearch = useDebounce(search, 400);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["contents", page, debouncedSearch, typeFilter],
    queryFn: () =>
      contentService.list({
        page,
        page_size: PAGE_SIZE,
        search: debouncedSearch || undefined,
        type: typeFilter !== "all" ? typeFilter : undefined,
      }),
  });

  function handleSearchChange(value: string) {
    setSearch(value);
    setPage(1);
  }

  function handleTypeChange(value: string) {
    setTypeFilter(value as ContentType | "all");
    setPage(1);
  }

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold">Olá, {user?.name?.split(" ")[0]} 👋</h1>
        <p className="text-muted-foreground mt-1">Acesse seus projetos e arquivos disponíveis.</p>
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Buscar por nome..."
            value={search}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="pl-9"
            aria-label="Buscar conteúdos"
          />
        </div>
        <div className="flex items-center gap-2">
          <SlidersHorizontal className="h-4 w-4 text-muted-foreground shrink-0" />
          <Select value={typeFilter} onValueChange={handleTypeChange}>
            <SelectTrigger className="w-40" aria-label="Filtrar por tipo">
              <SelectValue placeholder="Tipo" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos os tipos</SelectItem>
              <SelectItem value="project">Projetos</SelectItem>
              <SelectItem value="file">Arquivos</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {isLoading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="space-y-3 rounded-lg border p-4">
              <Skeleton className="h-12 w-12 rounded-xl" />
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-3 w-full" />
              <Skeleton className="h-3 w-2/3" />
              <Skeleton className="h-9 w-full mt-2" />
            </div>
          ))}
        </div>
      )}

      {isError && (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-destructive/10 mb-4">
            <AlertCircle className="h-7 w-7 text-destructive" />
          </div>
          <h3 className="font-semibold text-lg">Erro ao carregar conteúdos</h3>
          <p className="text-muted-foreground text-sm mt-1">Tente novamente em alguns instantes.</p>
        </div>
      )}

      {!isLoading && !isError && data?.items.length === 0 && (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-muted mb-4">
            <PackageOpen className="h-7 w-7 text-muted-foreground" />
          </div>
          <h3 className="font-semibold text-lg">Nenhum conteúdo encontrado</h3>
          <p className="text-muted-foreground text-sm mt-1">
            {search ? "Tente buscar com outros termos." : "Nenhum conteúdo disponível no momento."}
          </p>
          {search && (
            <Button variant="ghost" size="sm" className="mt-4" onClick={() => handleSearchChange("")}>
              Limpar busca
            </Button>
          )}
        </div>
      )}

      {!isLoading && !isError && data && data.items.length > 0 && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {data.items.map((content) => (
              <ContentCard key={content.id} content={content} />
            ))}
          </div>

          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              {data.total} {data.total === 1 ? "item" : "itens"} encontrado{data.total !== 1 ? "s" : ""}
            </p>
            <Pagination
              page={data.page}
              totalPages={data.total_pages}
              onPageChange={setPage}
            />
          </div>
        </>
      )}
    </div>
  );
}
