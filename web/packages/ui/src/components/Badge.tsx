import { cva, type VariantProps } from "class-variance-authority";
import { type HTMLAttributes } from "react";
import { cn } from "../lib/cn";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors",
  {
    variants: {
      variant: {
        default: "border-transparent bg-[var(--color-primary)] text-[var(--color-primary-fg)]",
        secondary: "border-transparent bg-[var(--color-background)] text-[--color-text-secondary]",
        outline: "border-[--color-border] text-[--color-text-primary]",
        success: "border-transparent bg-[var(--color-success)] text-[var(--color-success-fg)]",
        warning: "border-transparent bg-[var(--color-warning)] text-[var(--color-warning-fg)]",
        error: "border-transparent bg-[var(--color-error)] text-[var(--color-error-fg)]",
      },
    },
    defaultVariants: { variant: "default" },
  }
);

interface BadgeProps extends HTMLAttributes<HTMLDivElement>, VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { Badge, badgeVariants };
