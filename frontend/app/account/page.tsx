"use client";

import { FormEvent, ReactNode, useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, CheckCircle2, Loader2, LockKeyhole, LogOut, UserPlus, UserRound } from "lucide-react";
import { AuthResponse, getMe, login, logout, SESSION_STORAGE_KEY, signup, UserProfile } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Toast } from "@/components/ui/toast";
import { MatchOrbitIcon, ResumePrismIcon } from "@/components/visuals/product-icons";

type Notice = { message: string; tone: "success" | "error" | "info" } | null;

export default function AccountPage() {
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(false);
  const [checking, setChecking] = useState(true);
  const [notice, setNotice] = useState<Notice>(null);

  useEffect(() => {
    void getMe()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setChecking(false));
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setNotice(null);
    try {
      const result = mode === "signup"
        ? await signup(name, email, password)
        : await login(email, password);
      saveSession(result);
      setUser(result.user);
      setPassword("");
      setNotice({ message: mode === "signup" ? "Account created. You can keep using the resume workflow." : "Signed in successfully.", tone: "success" });
    } catch (exc) {
      setNotice({ message: exc instanceof Error ? exc.message : "Account request failed.", tone: "error" });
    } finally {
      setLoading(false);
    }
  }

  async function signOut() {
    setLoading(true);
    try {
      await logout();
    } catch {
      // Local sign-out is still valid if the backend session was already gone.
    } finally {
      localStorage.removeItem(SESSION_STORAGE_KEY);
      setUser(null);
      setLoading(false);
      setNotice({ message: "Signed out locally.", tone: "info" });
    }
  }

  return (
    <main className="relative min-h-[calc(100vh-4rem)] overflow-hidden bg-white">
      <div className="landing-grid absolute inset-0 -z-20" />
      <div className="aurora absolute inset-x-0 top-0 -z-10 h-[520px] opacity-45" />

      <section className="mx-auto grid max-w-7xl gap-8 px-4 py-10 sm:px-6 sm:py-14 lg:grid-cols-[0.9fr_1.1fr] lg:items-start">
        <div className="space-y-6 lg:sticky lg:top-24">
          <div className="inline-flex items-center gap-2 rounded-full border border-indigo-200 bg-white/85 px-3 py-1.5 text-xs font-bold text-indigo-700 shadow-sm">
            <ResumePrismIcon className="h-5 w-5" />
            Optional account
          </div>
          <div>
            <h1 className="max-w-xl text-4xl font-bold tracking-[-0.04em] text-zinc-950 sm:text-5xl">
              Save your workspace identity without blocking analysis.
            </h1>
            <p className="mt-5 max-w-xl text-base leading-8 text-zinc-600">
              Sign in only if you want a local account. Resume upload, ATS scoring, optimization, and exports still work without an account.
            </p>
          </div>

          <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1 xl:grid-cols-3">
            {[
              ["Optional", "Anonymous resume analysis remains available."],
              ["Local SQLite", "Account records stay in the backend data folder."],
              ["No paid auth", "No third-party login provider is required."]
            ].map(([title, copy]) => (
              <div className="reveal-card rounded-2xl border border-zinc-200 bg-white/85 p-4 shadow-sm backdrop-blur" key={title}>
                <CheckCircle2 className="h-6 w-6 text-emerald-600" />
                <p className="mt-4 text-sm font-bold text-zinc-950">{title}</p>
                <p className="mt-1 text-xs leading-5 text-zinc-500">{copy}</p>
              </div>
            ))}
          </div>
        </div>

        <Card className="overflow-hidden bg-white">
          <div className="border-b border-zinc-100 bg-gradient-to-r from-indigo-50 to-cyan-50 px-5 py-4 sm:px-7">
            <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-indigo-600">Profile access</p>
            <h2 className="mt-1 text-lg font-black text-zinc-950">{user ? "Signed-in workspace" : mode === "signup" ? "Create account" : "Sign in"}</h2>
            <p className="mt-1 text-xs leading-5 text-zinc-600">Use the app with or without this account layer.</p>
          </div>
          <CardContent className="space-y-6">
            {checking ? (
              <div className="flex items-center gap-3 rounded-2xl border border-zinc-100 bg-zinc-50 p-5 text-sm text-zinc-600">
                <Loader2 className="h-4 w-4 animate-spin" />
                Checking local session...
              </div>
            ) : user ? (
              <div className="space-y-5">
                <div className="rounded-2xl border border-emerald-100 bg-emerald-50 p-5">
                  <div className="flex items-center gap-3">
                    <div className="grid h-12 w-12 place-items-center rounded-2xl bg-white text-emerald-700 shadow-sm">
                      <UserRound className="h-6 w-6" />
                    </div>
                    <div className="min-w-0">
                      <p className="truncate text-lg font-bold text-zinc-950">{user.name}</p>
                      <p className="truncate text-sm text-zinc-600">{user.email}</p>
                    </div>
                  </div>
                  <p className="mt-4 text-xs leading-5 text-emerald-800">
                    Account created {new Date(user.created_at).toLocaleDateString()}. This sign-in is optional and the resume workflow remains available to guests.
                  </p>
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  <Button asChild variant="secondary" className="justify-center">
                    <Link href="/upload">Upload resume <ArrowRight className="h-4 w-4" /></Link>
                  </Button>
                  <Button variant="outline" onClick={signOut} disabled={loading} className="justify-center">
                    {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <LogOut className="h-4 w-4" />}
                    Sign out
                  </Button>
                </div>
              </div>
            ) : (
              <form className="space-y-4" onSubmit={submit}>
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
                  <Field label="Name">
                    <input className="form-input" value={name} onChange={(event) => setName(event.target.value)} placeholder="Your name" maxLength={120} />
                  </Field>
                ) : null}

                <Field label="Email">
                  <input className="form-input" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@example.com" type="email" autoComplete="email" required />
                </Field>

                <Field label="Password">
                  <input className="form-input" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Minimum 8 characters" type="password" autoComplete={mode === "signup" ? "new-password" : "current-password"} minLength={8} required />
                </Field>

                <Button className="h-12 w-full justify-center" variant="secondary" disabled={loading}>
                  {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : mode === "signup" ? <UserPlus className="h-4 w-4" /> : <LockKeyhole className="h-4 w-4" />}
                  {mode === "signup" ? "Create optional account" : "Sign in"}
                </Button>

                <div className="rounded-2xl border border-indigo-100 bg-indigo-50 p-4">
                  <MatchOrbitIcon className="h-9 w-9" />
                  <p className="mt-3 text-sm font-bold text-indigo-950">Skip sign-in anytime</p>
                  <p className="mt-1 text-xs leading-5 text-indigo-800">The resume workflow stores the current analysis in browser storage for guest users.</p>
                  <Link className="mt-3 inline-flex text-xs font-bold text-indigo-700 hover:text-indigo-900" href="/upload">
                    Continue without account <ArrowRight className="ml-1 h-3.5 w-3.5" />
                  </Link>
                </div>
              </form>
            )}
          </CardContent>
        </Card>
      </section>

      {notice ? <Toast message={notice.message} tone={notice.tone} onClose={() => setNotice(null)} /> : null}
    </main>
  );
}

function saveSession(result: AuthResponse) {
  localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(result));
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block">
      <span className="mb-2 block text-sm font-bold text-zinc-900">{label}</span>
      {children}
    </label>
  );
}
