import { createRootRoute, Outlet } from "@tanstack/react-router";
import { ApiUnavailable } from "@di-mata/ui";
import { useApiHealth } from "@di-mata/shared";

export const Route = createRootRoute({
  component: RootLayout,
});

function RootLayout() {
  const { status, retry } = useApiHealth();

  if (status === "unavailable") {
    return <ApiUnavailable onRetry={retry} />;
  }

  // Em "checking" deixa renderizar normalmente — o portal tem skeleton por rota
  return <Outlet />;
}
