import { createRootRouteWithContext, Outlet } from "@tanstack/react-router";
import type { QueryClient } from "@tanstack/react-query";
import { ApiUnavailable } from "@di-mata/ui";
import { useApiHealth } from "@di-mata/shared";
import { Skeleton } from "@di-mata/ui";

interface RouterContext {
  queryClient: QueryClient;
}

export const Route = createRootRouteWithContext<RouterContext>()({
  component: RootLayout,
});

function RootLayout() {
  const { status, retry } = useApiHealth();

  if (status === "checking") {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[--color-background]">
        <Skeleton className="h-6 w-32" />
      </main>
    );
  }

  if (status === "unavailable") {
    return <ApiUnavailable onRetry={retry} />;
  }

  return <Outlet />;
}
