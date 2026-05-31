import * as React from "react";
import { cn } from "@/lib/utils";

export function Textarea(props: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      {...props}
      className={cn(
        "min-h-40 w-full resize-y rounded-md border border-zinc-300 bg-white p-3 text-sm outline-none focus:border-emerald-700 focus:ring-2 focus:ring-emerald-100",
        props.className
      )}
    />
  );
}
