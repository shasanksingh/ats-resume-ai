"use client";

import { useEffect, useMemo, useState } from "react";
import { ArrowRight, BriefcaseBusiness, CheckCircle2, FileText, Loader2, SearchCheck, TriangleAlert, UploadCloud, UserRound } from "lucide-react";
import { useRouter } from "next/navigation";
import { AnalysisResponse, analyzeResume, WorkflowState } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

export default function DashboardPage() {
  const router = useRouter();
  const [workflow, setWorkflow] = useState<WorkflowState | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [needsUpload, setNeedsUpload] = useState(false);
  const ats = analysis?.ats;
  const score = ats?.score ?? 0;

  useEffect(() => {
    const saved = localStorage.getItem("ats-workflow");
    const savedAnalysis = localStorage.getItem("ats-analysis");
    if (saved) setWorkflow(JSON.parse(saved));
    if (!saved) setNeedsUpload(true);
    if (savedAnalysis) setAnalysis(JSON.parse(savedAnalysis));
  }, []);

  async function runAnalysis() {
    if (!workflow) return;
    setLoading(true);
    setError("");
    try {
      const result = await analyzeResume(workflow.filename, workflow.jobDescription);
      setAnalysis(result);
      localStorage.setItem("ats-analysis", JSON.stringify(result));
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  }

  const sectionScores = useMemo(() => Object.entries(ats?.section_scores || {}), [ats]);

  return (
    <main className="mx-auto max-w-6xl space-y-6 px-4 py-8">
      {needsUpload ? (
        <div className="fixed inset-0 z-30 flex items-center justify-center bg-zinc-950/45 px-4 backdrop-blur-sm">
          <div className="max-w-md rounded-md border border-white/70 bg-white p-6 shadow-xl">
            <div className="flex h-11 w-11 items-center justify-center rounded-md bg-cyan-50 text-cyan-800">
              <UploadCloud className="h-5 w-5" />
            </div>
            <h2 className="mt-4 text-xl font-semibold text-zinc-950">Upload resume and JD first</h2>
            <p className="mt-2 text-sm leading-6 text-zinc-600">
              The dashboard needs a PDF resume and job description before it can run ATS analysis.
            </p>
            <Button className="mt-5 w-full" variant="secondary" onClick={() => router.push("/upload")}>
              <UploadCloud className="h-4 w-4" />
              Go to upload
            </Button>
          </div>
        </div>
      ) : null}

      <div className="flex flex-col justify-between gap-4 rounded-md border border-white/70 bg-white/80 p-5 shadow-sm backdrop-blur sm:flex-row sm:items-center">
        <div>
          <p className="text-xs font-semibold uppercase text-cyan-800">Analysis dashboard</p>
          <h1 className="mt-1 text-2xl font-semibold text-zinc-950">{workflow?.filename || "No resume selected"}</h1>
          <p className="mt-1 text-sm text-zinc-600">Keyword match, section health, impact signals, and recruiter-ready recommendations.</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={runAnalysis} disabled={!workflow || loading} variant="secondary">
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <SearchCheck className="h-4 w-4" />}
            Analyze
          </Button>
          <Button variant="outline" onClick={() => router.push("/results")} disabled={!analysis}>
            <ArrowRight className="h-4 w-4" />
            Results
          </Button>
        </div>
      </div>

      {error ? <p className="rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}

      <div className="grid gap-4 lg:grid-cols-[1fr_1fr_1fr]">
        <Card>
          <CardHeader><CardTitle>ATS score</CardTitle></CardHeader>
          <CardContent>
            <div className="flex items-end gap-2">
              <span className="text-5xl font-semibold text-zinc-950">{score}</span>
              <span className="pb-2 text-sm text-zinc-500">/ 100</span>
            </div>
            <Progress value={score} className="mt-4" />
            <p className="mt-3 text-xs text-zinc-500">{analysis ? `${analysis.raw_text_chars.toLocaleString()} resume characters parsed` : "Run analysis to generate score."}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Matched skills</CardTitle></CardHeader>
          <CardContent className="flex min-h-36 flex-wrap content-start gap-2">
            {(ats?.matched_keywords || []).slice(0, 18).map((skill) => (
              <span className="rounded-md bg-cyan-50 px-2 py-1 text-xs font-medium text-cyan-800" key={skill}>{skill}</span>
            ))}
            {!ats?.matched_keywords?.length ? <p className="text-sm text-zinc-500">Matched skills appear here after analysis.</p> : null}
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Missing signals</CardTitle></CardHeader>
          <CardContent className="flex min-h-36 flex-wrap content-start gap-2">
            {(ats?.missing_keywords || []).slice(0, 18).map((skill) => (
              <span className="rounded-md bg-amber-50 px-2 py-1 text-xs font-medium text-amber-800" key={skill}>{skill}</span>
            ))}
            {!ats?.missing_keywords?.length ? <p className="text-sm text-zinc-500">Missing JD skills appear here after analysis.</p> : null}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-[0.9fr_1.1fr]">
        <Card>
          <CardHeader><CardTitle>Section health</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            {sectionScores.length ? sectionScores.map(([label, value]) => (
              <div key={label}>
                <div className="mb-2 flex items-center justify-between text-sm">
                  <span className="capitalize text-zinc-700">{label.replaceAll("_", " ")}</span>
                  <span className="font-medium text-zinc-950">{value}</span>
                </div>
                <Progress value={value} />
              </div>
            )) : <p className="text-sm text-zinc-500">Section scoring appears after analysis.</p>}
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Recruiter scan</CardTitle></CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-2">
            {(ats?.strengths || []).map((item) => (
              <p className="flex gap-2 rounded-md bg-cyan-50 p-3 text-sm text-cyan-950" key={item}>
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-cyan-700" />
                {item}
              </p>
            ))}
            {(ats?.weaknesses || []).map((item) => (
              <p className="flex gap-2 rounded-md bg-amber-50 p-3 text-sm text-amber-950" key={item}>
                <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0 text-amber-700" />
                {item}
              </p>
            ))}
            {!ats ? <p className="text-sm text-zinc-500">Strengths and risks appear here after analysis.</p> : null}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader><CardTitle>Resume snapshot</CardTitle></CardHeader>
        <CardContent className="grid gap-4 lg:grid-cols-3">
          <div className="rounded-md bg-white p-4 shadow-sm">
            <UserRound className="h-5 w-5 text-cyan-700" />
            <p className="mt-3 text-sm font-semibold text-zinc-950">{analysis?.resume_data?.name || "Candidate name"}</p>
            <p className="mt-1 text-xs leading-5 text-zinc-500">{analysis?.resume_data?.email || "Contact details appear after analysis."}</p>
          </div>
          <div className="rounded-md bg-white p-4 shadow-sm">
            <FileText className="h-5 w-5 text-cyan-700" />
            <p className="mt-3 text-sm font-semibold text-zinc-950">Summary</p>
            <p className="mt-1 line-clamp-4 text-xs leading-5 text-zinc-500">{analysis?.resume_data?.summary || "A readable summary appears here after analysis."}</p>
          </div>
          <div className="rounded-md bg-white p-4 shadow-sm">
            <BriefcaseBusiness className="h-5 w-5 text-cyan-700" />
            <p className="mt-3 text-sm font-semibold text-zinc-950">Experience items</p>
            <p className="mt-1 text-xs leading-5 text-zinc-500">
              {analysis ? `${(analysis.resume_data?.experience || []).length} roles and ${(analysis.resume_data?.projects || []).length} projects detected.` : "Role and project counts appear after analysis."}
            </p>
          </div>
        </CardContent>
      </Card>
    </main>
  );
}
