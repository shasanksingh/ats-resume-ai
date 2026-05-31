"use client";

import { ChangeEvent, useState } from "react";
import { ArrowRight, BrainCircuit, FileUp, Layers3, Loader2, ShieldCheck } from "lucide-react";
import { useRouter } from "next/navigation";
import { uploadResume } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";

const profiles = ["Data Analyst", "SQL Developer", "Python Developer", "Digital Marketing", "AI Engineer"];
const pipeline = [
  { label: "Local-first", icon: ShieldCheck },
  { label: "ATS scoring", icon: Layers3 },
  { label: "RAG guidance", icon: BrainCircuit },
];

export default function UploadPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [jd, setJd] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function onFile(event: ChangeEvent<HTMLInputElement>) {
    setFile(event.target.files?.[0] || null);
  }

  async function submit() {
    if (!file || !jd.trim()) {
      setError("Upload a PDF resume and paste a job description.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const uploaded = await uploadResume(file);
      localStorage.setItem("ats-workflow", JSON.stringify({ filename: uploaded.filename, jobDescription: jd }));
      localStorage.removeItem("ats-analysis");
      localStorage.removeItem("ats-optimized");
      router.push("/dashboard");
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Upload failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto grid max-w-6xl gap-6 px-4 py-8 lg:grid-cols-[0.86fr_1.14fr]">
      <section className="space-y-6">
        <div className="rounded-md border border-white/70 bg-zinc-950 p-6 text-white shadow-sm">
          <div className="inline-flex items-center gap-2 rounded-md bg-white/10 px-3 py-1 text-xs font-medium text-cyan-100">
            <BrainCircuit className="h-4 w-4" />
            RAG powered ATS optimizer
          </div>
          <h1 className="mt-5 text-4xl font-semibold tracking-normal">Resume intelligence for role-specific matching</h1>
          <p className="mt-4 max-w-xl text-sm leading-6 text-zinc-300">
            Parse a PDF resume, compare it against a target JD, surface missing keywords, and rebuild an optimized draft with truthful guidance.
          </p>
          <div className="mt-6 grid gap-3 sm:grid-cols-3">
            {pipeline.map(({ label, icon: Icon }) => (
              <div className="rounded-md border border-white/10 bg-white/5 p-3" key={label}>
                <Icon className="h-5 w-5 text-amber-300" />
                <p className="mt-3 text-sm font-medium">{label}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          {profiles.map((profile) => (
            <span className="rounded-md border border-white/70 bg-white/80 px-3 py-2 text-xs font-medium text-zinc-700 shadow-sm" key={profile}>
              {profile}
            </span>
          ))}
        </div>
      </section>

      <Card>
        <CardHeader>
          <CardTitle>Resume and job description</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <label className="flex min-h-44 cursor-pointer flex-col items-center justify-center rounded-md border border-dashed border-cyan-300 bg-cyan-50/70 p-6 text-center transition hover:bg-white">
            <FileUp className="mb-3 h-8 w-8 text-cyan-800" />
            <span className="text-sm font-semibold text-zinc-950">{file ? file.name : "Choose resume PDF"}</span>
            <span className="mt-1 text-xs text-zinc-500">PDF only</span>
            <input className="sr-only" type="file" accept="application/pdf" onChange={onFile} />
          </label>
          <Textarea
            value={jd}
            onChange={(event) => setJd(event.target.value)}
            placeholder="Paste the target job description..."
            className="min-h-64"
          />
          {error ? <p className="rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
          <Button onClick={submit} disabled={loading} className="w-full" variant="secondary">
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <ArrowRight className="h-4 w-4" />}
            Continue to analysis
          </Button>
        </CardContent>
      </Card>
    </main>
  );
}
