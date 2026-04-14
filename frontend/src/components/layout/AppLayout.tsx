import { Outlet } from "react-router-dom";
import { Navbar } from "./Navbar";
import { Toaster } from "sonner";

export function AppLayout() {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container py-8">
        <Outlet />
      </main>
      <Toaster richColors position="top-right" />
    </div>
  );
}
