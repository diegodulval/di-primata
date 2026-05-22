import { cva, type VariantProps } from "class-variance-authority";
import { type InputHTMLAttributes, forwardRef } from "react";
import { cn } from "../lib/cn";

const inputVariants = cva(
  [
    "w-full border border-[--color-border] text-sm text-[--color-text-primary]",
    "placeholder:text-[--color-text-muted]",
    "focus:outline-none focus:ring-2 focus:ring-[--color-primary] focus:border-transparent",
    "disabled:opacity-50 disabled:cursor-not-allowed",
  ].join(" "),
  {
    variants: {
      // Renamed to avoid conflict with the native HTML `size` attribute (number)
      inputSize: {
        sm: "rounded-md bg-[--color-surface] px-3 py-2",
        md: "rounded-lg bg-[--color-background] px-4 py-3",
      },
      state: {
        default: "",
        error: "border-[--color-error] focus:ring-[--color-error]",
      },
    },
    defaultVariants: {
      inputSize: "sm",
      state: "default",
    },
  }
);

interface InputProps
  extends InputHTMLAttributes<HTMLInputElement>,
    VariantProps<typeof inputVariants> {}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, inputSize, state, ...props }, ref) => (
    <input ref={ref} className={cn(inputVariants({ inputSize, state, className }))} {...props} />
  )
);

Input.displayName = "Input";

export { Input, inputVariants };
