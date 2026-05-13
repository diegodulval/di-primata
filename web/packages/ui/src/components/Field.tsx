import { type ReactNode } from "react";
import { cn } from "../lib/cn";

interface FieldProps {
  label: string;
  error?: string | undefined;
  hint?: string;
  className?: string;
  children: ReactNode;
}

function Field({ label, error, hint, className, children }: FieldProps) {
  return (
    <div className={cn("space-y-1", className)}>
      <label className="block text-sm font-medium text-[--color-text-primary]">{label}</label>
      {hint && <p className="text-xs text-[--color-text-muted]">{hint}</p>}
      {children}
      {error && <p className="text-xs text-[--color-error]">{error}</p>}
    </div>
  );
}

export { Field };
