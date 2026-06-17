import type { Metadata } from "next";
import Link from "next/link";
import { AuthPrompt } from "@/components/auth-prompt";
import { CursorLine } from "@/components/cursor-line";
import { FeedbackPrompt } from "@/components/feedback-prompt";
import { SiteNav } from "@/components/site-nav";
import { ResumePrismIcon } from "@/components/visuals/product-icons";
import "./globals.css";

export const metadata: Metadata = {
  title: "ATS Resume Studio",
  description: "Analyze, optimize, and rebuild ATS-ready resumes with clear role-aware guidance."
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <header className="sticky top-0 z-40 border-b border-zinc-200/70 bg-white/75 backdrop-blur-2xl">
          <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-2 px-3 sm:h-[4.5rem] sm:gap-4 sm:px-6">
            <Link href="/" className="group flex min-w-0 items-center gap-3 text-zinc-950">
              <span className="grid h-10 w-10 shrink-0 place-items-center rounded-2xl border border-white/80 bg-gradient-to-br from-indigo-50 to-cyan-50 shadow-lg shadow-indigo-950/10 transition group-hover:-translate-y-0.5 sm:h-11 sm:w-11">
                <ResumePrismIcon className="h-8 w-8 sm:h-9 sm:w-9" />
              </span>
              <span className="min-w-0">
                <span className="block truncate text-xs font-black tracking-tight min-[380px]:text-sm sm:text-base">ATS Resume Studio</span>
                <span className="hidden text-[11px] font-semibold uppercase tracking-[0.16em] text-zinc-400 sm:block">Resume match workspace</span>
              </span>
            </Link>
            <SiteNav />
          </div>
        </header>
        <CursorLine />
        <AuthPrompt />
        <FeedbackPrompt />
        {children}
      </body>
    </html>
  );
}
