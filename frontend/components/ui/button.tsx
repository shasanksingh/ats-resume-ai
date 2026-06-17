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
        "inline-flex h-11 items-center justify-center gap-2 rounded-xl px-5 text-sm font-semibold shadow-sm transition duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
        variant === "default" && "bg-zinc-950 text-white hover:-translate-y-0.5 hover:bg-zinc-800 hover:shadow-lg",
        variant === "secondary" && "bg-indigo-600 text-white hover:-translate-y-0.5 hover:bg-indigo-700 hover:shadow-lg",
        variant === "outline" && "border border-zinc-200 bg-white/90 text-zinc-900 hover:-translate-y-0.5 hover:border-indigo-200 hover:bg-indigo-50",
        variant === "ghost" && "text-zinc-700 shadow-none hover:bg-zinc-100",
        className
      )}
      {...props}
    />
  );
}
