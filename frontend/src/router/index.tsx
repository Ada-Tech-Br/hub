import { createBrowserRouter, Navigate } from "react-router-dom";
import { LoginPage } from "@/pages/auth/LoginPage";
import { GoogleCallbackPage } from "@/pages/auth/GoogleCallbackPage";
import { DashboardPage } from "@/pages/dashboard/DashboardPage";
import { ContentViewerPage } from "@/pages/dashboard/ContentViewerPage";
import { AdminOverviewPage } from "@/pages/admin/AdminOverviewPage";
import { UsersPage } from "@/pages/admin/UsersPage";
import { ContentAdminPage } from "@/pages/admin/ContentAdminPage";
import { AppLayout } from "@/components/layout/AppLayout";
import { AdminLayout } from "@/components/layout/AdminLayout";
import { ProtectedRoute } from "./ProtectedRoute";

export const router = createBrowserRouter([
  {
    path: "/login",
    element: <LoginPage />,
  },
  {
    path: "/oauth/callback",
    element: <GoogleCallbackPage />,
  },
  {
    path: "/",
    element: (
      <ProtectedRoute>
        <AppLayout />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: <Navigate to="/dashboard" replace />,
      },
      {
        path: "dashboard",
        element: <DashboardPage />,
      },
      {
        path: "content/:id",
        element: <ContentViewerPage />,
      },
    ],
  },
  {
    path: "/admin",
    element: (
      <ProtectedRoute requireAdmin>
        <AdminLayout />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: <AdminOverviewPage />,
      },
      {
        path: "users",
        element: <UsersPage />,
      },
      {
        path: "content",
        element: <ContentAdminPage />,
      },
    ],
  },
  {
    path: "*",
    element: <Navigate to="/dashboard" replace />,
  },
]);
