import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/")({
  component: () => (
    <main className="flex min-h-screen items-center justify-center p-6">
      <p className="text-[--color-text-muted] text-sm">
        Acesse um produto via QR code para ver sua rastreabilidade.
      </p>
    </main>
  ),
});
