import type { Metadata } from "next";
import Link from "next/link";
import { FileScan, Gauge, UploadCloud } from "lucide-react";
import "./globals.css";

export const metadata: Metadata = {
  title: "ATS Resume AI",
  description: "Offline-first ATS resume optimization platform"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <header className="sticky top-0 z-20 border-b border-white/70 bg-white/80 backdrop-blur">
          <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
            <Link href="/upload" className="flex items-center gap-2 text-sm font-semibold tracking-normal text-zinc-950">
              <span className="flex h-8 w-8 items-center justify-center rounded-md bg-zinc-950 text-white">
                <FileScan className="h-4 w-4" />
              </span>
              ATS Resume AI
            </Link>
            <nav className="flex items-center gap-1 text-sm text-zinc-600">
              <Link className="flex items-center gap-2 rounded-md px-3 py-2 hover:bg-white" href="/upload">
                <UploadCloud className="h-4 w-4" />
                <span className="hidden sm:inline">Upload</span>
              </Link>
              <Link className="flex items-center gap-2 rounded-md px-3 py-2 hover:bg-white" href="/dashboard">
                <Gauge className="h-4 w-4" />
                <span className="hidden sm:inline">Dashboard</span>
              </Link>
              <Link className="flex items-center gap-2 rounded-md px-3 py-2 hover:bg-white" href="/results">
                <FileScan className="h-4 w-4" />
                <span className="hidden sm:inline">Results</span>
              </Link>
            </nav>
          </div>
        </header>
        {children}
      </body>
    </html>
  );
}
