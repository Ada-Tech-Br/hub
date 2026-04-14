import { Outlet, Link, useLocation } from "react-router-dom";
import { Users, FileText, LayoutDashboard, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { Navbar } from "./Navbar";
import { Toaster } from "sonner";

const sidebarItems = [
  { href: "/admin", icon: LayoutDashboard, label: "Visão Geral", exact: true },
  { href: "/admin/users", icon: Users, label: "Usuários" },
  { href: "/admin/content", icon: FileText, label: "Conteúdos" },
];

export function AdminLayout() {
  const location = useLocation();

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <div className="container flex gap-8 py-8">
        <aside className="w-56 shrink-0">
          <nav className="space-y-1">
            {sidebarItems.map((item) => {
              const isActive = item.exact
                ? location.pathname === item.href
                : location.pathname.startsWith(item.href);

              return (
                <Link
                  key={item.href}
                  to={item.href}
                  className={cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                  )}
                >
                  <item.icon className="h-4 w-4" />
                  {item.label}
                  {isActive && <ChevronRight className="ml-auto h-4 w-4" />}
                </Link>
              );
            })}
          </nav>
        </aside>

        <div className="flex-1 min-w-0">
          <Outlet />
        </div>
      </div>
      <Toaster richColors position="top-right" />
    </div>
  );
}
