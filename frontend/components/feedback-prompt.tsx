"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { MessageSquareHeart, Send, Star, X } from "lucide-react";
import { FEEDBACK_SUBMITTED_STORAGE_KEY, submitFeedback } from "@/lib/api";
import { Button } from "@/components/ui/button";

export function FeedbackPrompt() {
  const pathname = usePathname();
  const [visible, setVisible] = useState(false);
  const [rating, setRating] = useState(5);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (pathname !== "/results") {
      setVisible(false);
      return;
    }
    if (localStorage.getItem(FEEDBACK_SUBMITTED_STORAGE_KEY) === "1") return;
    const timer = window.setTimeout(() => setVisible(true), 1800);
    return () => window.clearTimeout(timer);
  }, [pathname]);

  if (!visible) return null;

  async function submit() {
    setLoading(true);
    setError("");
    try {
      await submitFeedback(rating, message, pathname);
      localStorage.setItem(FEEDBACK_SUBMITTED_STORAGE_KEY, "1");
      setSaved(true);
      window.setTimeout(() => setVisible(false), 1200);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Could not save feedback.");
    } finally {
      setLoading(false);
    }
  }

  function close() {
    setVisible(false);
  }

  return (
    <div className="fixed inset-x-3 bottom-3 z-50 mx-auto max-w-md rounded-3xl border border-zinc-200 bg-white p-4 shadow-2xl shadow-zinc-950/15 sm:bottom-5 sm:right-5 sm:mx-0" role="dialog" aria-label="Feedback">
      <div className="flex items-start justify-between gap-3">
        <div className="flex gap-3">
          <div className="grid h-10 w-10 shrink-0 place-items-center rounded-2xl bg-indigo-50 text-indigo-700">
            <MessageSquareHeart className="h-5 w-5" />
          </div>
          <div>
            <p className="text-sm font-black text-zinc-950">How was your resume review?</p>
            <p className="mt-1 text-xs leading-5 text-zinc-500">Your feedback is stored locally with this workspace.</p>
          </div>
        </div>
        <button className="rounded-full p-1.5 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-700" type="button" onClick={close} aria-label="Close feedback">
          <X className="h-4 w-4" />
        </button>
      </div>

      {saved ? (
        <p className="mt-4 rounded-2xl bg-emerald-50 p-3 text-sm font-semibold text-emerald-800">Thanks. Feedback saved.</p>
      ) : (
        <div className="mt-4 space-y-3">
          <div>
            <div className="mb-2 flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-[0.14em] text-zinc-500">Rating</span>
              <span className="text-xs font-semibold text-indigo-700">{rating}/5</span>
            </div>
            <div className="grid grid-cols-5 gap-2" aria-label="Rating">
            {[1, 2, 3, 4, 5].map((value) => (
              <button
                className={`grid h-11 place-items-center rounded-2xl border transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 ${
                  rating >= value
                    ? "border-amber-300 bg-amber-50 text-amber-500 shadow-sm"
                    : "border-zinc-200 bg-white text-zinc-300 hover:border-indigo-200 hover:bg-indigo-50 hover:text-indigo-500"
                }`}
                key={value}
                onClick={() => setRating(value)}
                type="button"
                aria-pressed={rating >= value}
                aria-label={`${value} star rating`}
              >
                <Star className={`h-5 w-5 ${rating >= value ? "fill-current" : ""}`} />
              </button>
            ))}
            </div>
          </div>
          <textarea
            className="form-input min-h-20 resize-none"
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            placeholder="Tell us what felt good or what should improve..."
            maxLength={2000}
          />
          {error ? <p className="rounded-xl border border-red-200 bg-red-50 p-3 text-xs leading-5 text-red-700">{error}</p> : null}
          <div className="flex flex-col gap-2 sm:flex-row">
            <Button className="h-10 flex-1 justify-center" variant="secondary" onClick={submit} disabled={loading}>
              <Send className="h-4 w-4" />
              {loading ? "Saving..." : "Send feedback"}
            </Button>
            <Button className="h-10 justify-center" variant="outline" onClick={close} type="button">
              Later
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
