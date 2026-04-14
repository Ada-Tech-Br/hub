import { useQuery } from "@tanstack/react-query";
import { Users, FileText } from "lucide-react";
import { Link } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { usersService } from "@/services/users.service";
import { contentService } from "@/services/content.service";

export function AdminOverviewPage() {
  const { data: usersData, isLoading: loadingUsers } = useQuery({
    queryKey: ["admin-users-summary"],
    queryFn: () => usersService.list({ page_size: 1 }),
  });

  const { data: contentsData, isLoading: loadingContents } = useQuery({
    queryKey: ["admin-contents-summary"],
    queryFn: () => contentService.list({ page_size: 1 }),
  });

  const stats = [
    {
      label: "Total de Usuários",
      value: usersData?.total,
      icon: Users,
      href: "/admin/users",
      color: "text-blue-600",
      bg: "bg-blue-50",
    },
    {
      label: "Total de Conteúdos",
      value: contentsData?.total,
      icon: FileText,
      href: "/admin/content",
      color: "text-purple-600",
      bg: "bg-purple-50",
    },
  ];

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold">Visão Geral</h1>
        <p className="text-muted-foreground mt-1">Resumo da plataforma Ada</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {stats.map((stat) => (
          <Card key={stat.label} className="hover:shadow-md transition-shadow">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardDescription>{stat.label}</CardDescription>
                <div className={`flex h-9 w-9 items-center justify-center rounded-lg ${stat.bg}`}>
                  <stat.icon className={`h-5 w-5 ${stat.color}`} />
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {loadingUsers || loadingContents ? (
                <Skeleton className="h-8 w-16" />
              ) : (
                <div className="flex items-end justify-between">
                  <span className="text-3xl font-bold">{stat.value ?? "—"}</span>
                  <Button variant="link" size="sm" className="text-xs" asChild>
                    <Link to={stat.href}>Ver todos →</Link>
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Gestão de Usuários</CardTitle>
            <CardDescription>Crie, edite e gerencie usuários da plataforma</CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild>
              <Link to="/admin/users">
                <Users className="mr-2 h-4 w-4" />
                Gerenciar Usuários
              </Link>
            </Button>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Gestão de Conteúdos</CardTitle>
            <CardDescription>Adicione projetos e faça upload de arquivos</CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild>
              <Link to="/admin/content">
                <FileText className="mr-2 h-4 w-4" />
                Gerenciar Conteúdos
              </Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
