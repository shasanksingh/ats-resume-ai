"use client";

import { ChangeEvent, DragEvent, useState } from "react";
import {
  ArrowRight,
  Check,
  FileCheck2,
  FileText,
  FileUp,
  Layers3,
  Loader2,
  ShieldCheck,
  X
} from "lucide-react";
import { useRouter } from "next/navigation";
import { uploadResume } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Textarea } from "@/components/ui/textarea";
import { Toast } from "@/components/ui/toast";
import { InsightStackIcon, ResumePrismIcon } from "@/components/visuals/product-icons";

const MAX_FILE_SIZE = 10 * 1024 * 1024;
const profiles = ["Data Analyst", "SQL Developer", "Python Developer", "Digital Marketing", "Technical Support", "Mechanical Engineer"];
const pipeline = [
  { label: "Private local workflow", icon: ShieldCheck },
  { label: "Multi-factor ATS scoring", icon: Layers3 },
  { label: "Role-specific career guidance", icon: InsightStackIcon }
];

type Notice = { message: string; tone: "success" | "error" } | null;

export default function UploadPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [jd, setJd] = useState("");
  const [loading, setLoading] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState<Notice>(null);

  function selectFile(candidate: File | null) {
    setError("");
    setProgress(0);
    if (!candidate) {
      setFile(null);
      return;
    }
    if (candidate.type !== "application/pdf" && !candidate.name.toLowerCase().endsWith(".pdf")) {
      setFile(null);
      setError("Choose a PDF resume. DOCX and image files are not supported for upload.");
      return;
    }
    if (candidate.size > MAX_FILE_SIZE) {
      setFile(null);
      setError("The resume PDF is larger than 10 MB. Compress it and try again.");
      return;
    }
    if (candidate.size === 0) {
      setFile(null);
      setError("The selected PDF is empty.");
      return;
    }
    setFile(candidate);
  }

  function onFile(event: ChangeEvent<HTMLInputElement>) {
    selectFile(event.target.files?.[0] || null);
    event.target.value = "";
  }

  function onDrop(event: DragEvent<HTMLLabelElement>) {
    event.preventDefault();
    setDragging(false);
    selectFile(event.dataTransfer.files?.[0] || null);
  }

  async function submit() {
    if (!file) {
      setError("Upload a PDF resume before continuing.");
      return;
    }
    if (!jd.trim()) {
      setError("Paste the target job description before continuing.");
      document.getElementById("jd-input")?.focus();
      return;
    }

    setLoading(true);
    setProgress(0);
    setError("");
    setNotice(null);
    try {
      const uploaded = await uploadResume(file, setProgress);
      localStorage.setItem("ats-workflow", JSON.stringify({ filename: uploaded.filename, jobDescription: jd.trim() }));
      localStorage.removeItem("ats-analysis");
      localStorage.removeItem("ats-optimized");
      setNotice({ message: "Resume uploaded successfully. Opening your analysis workspace.", tone: "success" });
      window.setTimeout(() => router.push("/dashboard"), 450);
    } catch (exc) {
      const message = exc instanceof Error ? exc.message : "The resume could not be uploaded.";
      setError(message);
      setNotice({ message, tone: "error" });
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="relative min-h-[calc(100vh-4rem)] overflow-hidden">
      <div className="landing-grid absolute inset-0 -z-20" />
      <div className="aurora absolute inset-x-0 top-0 -z-10 h-[560px] opacity-45" />

      <div className="mx-auto grid max-w-7xl gap-8 px-4 py-10 sm:px-6 sm:py-14 lg:grid-cols-[0.86fr_1.14fr] lg:items-start">
        <section className="space-y-7 lg:sticky lg:top-24">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-indigo-200 bg-white/80 px-3 py-1.5 text-xs font-bold text-indigo-700 shadow-sm">
              <ResumePrismIcon className="h-5 w-5" />
              Start your ATS review
            </div>
            <h1 className="mt-6 max-w-xl text-4xl font-bold tracking-[-0.04em] text-zinc-950 sm:text-5xl">
              Match your resume to the role, not just the keywords.
            </h1>
            <p className="mt-5 max-w-xl text-base leading-8 text-zinc-600">
              Upload a text-based PDF and paste the complete job description. The analysis will identify skill alignment, section quality, missing evidence, and practical next steps.
            </p>
          </div>

          <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1 xl:grid-cols-3">
            {pipeline.map(({ label, icon: Icon }) => (
              <div className="reveal-card rounded-2xl border border-zinc-200 bg-white/85 p-4 shadow-sm backdrop-blur" key={label}>
                <Icon className="h-7 w-7 text-indigo-600" />
                <p className="mt-4 text-sm font-semibold leading-5 text-zinc-800">{label}</p>
              </div>
            ))}
          </div>

          <div>
            <p className="text-xs font-bold uppercase tracking-[0.18em] text-zinc-500">Role intelligence available</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {profiles.map((profile) => (
                <span className="rounded-lg border border-zinc-200 bg-white/80 px-3 py-2 text-xs font-semibold text-zinc-600" key={profile}>
                  {profile}
                </span>
              ))}
            </div>
          </div>
        </section>

        <Card className="overflow-hidden bg-white">
          <div className="border-b border-zinc-100 bg-gradient-to-r from-indigo-50 to-cyan-50 px-5 py-4 sm:px-7">
            <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-indigo-600">New analysis</p>
            <h2 className="mt-1 text-lg font-black text-zinc-950">Resume and target job</h2>
            <p className="mt-1 text-xs leading-5 text-zinc-600">Upload your PDF and paste the role in one focused step.</p>
          </div>
          <CardContent className="space-y-6">
            <div>
              <div className="mb-2 flex items-center justify-between">
                <label className="text-sm font-bold text-zinc-900">Resume PDF</label>
                <span className="text-xs text-zinc-400">Maximum 10 MB</span>
              </div>
              <label
                className={`group flex min-h-52 cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed p-6 text-center outline-none transition focus-within:ring-4 focus-within:ring-indigo-100 ${
                  dragging ? "border-indigo-500 bg-indigo-50" : file ? "border-emerald-300 bg-emerald-50/60" : "border-zinc-200 bg-zinc-50 hover:border-indigo-300 hover:bg-indigo-50/50"
                }`}
                onDragEnter={(event) => {
                  event.preventDefault();
                  setDragging(true);
                }}
                onDragOver={(event) => event.preventDefault()}
                onDragLeave={(event) => {
                  if (!event.currentTarget.contains(event.relatedTarget as Node)) setDragging(false);
                }}
                onDrop={onDrop}
              >
                <input className="sr-only" type="file" accept=".pdf,application/pdf" onChange={onFile} disabled={loading} />
                {file ? (
                  <>
                    <div className="grid h-12 w-12 place-items-center rounded-2xl bg-emerald-100 text-emerald-700"><FileCheck2 className="h-6 w-6" /></div>
                    <span className="mt-4 max-w-full truncate text-sm font-bold text-zinc-950">{file.name}</span>
                    <span className="mt-1 text-xs text-zinc-500">{formatBytes(file.size)} | Ready to upload</span>
                    <button
                      type="button"
                    className="mt-4 inline-flex items-center gap-1 rounded-lg px-2 py-1 text-xs font-semibold text-zinc-500 hover:bg-white hover:text-red-600"
                      onClick={(event) => {
                        event.preventDefault();
                        selectFile(null);
                      }}
                    >
                      <X className="h-3.5 w-3.5" />
                      Remove
                    </button>
                  </>
                ) : (
                  <>
                    <div className="grid h-12 w-12 place-items-center rounded-2xl bg-indigo-100 text-indigo-700 transition group-hover:scale-105"><FileUp className="h-6 w-6" /></div>
                    <span className="mt-4 text-sm font-bold text-zinc-950">{dragging ? "Drop the PDF here" : "Drag and drop your resume"}</span>
                    <span className="mt-1 text-xs text-zinc-500">or click to browse your files</span>
                  </>
                )}
              </label>
            </div>

            <div id="job-description">
              <div className="mb-2 flex items-center justify-between">
                <label htmlFor="jd-input" className="text-sm font-bold text-zinc-900">Target job description</label>
                <span className="text-xs text-zinc-400">{jd.length.toLocaleString()} characters</span>
              </div>
              <Textarea
                id="jd-input"
                value={jd}
                onChange={(event) => setJd(event.target.value)}
                placeholder="Paste the full job description, including responsibilities and required skills..."
                className="min-h-64"
                disabled={loading}
              />
              <p className="mt-2 flex items-start gap-2 text-xs leading-5 text-zinc-500">
                <FileText className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                Complete job descriptions produce more useful skill-match and keyword analysis.
              </p>
            </div>

            {loading || progress > 0 ? (
              <div className="rounded-2xl border border-indigo-100 bg-indigo-50/70 p-4" aria-live="polite">
                <div className="mb-2 flex items-center justify-between text-sm">
                  <span className="font-semibold text-indigo-950">{progress >= 100 ? "Upload complete" : "Uploading resume"}</span>
                  <span className="font-bold text-indigo-700">{progress}%</span>
                </div>
                <Progress value={progress} />
              </div>
            ) : null}

            {error ? (
              <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm leading-6 text-red-700" role="alert">
                {error}
              </div>
            ) : null}

            <Button onClick={submit} disabled={loading} className="h-12 w-full justify-center" variant="secondary">
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <ArrowRight className="h-4 w-4" />}
              {loading ? "Uploading resume" : "Continue to ATS analysis"}
            </Button>

            <div className="flex flex-wrap justify-center gap-x-5 gap-y-2 text-xs text-zinc-500">
              {["PDF validation", "Secure filename", "No paid service"].map((item) => (
                <span className="flex items-center gap-1.5" key={item}><Check className="h-3.5 w-3.5 text-emerald-600" />{item}</span>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {notice ? <Toast message={notice.message} tone={notice.tone} onClose={() => setNotice(null)} /> : null}
    </main>
  );
}

function formatBytes(bytes: number) {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
