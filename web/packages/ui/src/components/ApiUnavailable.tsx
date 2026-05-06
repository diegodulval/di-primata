interface ApiUnavailableProps {
  onRetry?: () => void;
}

export function ApiUnavailable({ onRetry }: ApiUnavailableProps) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[--color-background] p-6">
      <div className="text-center max-w-sm space-y-4">
        <div className="text-5xl">⚠️</div>
        <h1 className="text-xl font-semibold text-[--color-text-primary]">
          Serviço temporariamente indisponível
        </h1>
        <p className="text-sm text-[--color-text-muted]">
          Não foi possível conectar ao servidor. Tente novamente em instantes.
        </p>
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="mt-2 rounded-md bg-[--color-primary] px-4 py-2 text-sm font-medium text-[--color-primary-fg] hover:opacity-90 transition-opacity"
          >
            Tentar novamente
          </button>
        )}
      </div>
    </main>
  );
}
