"use client";

import { CheckCircle2, CircleAlert, X } from "lucide-react";

type ToastProps = {
  message: string;
  tone?: "success" | "error" | "info";
  onClose: () => void;
};

export function Toast({ message, tone = "success", onClose }: ToastProps) {
  const Icon = tone === "success" ? CheckCircle2 : CircleAlert;
  const iconTone = tone === "success" ? "text-emerald-600" : tone === "error" ? "text-red-600" : "text-indigo-600";

  return (
    <div
      className="fixed bottom-5 right-5 z-50 flex max-w-sm items-start gap-3 rounded-2xl border border-zinc-200 bg-white p-4 text-sm text-zinc-700 shadow-2xl"
      role={tone === "error" ? "alert" : "status"}
      aria-live="polite"
    >
      <Icon className={`mt-0.5 h-5 w-5 shrink-0 ${iconTone}`} />
      <p className="leading-5">{message}</p>
      <button className="rounded-md p-1 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-700" onClick={onClose} aria-label="Dismiss notification">
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}
