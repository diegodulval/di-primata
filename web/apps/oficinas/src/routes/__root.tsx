import { ApiUnavailable, Skeleton } from "@di-mata/ui";
import type { QueryClient } from "@tanstack/react-query";
import { Outlet, createRootRouteWithContext } from "@tanstack/react-router";
import { useEffect, useState } from "react";

interface RouterContext {
  queryClient: QueryClient;
}

export const Route = createRootRouteWithContext<RouterContext>()({
  component: RootLayout,
});

function RootLayout() {
  const [status, setStatus] = useState<"checking" | "ok" | "unavailable">("checking");

  useEffect(() => {
    let cancelled = false;
    fetch("/api/health", { signal: AbortSignal.timeout(5000) })
      .then((r) => {
        if (!cancelled) setStatus(r.ok ? "ok" : "unavailable");
      })
      .catch(() => {
        if (!cancelled) setStatus("unavailable");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (status === "checking") {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[var(--color-background)]">
        <Skeleton className="h-6 w-32" />
      </main>
    );
  }

  if (status === "unavailable") {
    return <ApiUnavailable onRetry={() => setStatus("checking")} />;
  }

  return <Outlet />;
}
