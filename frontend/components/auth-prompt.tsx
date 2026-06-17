"use client";

import { FormEvent, useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { ArrowRight, Check, Loader2, LockKeyhole, UserPlus, X } from "lucide-react";
import { AUTH_SKIP_STORAGE_KEY, AuthResponse, login, SESSION_STORAGE_KEY, signup } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { ResumePrismIcon } from "@/components/visuals/product-icons";

type Mode = "login" | "signup";

export function AuthPrompt() {
  const pathname = usePathname();
  const [visible, setVisible] = useState(false);
  const [mode, setMode] = useState<Mode>("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (pathname === "/account") {
      setVisible(false);
      return;
    }
    const hasSession = Boolean(localStorage.getItem(SESSION_STORAGE_KEY));
    const skipped = localStorage.getItem(AUTH_SKIP_STORAGE_KEY) === "1";
    setVisible(!hasSession && !skipped);
  }, [pathname]);

  if (!visible) return null;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const result = mode === "signup"
        ? await signup(name, email, password)
        : await login(email, password);
      saveSession(result);
      setVisible(false);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Account request failed.");
    } finally {
      setLoading(false);
    }
  }

  function skip() {
    localStorage.setItem(AUTH_SKIP_STORAGE_KEY, "1");
    setVisible(false);
  }

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-white/55 p-4 backdrop-blur-md" role="dialog" aria-modal="true" aria-labelledby="auth-prompt-title">
      <div className="relative w-full max-w-md overflow-hidden rounded-[1.75rem] border border-white/80 bg-white shadow-2xl shadow-indigo-950/20">
        <button
          className="absolute right-4 top-4 rounded-full p-2 text-zinc-400 transition hover:bg-zinc-100 hover:text-zinc-700"
          onClick={skip}
          aria-label="Close sign-in prompt"
          type="button"
        >
          <X className="h-4 w-4" />
        </button>

        <div className="border-b border-zinc-100 bg-gradient-to-br from-indigo-50 to-cyan-50 px-5 py-5">
          <ResumePrismIcon className="h-12 w-12" />
          <p className="mt-4 text-xs font-bold uppercase tracking-[0.18em] text-indigo-600">Optional account</p>
          <h2 id="auth-prompt-title" className="mt-2 text-2xl font-black tracking-tight text-zinc-950">
            Save your workspace or continue as guest.
          </h2>
          <p className="mt-2 text-sm leading-6 text-zinc-600">
            Sign in to keep a local profile. Resume upload, analysis, and exports still work without an account.
          </p>
        </div>

        <form className="space-y-4 p-5" onSubmit={submit}>
          <div className="grid grid-cols-2 gap-2 rounded-2xl bg-zinc-100 p-1">
            <button
              type="button"
              className={`rounded-xl px-3 py-2 text-sm font-bold transition ${mode === "login" ? "bg-white text-zinc-950 shadow-sm" : "text-zinc-500"}`}
              onClick={() => setMode("login")}
            >
              Login
            </button>
            <button
              type="button"
              className={`rounded-xl px-3 py-2 text-sm font-bold transition ${mode === "signup" ? "bg-white text-zinc-950 shadow-sm" : "text-zinc-500"}`}
              onClick={() => setMode("signup")}
            >
              Signup
            </button>
          </div>

          {mode === "signup" ? (
            <label className="block">
              <span className="mb-2 block text-sm font-bold text-zinc-900">Name</span>
              <input className="form-input" value={name} onChange={(event) => setName(event.target.value)} placeholder="Your name" maxLength={120} />
            </label>
          ) : null}

          <label className="block">
            <span className="mb-2 block text-sm font-bold text-zinc-900">Email</span>
            <input className="form-input" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@example.com" type="email" autoComplete="email" required />
          </label>

          <label className="block">
            <span className="mb-2 block text-sm font-bold text-zinc-900">Password</span>
            <input className="form-input" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Minimum 8 characters" type="password" autoComplete={mode === "signup" ? "new-password" : "current-password"} minLength={8} required />
          </label>

          {error ? <p className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm leading-6 text-red-700">{error}</p> : null}

          <div className="grid gap-2 sm:grid-cols-2">
            <Button className="h-11 justify-center" variant="secondary" disabled={loading}>
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : mode === "signup" ? <UserPlus className="h-4 w-4" /> : <LockKeyhole className="h-4 w-4" />}
              {mode === "signup" ? "Create account" : "Sign in"}
            </Button>
            <Button type="button" className="h-11 justify-center" variant="outline" onClick={skip}>
              <Check className="h-4 w-4" />
              Use without account
            </Button>
          </div>

          <button type="button" className="inline-flex items-center text-xs font-bold text-indigo-700 hover:text-indigo-900" onClick={skip}>
            Skip sign-in for now <ArrowRight className="ml-1 h-3.5 w-3.5" />
          </button>
        </form>
      </div>
    </div>
  );
}

function saveSession(result: AuthResponse) {
  localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(result));
  localStorage.removeItem(AUTH_SKIP_STORAGE_KEY);
}
