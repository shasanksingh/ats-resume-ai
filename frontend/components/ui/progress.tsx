import { cn } from "@/lib/utils";

export function Progress({ value, className }: { value: number; className?: string }) {
  return (
    <div className={cn("h-3 w-full overflow-hidden rounded-md bg-zinc-100", className)}>
      <div className="h-full bg-cyan-700 transition-all" style={{ width: `${Math.max(0, Math.min(100, value))}%` }} />
    </div>
  );
}
