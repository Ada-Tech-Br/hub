import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  UserPlus, Search, MoreHorizontal, UserCheck, UserX,
  Trash2, Edit, Loader2, Users
} from "lucide-react";
import { toast } from "sonner";
import { formatDate } from "@/lib/utils";
import { getApiErrorMessage } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Skeleton } from "@/components/ui/skeleton";
import { Pagination } from "@/components/shared/Pagination";
import { usersService, type CreateUserData, type UpdateUserData } from "@/services/users.service";
import { useDebounce } from "@/hooks/useDebounce";
import type { User } from "@/types";

const PAGE_SIZE = 15;

const userFormSchema = z.object({
  name: z.string().min(2, "Nome deve ter pelo menos 2 caracteres"),
  email: z.string().email("E-mail inválido"),
  type: z.enum(["internal", "external"]),
  role: z.enum(["admin", "user"]),
  auth_provider: z.enum(["google", "otp"]),
});

type UserForm = z.infer<typeof userFormSchema>;

function UserFormDialog({
  open,
  onClose,
  editUser,
}: {
  open: boolean;
  onClose: () => void;
  editUser: User | null;
}) {
  const queryClient = useQueryClient();
  const isEditing = !!editUser;

  const form = useForm<UserForm>({
    resolver: zodResolver(userFormSchema),
    defaultValues: editUser
      ? {
          name: editUser.name,
          email: editUser.email,
          type: editUser.type,
          role: editUser.role,
          auth_provider: editUser.auth_provider,
        }
      : { type: "external", role: "user", auth_provider: "otp" },
  });

  const mutation = useMutation({
    mutationFn: (data: UserForm) => {
      if (isEditing) return usersService.update(editUser.id, data as UpdateUserData);
      return usersService.create(data as CreateUserData);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      queryClient.invalidateQueries({ queryKey: ["admin-users-summary"] });
      toast.success(isEditing ? "Usuário atualizado!" : "Usuário criado com sucesso!");
      onClose();
      form.reset();
    },
    onError: (error) => toast.error(getApiErrorMessage(error)),
  });

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{isEditing ? "Editar Usuário" : "Novo Usuário"}</DialogTitle>
          <DialogDescription>
            {isEditing ? "Edite os dados do usuário." : "Preencha os dados para criar um novo usuário."}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={form.handleSubmit((d) => mutation.mutate(d))} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Nome completo</Label>
            <Input id="name" placeholder="João Silva" {...form.register("name")} />
            {form.formState.errors.name && (
              <p className="text-xs text-destructive">{form.formState.errors.name.message}</p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="email">E-mail</Label>
            <Input id="email" type="email" placeholder="joao@empresa.com" {...form.register("email")} />
            {form.formState.errors.email && (
              <p className="text-xs text-destructive">{form.formState.errors.email.message}</p>
            )}
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Tipo</Label>
              <Select
                value={form.watch("type")}
                onValueChange={(v) => form.setValue("type", v as "internal" | "external")}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="internal">Interno</SelectItem>
                  <SelectItem value="external">Externo</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Papel</Label>
              <Select
                value={form.watch("role")}
                onValueChange={(v) => form.setValue("role", v as "admin" | "user")}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="user">Usuário</SelectItem>
                  <SelectItem value="admin">Admin</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="space-y-2">
            <Label>Autenticação</Label>
            <Select
              value={form.watch("auth_provider")}
              onValueChange={(v) => form.setValue("auth_provider", v as "google" | "otp")}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="otp">OTP por E-mail</SelectItem>
                <SelectItem value="google">Google OAuth</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <DialogFooter className="gap-2">
            <Button type="button" variant="outline" onClick={onClose}>Cancelar</Button>
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {isEditing ? "Salvar" : "Criar Usuário"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

export function UsersPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [showDialog, setShowDialog] = useState(false);
  const [editUser, setEditUser] = useState<User | null>(null);
  const debouncedSearch = useDebounce(search, 400);
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["admin-users", page, debouncedSearch],
    queryFn: () => usersService.list({ page, page_size: PAGE_SIZE, search: debouncedSearch || undefined }),
  });

  const deleteMutation = useMutation({
    mutationFn: usersService.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      toast.success("Usuário removido");
    },
    onError: (e) => toast.error(getApiErrorMessage(e)),
  });

  const toggleActiveMutation = useMutation({
    mutationFn: ({ id, active }: { id: string; active: boolean }) =>
      active ? usersService.activate(id) : usersService.deactivate(id),
    onSuccess: (_, vars) => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      toast.success(vars.active ? "Usuário ativado" : "Usuário desativado");
    },
    onError: (e) => toast.error(getApiErrorMessage(e)),
  });

  function openCreate() {
    setEditUser(null);
    setShowDialog(true);
  }

  function openEdit(user: User) {
    setEditUser(user);
    setShowDialog(true);
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Usuários</h1>
          <p className="text-muted-foreground text-sm mt-0.5">Gerencie os usuários da plataforma</p>
        </div>
        <Button onClick={openCreate}>
          <UserPlus className="mr-2 h-4 w-4" />
          Novo Usuário
        </Button>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Buscar por nome ou e-mail..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          className="pl-9 max-w-sm"
        />
      </div>

      <div className="rounded-lg border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-muted/50">
            <tr className="border-b">
              <th className="text-left font-medium py-3 px-4">Usuário</th>
              <th className="text-left font-medium py-3 px-4 hidden md:table-cell">Tipo</th>
              <th className="text-left font-medium py-3 px-4 hidden md:table-cell">Papel</th>
              <th className="text-left font-medium py-3 px-4 hidden lg:table-cell">Autenticação</th>
              <th className="text-left font-medium py-3 px-4 hidden lg:table-cell">Criado</th>
              <th className="text-left font-medium py-3 px-4">Status</th>
              <th className="py-3 px-4 w-12"></th>
            </tr>
          </thead>
          <tbody>
            {isLoading &&
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={i} className="border-b">
                  {Array.from({ length: 7 }).map((_, j) => (
                    <td key={j} className="py-3 px-4">
                      <Skeleton className="h-4 w-full max-w-[120px]" />
                    </td>
                  ))}
                </tr>
              ))}

            {!isLoading && data?.items.length === 0 && (
              <tr>
                <td colSpan={7} className="py-16 text-center">
                  <Users className="h-8 w-8 mx-auto text-muted-foreground mb-3" />
                  <p className="text-muted-foreground">Nenhum usuário encontrado</p>
                </td>
              </tr>
            )}

            {!isLoading &&
              data?.items.map((user) => (
                <tr key={user.id} className="border-b hover:bg-muted/30 transition-colors">
                  <td className="py-3 px-4">
                    <div>
                      <p className="font-medium">{user.name}</p>
                      <p className="text-muted-foreground text-xs">{user.email}</p>
                    </div>
                  </td>
                  <td className="py-3 px-4 hidden md:table-cell">
                    <Badge variant="outline" className="text-xs">
                      {user.type === "internal" ? "Interno" : "Externo"}
                    </Badge>
                  </td>
                  <td className="py-3 px-4 hidden md:table-cell">
                    <Badge
                      className="text-xs"
                      variant={user.role === "admin" ? "default" : "secondary"}
                    >
                      {user.role === "admin" ? "Admin" : "Usuário"}
                    </Badge>
                  </td>
                  <td className="py-3 px-4 hidden lg:table-cell text-muted-foreground text-xs capitalize">
                    {user.auth_provider}
                  </td>
                  <td className="py-3 px-4 hidden lg:table-cell text-muted-foreground text-xs">
                    {formatDate(user.created_at)}
                  </td>
                  <td className="py-3 px-4">
                    <Badge variant={user.is_active ? "success" : "warning"} className="text-xs">
                      {user.is_active ? "Ativo" : "Inativo"}
                    </Badge>
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
                        <DropdownMenuItem onClick={() => openEdit(user)}>
                          <Edit className="mr-2 h-4 w-4" />
                          Editar
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() => toggleActiveMutation.mutate({ id: user.id, active: !user.is_active })}
                        >
                          {user.is_active ? (
                            <><UserX className="mr-2 h-4 w-4" />Desativar</>
                          ) : (
                            <><UserCheck className="mr-2 h-4 w-4" />Ativar</>
                          )}
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          className="text-destructive focus:text-destructive"
                          onClick={() => {
                            if (confirm(`Remover ${user.name}?`)) deleteMutation.mutate(user.id);
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
          <p className="text-sm text-muted-foreground">{data.total} usuários no total</p>
          <Pagination page={data.page} totalPages={data.total_pages} onPageChange={setPage} />
        </div>
      )}

      <UserFormDialog
        open={showDialog}
        onClose={() => { setShowDialog(false); setEditUser(null); }}
        editUser={editUser}
      />
    </div>
  );
}
