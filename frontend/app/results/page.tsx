"use client";

import { useEffect, useState } from "react";
import { Download, FileText, Loader2, Sparkles, UploadCloud, Wand2 } from "lucide-react";
import { AnalysisResponse, apiUrl, OptimizationResponse, optimizeResume, rebuildResume, WorkflowState } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

export default function ResultsPage() {
  const [workflow, setWorkflow] = useState<WorkflowState | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [optimized, setOptimized] = useState<OptimizationResponse | null>(null);
  const [download, setDownload] = useState<{ href: string; label: string } | null>(null);
  const [loading, setLoading] = useState("");
  const [error, setError] = useState("");
  const [needsUpload, setNeedsUpload] = useState(false);

  useEffect(() => {
    const savedWorkflow = localStorage.getItem("ats-workflow");
    const savedAnalysis = localStorage.getItem("ats-analysis");
    const savedOptimized = localStorage.getItem("ats-optimized");
    if (savedWorkflow) setWorkflow(JSON.parse(savedWorkflow));
    if (!savedWorkflow) setNeedsUpload(true);
    if (savedAnalysis) setAnalysis(JSON.parse(savedAnalysis));
    if (savedOptimized) setOptimized(JSON.parse(savedOptimized));
  }, []);

  async function runOptimization() {
    if (!workflow) return;
    setLoading("optimize");
    setError("");
    try {
      const result = await optimizeResume(workflow.filename, workflow.jobDescription);
      setOptimized(result);
      localStorage.setItem("ats-optimized", JSON.stringify(result));
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Optimization failed");
    } finally {
      setLoading("");
    }
  }

  async function rebuild(format: "docx" | "pdf") {
    if (!workflow) return;
    setLoading(format);
    setError("");
    try {
      const result = await rebuildResume(workflow.filename, workflow.jobDescription, format);
      setDownload({ href: apiUrl(result.download_url), label: result.filename });
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Resume rebuild failed");
    } finally {
      setLoading("");
    }
  }

  const ats = optimized?.ats || analysis?.ats;
  const score = ats?.score ?? 0;

  return (
    <main className="mx-auto grid max-w-6xl gap-6 px-4 py-8 lg:grid-cols-[0.82fr_1.18fr]">
      {needsUpload ? (
        <div className="fixed inset-0 z-30 flex items-center justify-center bg-zinc-950/45 px-4 backdrop-blur-sm">
          <div className="max-w-md rounded-md border border-white/70 bg-white p-6 shadow-xl">
            <div className="flex h-11 w-11 items-center justify-center rounded-md bg-cyan-50 text-cyan-800">
              <UploadCloud className="h-5 w-5" />
            </div>
            <h2 className="mt-4 text-xl font-semibold text-zinc-950">Start with upload</h2>
            <p className="mt-2 text-sm leading-6 text-zinc-600">
              Results need an uploaded resume and job description before optimization can run.
            </p>
            <Button className="mt-5 w-full" variant="secondary" onClick={() => window.location.assign("/upload")}>
              <UploadCloud className="h-4 w-4" />
              Go to upload
            </Button>
          </div>
        </div>
      ) : null}

      <section className="space-y-4">
        <Card>
          <CardHeader><CardTitle>Final score</CardTitle></CardHeader>
          <CardContent>
            <div className="flex items-end gap-2">
              <span className="text-6xl font-semibold text-zinc-950">{score}</span>
              <span className="pb-3 text-sm text-zinc-500">/ 100</span>
            </div>
            <Progress value={score} className="mt-4" />
            <p className="mt-4 text-sm text-zinc-600">
              {optimized ? "Optimization guidance is ready." : "Run optimization to generate improved summary, bullets, and RAG-backed guidance."}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Build optimized resume</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <Button onClick={runOptimization} disabled={!workflow || loading === "optimize"} className="w-full" variant="secondary">
              {loading === "optimize" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Wand2 className="h-4 w-4" />}
              Optimize
            </Button>
            <div className="grid grid-cols-2 gap-2">
              <Button variant="outline" onClick={() => rebuild("docx")} disabled={!workflow || loading === "docx"}>
                {loading === "docx" ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileText className="h-4 w-4" />}
                DOCX
              </Button>
              <Button variant="outline" onClick={() => rebuild("pdf")} disabled={!workflow || loading === "pdf"}>
                {loading === "pdf" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
                PDF
              </Button>
            </div>
            {download ? (
              <a className="flex items-center gap-2 rounded-md bg-cyan-50 p-3 text-sm font-medium text-cyan-900 hover:bg-cyan-100" href={download.href} download>
                <Download className="h-4 w-4" />
                {download.label}
              </a>
            ) : null}
            {error ? <p className="rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
          </CardContent>
        </Card>
      </section>

      <section className="space-y-4">
        <Card>
          <CardHeader><CardTitle>Recommendations</CardTitle></CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-2">
            {(ats?.recommendations || []).map((item, index) => (
              <p key={`${item}-${index}`} className="flex gap-2 rounded-md bg-white p-3 text-sm text-zinc-700 shadow-sm">
                <Sparkles className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
                {item}
              </p>
            ))}
            {!ats?.recommendations?.length ? <p className="text-sm text-zinc-500">Recommendations appear after analysis or optimization.</p> : null}
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Optimized summary</CardTitle></CardHeader>
          <CardContent>
            <p className="rounded-md bg-zinc-950 p-4 text-sm leading-6 text-zinc-50">
              {optimized?.optimization.improved_summary || "Run optimization to generate a role-targeted summary."}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Optimized bullets</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {(optimized?.optimization.improved_bullets || []).map((item, index) => (
              <div className="rounded-md border border-zinc-200 bg-white p-3" key={`${item.original}-${index}`}>
                <p className="text-xs leading-5 text-zinc-500">{item.original}</p>
                <p className="mt-2 text-sm font-medium leading-6 text-zinc-950">{item.improved}</p>
              </div>
            ))}
            {!optimized?.optimization.improved_bullets?.length ? <p className="text-sm text-zinc-500">Improved bullets appear after optimization.</p> : null}
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>RAG guidance</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            {(optimized?.optimization.rag_guidance || []).map((item, index) => (
              <p className="rounded-md bg-cyan-50 p-3 text-sm text-cyan-950" key={`${item}-${index}`}>{item}</p>
            ))}
            {!optimized?.optimization.rag_guidance?.length ? <p className="text-sm text-zinc-500">Retrieved profile guidance appears after optimization.</p> : null}
          </CardContent>
        </Card>
      </section>
    </main>
  );
}
