import { cva, type VariantProps } from "class-variance-authority";
import { type SelectHTMLAttributes, forwardRef } from "react";
import { cn } from "../lib/cn";

const selectVariants = cva(
  [
    "w-full border border-[--color-border] bg-[--color-surface] text-sm text-[--color-text-primary]",
    "focus:outline-none focus:ring-2 focus:ring-[--color-primary] focus:border-transparent",
    "disabled:opacity-50 disabled:cursor-not-allowed",
  ].join(" "),
  {
    variants: {
      // Renamed to avoid conflict with the native HTML `size` attribute (number)
      selectSize: {
        sm: "rounded-md px-3 py-2",
        md: "rounded-lg px-4 py-3",
      },
    },
    defaultVariants: {
      selectSize: "sm",
    },
  }
);

interface SelectProps
  extends SelectHTMLAttributes<HTMLSelectElement>,
    VariantProps<typeof selectVariants> {}

const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, selectSize, ...props }, ref) => (
    <select
      ref={ref}
      className={cn(selectVariants({ selectSize, className }))}
      {...props}
    />
  )
);

Select.displayName = "Select";

export { Select, selectVariants };
