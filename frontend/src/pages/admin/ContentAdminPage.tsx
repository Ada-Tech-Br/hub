import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  Plus, Search, MoreHorizontal, Trash2, Edit, Loader2,
  FileText, Upload, Code, Globe, Lock, ExternalLink
} from "lucide-react";
import { toast } from "sonner";
import { formatDate } from "@/lib/utils";
import { getApiErrorMessage } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Skeleton } from "@/components/ui/skeleton";
import { Pagination } from "@/components/shared/Pagination";
import { contentService, type CreateContentData } from "@/services/content.service";
import { useDebounce } from "@/hooks/useDebounce";
import type { Content } from "@/types";

const PAGE_SIZE = 15;

const contentSchema = z.object({
  title: z.string().min(1, "Título obrigatório"),
  description: z.string().optional(),
  type: z.enum(["project", "file"]),
  icon: z.string().optional(),
  is_public: z.boolean(),
  external_url: z.string().url("URL inválida").optional().or(z.literal("")),
});

type ContentForm = z.infer<typeof contentSchema>;

function SnippetDialog({ content, onClose }: { content: Content | null; onClose: () => void }) {
  const { data, isLoading } = useQuery({
    queryKey: ["snippet", content?.id],
    queryFn: () => contentService.getSnippet(content!.id),
    enabled: !!content,
  });

  return (
    <Dialog open={!!content} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>Snippet de Acesso Controlado</DialogTitle>
          <DialogDescription>
            Adicione este script ao seu projeto para validar autenticação.
          </DialogDescription>
        </DialogHeader>
        {isLoading && <Skeleton className="h-48" />}
        {data && (
          <div className="space-y-3">
            <pre className="bg-muted rounded-lg p-4 text-xs overflow-auto max-h-72 whitespace-pre-wrap">
              {data.snippet}
            </pre>
            <Button
              size="sm"
              onClick={() => {
                navigator.clipboard.writeText(data.snippet);
                toast.success("Snippet copiado!");
              }}
            >
              Copiar snippet
            </Button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

function ReplaceFileDialog({
  content,
  onClose,
}: {
  content: Content | null;
  onClose: () => void;
}) {
  const queryClient = useQueryClient();
  const [file, setFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);

  const mutation = useMutation({
    mutationFn: () => contentService.uploadFile(content!.id, file!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-contents"] });
      toast.success("Arquivo substituído com sucesso!");
      onClose();
      setFile(null);
    },
    onError: (e) => toast.error(getApiErrorMessage(e)),
  });

  function handleDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragOver(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) setFile(dropped);
  }

  return (
    <Dialog open={!!content} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Substituir Arquivo</DialogTitle>
          <DialogDescription>
            O arquivo atual será substituído. Envie um HTML ou ZIP com index.html.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div
            className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
              dragOver ? "border-primary bg-primary/5" : "hover:border-primary"
            }`}
            onClick={() => document.getElementById("replace-file-input")?.click()}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
          >
            <Upload className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
            {file ? (
              <p className="text-sm font-medium">{file.name}</p>
            ) : (
              <>
                <p className="text-sm font-medium">Clique ou arraste o arquivo</p>
                <p className="text-xs text-muted-foreground mt-1">HTML ou ZIP (máx. 50MB)</p>
              </>
            )}
          </div>
          <input
            id="replace-file-input"
            type="file"
            accept=".html,.htm,.zip"
            className="hidden"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
        </div>
        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={onClose}>Cancelar</Button>
          <Button onClick={() => mutation.mutate()} disabled={!file || mutation.isPending}>
            {mutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Substituir
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function ContentFormDialog({
  open,
  onClose,
  editContent,
}: {
  open: boolean;
  onClose: () => void;
  editContent: Content | null;
}) {
  const queryClient = useQueryClient();
  const isEditing = !!editContent;
  const [file, setFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);

  const form = useForm<ContentForm>({
    resolver: zodResolver(contentSchema),
    defaultValues: editContent
      ? {
          title: editContent.title,
          description: editContent.description ?? "",
          type: editContent.type,
          icon: editContent.icon ?? "",
          is_public: editContent.is_public,
          external_url: editContent.external_url ?? "",
        }
      : { type: "project", is_public: true },
  });

  const contentType = form.watch("type");
  const needsFile = !isEditing && contentType === "file";

  function handleClose() {
    onClose();
    form.reset();
    setFile(null);
  }

  const mutation = useMutation({
    mutationFn: async (data: ContentForm) => {
      const payload: CreateContentData = {
        ...data,
        external_url: data.external_url || undefined,
      };
      if (isEditing) return contentService.update(editContent.id, payload);
      const created = await contentService.create(payload);
      if (file) await contentService.uploadFile(created.id, file);
      return created;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-contents"] });
      queryClient.invalidateQueries({ queryKey: ["admin-contents-summary"] });
      toast.success(isEditing ? "Conteúdo atualizado!" : "Conteúdo criado!");
      handleClose();
    },
    onError: (e) => toast.error(getApiErrorMessage(e)),
  });

  function handleDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragOver(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) setFile(dropped);
  }

  const submitLabel = isEditing ? "Salvar" : contentType === "file" ? "Criar e enviar" : "Criar";

  return (
    <Dialog open={open} onOpenChange={(o) => !o && handleClose()}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{isEditing ? "Editar Conteúdo" : "Novo Conteúdo"}</DialogTitle>
          <DialogDescription>
            {isEditing ? "Edite os dados do conteúdo." : "Adicione um novo projeto ou arquivo."}
          </DialogDescription>
        </DialogHeader>
        <form
          onSubmit={form.handleSubmit((d) => {
            if (needsFile && !file) {
              toast.error("Selecione um arquivo para enviar");
              return;
            }
            mutation.mutate(d);
          })}
          className="space-y-4"
        >
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2 col-span-2">
              <Label>Tipo de conteúdo</Label>
              <Select
                value={form.watch("type")}
                onValueChange={(v) => {
                  form.setValue("type", v as "project" | "file");
                  setFile(null);
                }}
                disabled={isEditing}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="project">Projeto (link externo)</SelectItem>
                  <SelectItem value="file">Arquivo (HTML / ZIP)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2 col-span-2">
              <Label>Título</Label>
              <Input placeholder="Nome do projeto ou arquivo" {...form.register("title")} />
              {form.formState.errors.title && (
                <p className="text-xs text-destructive">{form.formState.errors.title.message}</p>
              )}
            </div>

            <div className="space-y-2 col-span-2">
              <Label>Descrição</Label>
              <Textarea
                placeholder="Descreva brevemente este conteúdo..."
                rows={3}
                {...form.register("description")}
              />
            </div>

            <div className="space-y-2">
              <Label>Ícone (emoji)</Label>
              <Input placeholder="🚀" {...form.register("icon")} />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label>Visibilidade</Label>
                <div className="flex items-center gap-2">
                  <Switch
                    checked={form.watch("is_public")}
                    onCheckedChange={(v) => form.setValue("is_public", v)}
                  />
                  <span className="text-sm text-muted-foreground">
                    {form.watch("is_public") ? "Público" : "Privado"}
                  </span>
                </div>
              </div>
            </div>

            {contentType === "project" && (
              <div className="space-y-2 col-span-2">
                <Label>URL do Projeto</Label>
                <Input
                  type="url"
                  placeholder="https://..."
                  {...form.register("external_url")}
                />
                {form.formState.errors.external_url && (
                  <p className="text-xs text-destructive">{form.formState.errors.external_url.message}</p>
                )}
              </div>
            )}

            {needsFile && (
              <div className="col-span-2">
                <Label className="mb-2 block">Arquivo</Label>
                <div
                  className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
                    dragOver ? "border-primary bg-primary/5" : "hover:border-primary"
                  } ${file ? "border-primary/50" : ""}`}
                  onClick={() => document.getElementById("cf-file-input")?.click()}
                  onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                  onDragLeave={() => setDragOver(false)}
                  onDrop={handleDrop}
                >
                  <Upload className="h-6 w-6 mx-auto text-muted-foreground mb-2" />
                  {file ? (
                    <div>
                      <p className="text-sm font-medium">{file.name}</p>
                      <p className="text-xs text-muted-foreground mt-1">
                        {(file.size / 1024 / 1024).toFixed(2)} MB · clique para trocar
                      </p>
                    </div>
                  ) : (
                    <>
                      <p className="text-sm font-medium">Clique ou arraste o arquivo</p>
                      <p className="text-xs text-muted-foreground mt-1">HTML ou ZIP com index.html (máx. 50MB)</p>
                    </>
                  )}
                </div>
                <input
                  id="cf-file-input"
                  type="file"
                  accept=".html,.htm,.zip"
                  className="hidden"
                  onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                />
              </div>
            )}
          </div>

          <DialogFooter className="gap-2">
            <Button type="button" variant="outline" onClick={handleClose}>Cancelar</Button>
            <Button type="submit" disabled={mutation.isPending || (needsFile && !file)}>
              {mutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {submitLabel}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

export function ContentAdminPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [showDialog, setShowDialog] = useState(false);
  const [editContent, setEditContent] = useState<Content | null>(null);
  const [uploadContent, setUploadContent] = useState<Content | null>(null);
  const [snippetContent, setSnippetContent] = useState<Content | null>(null);
  const debouncedSearch = useDebounce(search, 400);
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["admin-contents", page, debouncedSearch],
    queryFn: () =>
      contentService.list({ page, page_size: PAGE_SIZE, search: debouncedSearch || undefined }),
  });

  const deleteMutation = useMutation({
    mutationFn: contentService.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-contents"] });
      toast.success("Conteúdo removido");
    },
    onError: (e) => toast.error(getApiErrorMessage(e)),
  });

  function openCreate() {
    setEditContent(null);
    setShowDialog(true);
  }

  function openEdit(content: Content) {
    setEditContent(content);
    setShowDialog(true);
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Conteúdos</h1>
          <p className="text-muted-foreground text-sm mt-0.5">Gerencie projetos e arquivos</p>
        </div>
        <Button onClick={openCreate}>
          <Plus className="mr-2 h-4 w-4" />
          Novo Conteúdo
        </Button>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Buscar por título..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          className="pl-9 max-w-sm"
        />
      </div>

      <div className="rounded-lg border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-muted/50">
            <tr className="border-b">
              <th className="text-left font-medium py-3 px-4">Título</th>
              <th className="text-left font-medium py-3 px-4 hidden sm:table-cell">Tipo</th>
              <th className="text-left font-medium py-3 px-4 hidden md:table-cell">Visibilidade</th>
              <th className="text-left font-medium py-3 px-4 hidden lg:table-cell">S3 / URL</th>
              <th className="text-left font-medium py-3 px-4 hidden lg:table-cell">Criado</th>
              <th className="py-3 px-4 w-12"></th>
            </tr>
          </thead>
          <tbody>
            {isLoading &&
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={i} className="border-b">
                  {Array.from({ length: 6 }).map((_, j) => (
                    <td key={j} className="py-3 px-4">
                      <Skeleton className="h-4 w-full max-w-[120px]" />
                    </td>
                  ))}
                </tr>
              ))}

            {!isLoading && data?.items.length === 0 && (
              <tr>
                <td colSpan={6} className="py-16 text-center">
                  <FileText className="h-8 w-8 mx-auto text-muted-foreground mb-3" />
                  <p className="text-muted-foreground">Nenhum conteúdo encontrado</p>
                </td>
              </tr>
            )}

            {!isLoading &&
              data?.items.map((content) => (
                <tr key={content.id} className="border-b hover:bg-muted/30 transition-colors">
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      {content.icon && <span>{content.icon}</span>}
                      <p className="font-medium">{content.title}</p>
                    </div>
                    {content.description && (
                      <p className="text-xs text-muted-foreground mt-0.5 line-clamp-1">{content.description}</p>
                    )}
                  </td>
                  <td className="py-3 px-4 hidden sm:table-cell">
                    <Badge variant="outline" className="text-xs capitalize">
                      {content.type === "project" ? "Projeto" : `Arquivo ${content.file_type?.toUpperCase() ?? ""}`}
                    </Badge>
                  </td>
                  <td className="py-3 px-4 hidden md:table-cell">
                    {content.is_public ? (
                      <Badge variant="success" className="text-xs gap-1">
                        <Globe className="h-3 w-3" />Público
                      </Badge>
                    ) : (
                      <Badge variant="warning" className="text-xs gap-1">
                        <Lock className="h-3 w-3" />Privado
                      </Badge>
                    )}
                  </td>
                  <td className="py-3 px-4 hidden lg:table-cell text-muted-foreground text-xs max-w-[200px]">
                    <span className="truncate block">
                      {content.s3_path || content.external_url || "—"}
                    </span>
                  </td>
                  <td className="py-3 px-4 hidden lg:table-cell text-muted-foreground text-xs">
                    {formatDate(content.created_at)}
                  </td>
                  <td className="py-3 px-4">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon" className="h-8 w-8">
                          <MoreHorizontal className="h-4 w-4" />
                          <span className="sr-only">Ações</span>
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => openEdit(content as unknown as Content)}>
                          <Edit className="mr-2 h-4 w-4" />
                          Editar
                        </DropdownMenuItem>
                        {content.type === "file" && (
                          <DropdownMenuItem onClick={() => setUploadContent(content as unknown as Content)}>
                            <Upload className="mr-2 h-4 w-4" />
                            Substituir arquivo
                          </DropdownMenuItem>
                        )}
                        {content.type === "project" && !content.is_public && (
                          <DropdownMenuItem onClick={() => setSnippetContent(content as unknown as Content)}>
                            <Code className="mr-2 h-4 w-4" />
                            Gerar snippet
                          </DropdownMenuItem>
                        )}
                        {content.external_url && (
                          <DropdownMenuItem asChild>
                            <a href={content.external_url} target="_blank" rel="noopener noreferrer">
                              <ExternalLink className="mr-2 h-4 w-4" />
                              Abrir URL
                            </a>
                          </DropdownMenuItem>
                        )}
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          className="text-destructive focus:text-destructive"
                          onClick={() => {
                            if (confirm(`Remover "${content.title}"?`)) deleteMutation.mutate(content.id);
                          }}
                        >
                          <Trash2 className="mr-2 h-4 w-4" />
                          Remover
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      {data && data.total_pages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">{data.total} conteúdos no total</p>
          <Pagination page={data.page} totalPages={data.total_pages} onPageChange={setPage} />
        </div>
      )}

      <ContentFormDialog
        open={showDialog}
        onClose={() => { setShowDialog(false); setEditContent(null); }}
        editContent={editContent}
      />
      <ReplaceFileDialog content={uploadContent} onClose={() => setUploadContent(null)} />
      <SnippetDialog content={snippetContent} onClose={() => setSnippetContent(null)} />
    </div>
  );
}
