"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ArrowUpRight, Menu, UserRound, X } from "lucide-react";

const fullLinks = [
  { href: "/", label: "Home" },
  { href: "/upload", label: "Upload" },
  { href: "/dashboard", label: "Analysis" },
  { href: "/results", label: "Results" },
];

const homeLinks = fullLinks.slice(0, 2);
const workspacePaths = new Set(["/dashboard", "/results"]);

export function SiteNav() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const isWorkspace = workspacePaths.has(pathname);
  const links = isWorkspace ? fullLinks : homeLinks;

  useEffect(() => {
    setOpen(false);
  }, [pathname]);

  return (
    <>
      <nav
        className="hidden items-center rounded-full border border-zinc-200 bg-white/85 p-1 text-sm font-semibold text-zinc-600 shadow-sm shadow-zinc-950/5 lg:flex"
        aria-label="Primary navigation"
      >
        {links.map((link) => {
          const active = pathname === link.href;
          return (
            <Link
              className={`rounded-full px-4 py-2 transition ${
                active ? "bg-zinc-950 text-white shadow-sm" : "hover:bg-zinc-100 hover:text-zinc-950"
              }`}
              href={link.href}
              key={link.href}
            >
              {link.label}
            </Link>
          );
        })}
      </nav>
      <nav className="hidden shrink-0 items-center gap-2 text-sm font-semibold sm:flex" aria-label="Primary action">
        {isWorkspace ? (
          <Link className="hidden rounded-full px-3 py-2 text-zinc-600 transition hover:bg-zinc-100 hover:text-zinc-950 sm:block lg:hidden" href="/dashboard">
            Analysis
          </Link>
        ) : null}
        <Link className="flex items-center gap-2 rounded-full p-2.5 text-zinc-600 transition hover:bg-zinc-100 hover:text-zinc-950 sm:px-3 sm:py-2" href="/account" aria-label="Account">
          <UserRound className="h-4 w-4" />
          <span className="hidden sm:inline">Account</span>
        </Link>
        <Link className="flex items-center gap-1.5 rounded-full bg-zinc-950 px-3 py-2.5 text-white shadow-lg shadow-zinc-950/10 transition hover:-translate-y-0.5 hover:bg-zinc-800 sm:gap-2 sm:px-4" href="/upload">
          <span className="sm:hidden">Upload</span>
          <span className="hidden sm:inline">{isWorkspace ? "New upload" : "Upload resume"}</span>
          <ArrowUpRight className="h-3.5 w-3.5" />
        </Link>
      </nav>
      <button
        className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-zinc-200 bg-white text-zinc-700 shadow-sm transition hover:bg-zinc-50 sm:hidden"
        type="button"
        aria-label={open ? "Close navigation menu" : "Open navigation menu"}
        aria-expanded={open}
        onClick={() => setOpen((current) => !current)}
      >
        {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
      </button>
      {open ? (
        <div className="fixed inset-x-3 top-[4.75rem] z-50 overflow-hidden rounded-3xl border border-zinc-200 bg-white/95 p-3 shadow-2xl shadow-zinc-950/15 backdrop-blur-xl sm:hidden">
          <nav className="grid gap-1" aria-label="Mobile navigation">
            {links.map((link) => {
              const active = pathname === link.href;
              return (
                <Link
                  className={`rounded-2xl px-4 py-3 text-sm font-bold transition ${
                    active ? "bg-zinc-950 text-white" : "text-zinc-700 hover:bg-zinc-100 hover:text-zinc-950"
                  }`}
                  href={link.href}
                  key={link.href}
                >
                  {link.label}
                </Link>
              );
            })}
            <div className="my-2 h-px bg-zinc-100" />
            <Link className="flex items-center gap-2 rounded-2xl px-4 py-3 text-sm font-bold text-zinc-700 hover:bg-zinc-100" href="/account">
              <UserRound className="h-4 w-4" />
              Account
            </Link>
            <Link className="flex items-center justify-between rounded-2xl bg-zinc-950 px-4 py-3 text-sm font-bold text-white" href="/upload">
              {isWorkspace ? "Start new upload" : "Upload resume"}
              <ArrowUpRight className="h-4 w-4" />
            </Link>
          </nav>
        </div>
      ) : null}
    </>
  );
}
