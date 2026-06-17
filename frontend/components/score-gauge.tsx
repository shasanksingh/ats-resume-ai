import { cn } from "@/lib/utils";

export function ScoreGauge({ value, label = "ATS score", className }: { value: number; label?: string; className?: string }) {
  const score = Math.max(0, Math.min(100, Math.round(value)));
  const radius = 52;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div
      className={cn("group relative mx-auto grid w-fit place-items-center rounded-full transition-transform duration-300 hover:scale-[1.03] focus:scale-[1.03] focus:outline-none", className)}
      role="img"
      aria-label={`${label}: ${score} out of 100`}
      tabIndex={0}
    >
      <svg className="h-36 w-36 -rotate-90" viewBox="0 0 120 120" aria-hidden="true">
        <circle cx="60" cy="60" r={radius} fill="none" stroke="currentColor" strokeWidth="8" className="text-zinc-100" />
        <circle
          cx="60"
          cy="60"
          r={radius}
          fill="none"
          stroke="url(#score-gradient)"
          strokeLinecap="round"
          strokeWidth="8"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-[stroke-dashoffset] duration-1000 ease-out"
        />
        <defs>
          <linearGradient id="score-gradient" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#4f46e5" />
            <stop offset="55%" stopColor="#8b5cf6" />
            <stop offset="100%" stopColor="#06b6d4" />
          </linearGradient>
        </defs>
      </svg>
      <div className="absolute text-center">
        <p className="text-4xl font-bold tracking-tight text-zinc-950">{score}</p>
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-zinc-500">of 100</p>
      </div>
      <span className="pointer-events-none absolute -bottom-8 whitespace-nowrap rounded-lg bg-zinc-950 px-2.5 py-1 text-xs text-white opacity-0 shadow-lg transition group-hover:opacity-100 group-focus:opacity-100">
        {label}
      </span>
    </div>
  );
}
