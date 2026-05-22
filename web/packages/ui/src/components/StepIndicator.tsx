import { cn } from "../lib/cn";

interface StepIndicatorProps {
  current: number;
  total: number;
  className?: string;
}

function StepIndicator({ current, total, className }: StepIndicatorProps) {
  return (
    <div className={cn("flex items-center gap-2", className)}>
      {Array.from({ length: total }, (_, i) => (
        <div key={i} className="flex items-center gap-2">
          <div
            className={cn(
              "w-7 h-7 rounded-full flex items-center justify-center text-xs font-medium transition-colors",
              i < current
                ? "bg-[--color-primary] text-[--color-primary-fg]"
                : i === current
                  ? "bg-[--color-primary] text-[--color-primary-fg] ring-2 ring-[--color-primary] ring-offset-2 ring-offset-[--color-background]"
                  : "bg-[--color-border] text-[--color-text-muted]"
            )}
          >
            {i < current ? "✓" : i + 1}
          </div>
          {i < total - 1 && (
            <div
              className={cn(
                "h-px w-8",
                i < current ? "bg-[--color-primary]" : "bg-[--color-border]"
              )}
            />
          )}
        </div>
      ))}
    </div>
  );
}

export { StepIndicator };
