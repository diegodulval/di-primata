import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { type ButtonHTMLAttributes, forwardRef } from "react";
import { cn } from "../lib/cn";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default:
          "bg-[--color-primary] text-[--color-primary-fg] hover:opacity-90 focus-visible:ring-[--color-primary]",
        outline:
          "border border-[--color-border] bg-[--color-surface] hover:bg-[--color-background] text-[--color-text-primary]",
        ghost:
          "hover:bg-[--color-background] text-[--color-text-primary]",
        destructive:
          "bg-[--color-error] text-white hover:opacity-90",
        link: "text-[--color-primary] underline-offset-4 hover:underline",
      },
      size: {
        sm: "h-8 rounded px-3 text-xs",
        md: "h-10 px-4 py-2",
        lg: "h-12 rounded-lg px-8 text-base",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "md",
    },
  }
);

interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);

Button.displayName = "Button";

export { Button, buttonVariants };
