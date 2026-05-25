import { createFileRoute, Outlet, redirect, useNavigate } from "@tanstack/react-router";
import { AppSidebar } from "@/components/app-sidebar";
import { TopBar } from "@/components/top-bar";
import { MobileBottomNav } from "@/components/mobile-bottom-nav";
import { useEffect } from "react";
import { useAuthStore } from "@/lib/store";
import { notificationsApi } from "@/lib/api";
import { useNotifStore } from "@/lib/store";

export const Route = createFileRoute("/app")({
  beforeLoad: ({ location }) => {
    if (location.pathname === "/app" || location.pathname === "/app/") {
      throw redirect({ to: "/app/dashboard" });
    }
    // Check token in localStorage (works during SSR-like navigation)
    const token = typeof window !== "undefined" ? localStorage.getItem("munai_token") : null;
    if (!token) {
      throw redirect({ to: "/login" });
    }
  },
  component: AppLayout,
});

function AppLayout() {
  const { token } = useAuthStore();
  const nav = useNavigate();
  const { setNotifications } = useNotifStore();

  // Redirect if not authenticated
  useEffect(() => {
    if (!token) nav({ to: "/login" });
  }, [token, nav]);

  // Load notifications on mount
  useEffect(() => {
    if (!token) return;
    notificationsApi.list().then(setNotifications).catch(() => {});
    // Refresh every 30 seconds
    const interval = setInterval(() => {
      notificationsApi.list().then(setNotifications).catch(() => {});
    }, 30000);
    return () => clearInterval(interval);
  }, [token, setNotifications]);

  if (!token) return null;

  return (
    <div className="min-h-screen flex bg-background">
      <AppSidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <TopBar />
        <main className="flex-1 pb-20 md:pb-0">
          <Outlet />
        </main>
        <MobileBottomNav />
      </div>
    </div>
  );
}
