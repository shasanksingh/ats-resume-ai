"use client";

import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cn } from "@/lib/utils";

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  asChild?: boolean;
  variant?: "default" | "secondary" | "outline" | "ghost";
};

export function Button({ className, variant = "default", asChild, ...props }: ButtonProps) {
  const Comp = asChild ? Slot : "button";
  return (
    <Comp
      className={cn(
        "inline-flex h-10 items-center justify-center gap-2 rounded-md px-4 text-sm font-medium shadow-sm transition-colors disabled:pointer-events-none disabled:opacity-50",
        variant === "default" && "bg-zinc-950 text-white hover:bg-zinc-800",
        variant === "secondary" && "bg-cyan-700 text-white hover:bg-cyan-800",
        variant === "outline" && "border border-zinc-300 bg-white/90 text-zinc-900 hover:bg-white",
        variant === "ghost" && "text-zinc-700 shadow-none hover:bg-white/70",
        className
      )}
      {...props}
    />
  );
}
