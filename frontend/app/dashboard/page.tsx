"use client";

import { useEffect, useMemo, useState } from "react";
import type { ComponentType } from "react";
import {
  ArrowRight,
  BriefcaseBusiness,
  CheckCircle2,
  ClipboardList,
  FileSearch,
  FileText,
  ListChecks,
  Loader2,
  SearchCheck,
  Target,
  TriangleAlert,
  UploadCloud,
  UserRound
} from "lucide-react";
import { useRouter } from "next/navigation";
import { AnalysisResponse, analyzeResume, WorkflowState } from "@/lib/api";
import { readStoredJson } from "@/lib/storage";
import { ScoreGauge } from "@/components/score-gauge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { Toast } from "@/components/ui/toast";
import { ExportCubeIcon } from "@/components/visuals/product-icons";

type Notice = { message: string; tone: "success" | "error" } | null;

export default function DashboardPage() {
  const router = useRouter();
  const [workflow, setWorkflow] = useState<WorkflowState | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [hydrated, setHydrated] = useState(false);
  const [loading, setLoading] = useState(false);
  const [notice, setNotice] = useState<Notice>(null);

  useEffect(() => {
    setWorkflow(readStoredJson<WorkflowState>("ats-workflow"));
    setAnalysis(readStoredJson<AnalysisResponse>("ats-analysis"));
    setHydrated(true);
  }, []);

  async function runAnalysis() {
    if (!workflow) return;
    setLoading(true);
    setNotice(null);
    try {
      const result = await analyzeResume(workflow.filename, workflow.jobDescription);
      setAnalysis(result);
      localStorage.setItem("ats-analysis", JSON.stringify(result));
      setNotice({ message: "ATS analysis completed successfully.", tone: "success" });
    } catch (exc) {
      setNotice({ message: exc instanceof Error ? exc.message : "Analysis failed.", tone: "error" });
    } finally {
      setLoading(false);
    }
  }

  const ats = analysis?.ats;
  const sectionScores = useMemo(() => Object.entries(ats?.section_scores || {}), [ats]);
  const skillMatch = useMemo(() => {
    if (!ats?.jd_skills?.length) return ats?.score ?? 0;
    return Math.round(((ats.matched_keywords?.length || 0) / ats.jd_skills.length) * 100);
  }, [ats]);

  if (!hydrated) return <DashboardSkeleton />;

  if (!workflow) {
    return (
      <main className="grid min-h-[calc(100vh-4rem)] place-items-center px-4">
        <Card className="max-w-md text-center">
          <CardContent className="p-8">
            <div className="mx-auto grid h-12 w-12 place-items-center rounded-2xl bg-indigo-50 text-indigo-700"><UploadCloud className="h-5 w-5" /></div>
            <h1 className="mt-5 text-2xl font-bold text-zinc-950">Upload a resume first</h1>
            <p className="mt-3 text-sm leading-6 text-zinc-600">The dashboard needs a resume PDF and target job description before analysis can begin.</p>
            <Button className="mt-6 w-full" variant="secondary" onClick={() => router.push("/upload")}>Go to upload <ArrowRight className="h-4 w-4" /></Button>
          </CardContent>
        </Card>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-7xl space-y-6 px-4 py-8 sm:px-6 sm:py-10">
      <section className="flex flex-col justify-between gap-5 rounded-2xl border border-zinc-200 bg-white p-5 shadow-sm sm:p-7 lg:flex-row lg:items-center">
        <div className="min-w-0">
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-indigo-600">Analysis workspace</p>
          <h1 className="mt-2 truncate text-2xl font-bold tracking-tight text-zinc-950 sm:text-3xl">{workflow.filename}</h1>
          <p className="mt-2 text-sm leading-6 text-zinc-600">Review ATS alignment, resume structure, recruiter signals, and role-specific gaps.</p>
        </div>
        <div className="flex shrink-0 flex-col gap-2 sm:flex-row">
          <Button onClick={runAnalysis} disabled={loading} variant="secondary" className="w-full justify-center sm:w-auto">
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <SearchCheck className="h-4 w-4" />}
            {analysis ? "Run again" : "Analyze resume"}
          </Button>
          <Button variant="outline" onClick={() => router.push("/results")} disabled={!analysis} className="w-full justify-center sm:w-auto">
            View results <ArrowRight className="h-4 w-4" />
          </Button>
        </div>
      </section>

      <section className="grid overflow-hidden rounded-2xl border border-zinc-200 bg-white sm:grid-cols-3">
        <WorkflowStep icon={UploadCloud} label="Resume uploaded" copy="PDF validated and stored" state="complete" />
        <WorkflowStep icon={ListChecks} label="ATS analysis" copy={analysis ? "Score and gaps ready" : "Run the role comparison"} state={analysis ? "complete" : "active"} />
        <WorkflowStep icon={ExportCubeIcon} label="Optimize and export" copy="Build PDF, DOCX, or LaTeX" state="next" />
      </section>

      {loading ? <AnalysisSkeleton /> : (
        <>
          <section className="grid gap-4 lg:grid-cols-[0.9fr_1.05fr_1.05fr]">
            <Card className="reveal-card">
              <CardContent className="grid min-h-64 place-items-center">
                <ScoreGauge value={ats?.score ?? 0} label="Overall ATS score" />
                <p className="mt-5 text-center text-xs leading-5 text-zinc-500">{analysis ? `${analysis.raw_text_chars.toLocaleString()} resume characters parsed` : "Run analysis to calculate your score."}</p>
              </CardContent>
            </Card>
            <MetricCard title="Skill match" value={`${skillMatch}%`} copy="Detected JD skills supported by the resume." icon={FileSearch}>
              <Progress value={skillMatch} />
              <div className="mt-4 flex flex-wrap gap-2">
                {(ats?.matched_keywords || []).slice(0, 8).map((skill) => <Tag key={skill} label={skill} tone="match" />)}
                {!ats?.matched_keywords?.length ? <Empty text="Matched skills appear after analysis." /> : null}
              </div>
            </MetricCard>
            <MetricCard title="Missing skills" value={`${ats?.missing_keywords?.length || 0}`} copy="JD skills not currently detected in the resume." icon={TriangleAlert}>
              <div className="flex flex-wrap gap-2">
                {(ats?.missing_keywords || []).slice(0, 10).map((skill) => <Tag key={skill} label={skill} tone="missing" />)}
                {!ats?.missing_keywords?.length ? <Empty text="No missing skills to show yet." /> : null}
              </div>
            </MetricCard>
          </section>

          <section className="grid gap-4 lg:grid-cols-[0.9fr_1.1fr]">
            <Card>
              <CardHeader><CardTitle>Section health</CardTitle></CardHeader>
              <CardContent className="space-y-5">
                {sectionScores.length ? sectionScores.map(([label, value]) => (
                  <div key={label}>
                    <div className="mb-2 flex items-center justify-between text-sm">
                      <span className="capitalize text-zinc-600">{label.replaceAll("_", " ")}</span>
                      <span className="font-bold text-zinc-950">{value}%</span>
                    </div>
                    <Progress value={value} />
                  </div>
                )) : <Empty text="Section scoring appears after analysis." />}
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle>Recruiter scan</CardTitle></CardHeader>
              <CardContent className="grid gap-3 sm:grid-cols-2">
                {(ats?.strengths || []).map((item) => <Signal key={item} item={item} positive />)}
                {(ats?.weaknesses || []).map((item) => <Signal key={item} item={item} />)}
                {!ats ? <Empty text="Strengths and weaknesses appear after analysis." /> : null}
              </CardContent>
            </Card>
          </section>

          <section className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
            <Card>
              <CardHeader><CardTitle>Parsed resume snapshot</CardTitle></CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 sm:grid-cols-2">
                  <Snapshot icon={UserRound} title={String(analysis?.resume_data?.name || "Candidate name")} copy={String(analysis?.resume_data?.email || "Contact details appear after analysis.")} />
                  <Snapshot icon={BriefcaseBusiness} title="Detected experience" copy={analysis ? `${(analysis.resume_data?.experience || []).length} roles, ${(analysis.resume_data?.projects || []).length} projects, and ${(analysis.resume_data?.education_entries || []).length} education entries found.` : "Role and project counts appear after analysis."} />
                </div>
                <div className="rounded-2xl border border-zinc-100 bg-zinc-50 p-5">
                  <FileText className="h-5 w-5 text-indigo-600" />
                  <p className="mt-4 text-sm font-bold text-zinc-950">Professional summary</p>
                  <p className="mt-2 text-sm leading-6 text-zinc-600">{String(analysis?.resume_data?.summary || "A readable summary appears here after analysis.")}</p>
                </div>
                {analysis?.resume_data?.skill_groups ? (
                  <div className="grid gap-3 sm:grid-cols-2">
                    {Object.entries(analysis.resume_data.skill_groups).slice(0, 6).map(([label, skills]) => (
                      <div className="rounded-xl border border-zinc-100 p-3" key={label}>
                        <p className="text-xs font-bold text-zinc-950">{label}</p>
                        <p className="mt-1 text-xs leading-5 text-zinc-500">{skills.join(", ")}</p>
                      </div>
                    ))}
                  </div>
                ) : null}
              </CardContent>
            </Card>

            <Card>
              <CardHeader><CardTitle className="flex items-center gap-2"><Target className="h-5 w-5 text-indigo-600" />Target role brief</CardTitle></CardHeader>
              <CardContent className="space-y-4">
                <div className="rounded-2xl bg-zinc-950 p-5 text-zinc-100">
                  <p className="line-clamp-[14] whitespace-pre-wrap text-sm leading-7">{workflow.jobDescription}</p>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="rounded-xl bg-indigo-50 p-3">
                    <ClipboardList className="h-4 w-4 text-indigo-600" />
                    <p className="mt-2 text-lg font-bold text-indigo-950">{workflow.jobDescription.split(/\s+/).filter(Boolean).length}</p>
                    <p className="text-xs text-indigo-700">JD words analyzed</p>
                  </div>
                  <div className="rounded-xl bg-cyan-50 p-3">
                    <FileSearch className="h-4 w-4 text-cyan-600" />
                    <p className="mt-2 text-lg font-bold text-cyan-950">{ats?.jd_skills?.length || 0}</p>
                    <p className="text-xs text-cyan-700">Role skills detected</p>
                  </div>
                </div>
                <Button variant="outline" className="w-full justify-center" onClick={() => router.push("/upload")}>Change resume or job description</Button>
              </CardContent>
            </Card>
          </section>
        </>
      )}

      {notice ? <Toast message={notice.message} tone={notice.tone} onClose={() => setNotice(null)} /> : null}
    </main>
  );
}

function MetricCard({ title, value, copy, icon: Icon, children }: { title: string; value: string; copy: string; icon: typeof FileSearch; children: React.ReactNode }) {
  return (
    <Card className="reveal-card">
      <CardContent>
        <div className="flex items-start justify-between gap-4">
          <div><p className="text-sm font-semibold text-zinc-600">{title}</p><p className="mt-2 text-4xl font-bold tracking-tight text-zinc-950">{value}</p></div>
          <div className="grid h-10 w-10 place-items-center rounded-xl bg-indigo-50 text-indigo-700"><Icon className="h-5 w-5" /></div>
        </div>
        <p className="mb-5 mt-2 text-xs leading-5 text-zinc-500">{copy}</p>
        {children}
      </CardContent>
    </Card>
  );
}

function Tag({ label, tone }: { label: string; tone: "match" | "missing" }) {
  return <span className={`rounded-lg px-2.5 py-1.5 text-xs font-semibold ${tone === "match" ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"}`}>{label}</span>;
}

function Signal({ item, positive = false }: { item: string; positive?: boolean }) {
  const Icon = positive ? CheckCircle2 : TriangleAlert;
  return <p className={`flex gap-2.5 rounded-xl p-3 text-sm leading-6 ${positive ? "bg-emerald-50 text-emerald-950" : "bg-amber-50 text-amber-950"}`}><Icon className={`mt-1 h-4 w-4 shrink-0 ${positive ? "text-emerald-600" : "text-amber-600"}`} />{item}</p>;
}

function Snapshot({ icon: Icon, title, copy }: { icon: typeof UserRound; title: string; copy: string }) {
  return (
    <div className="rounded-2xl border border-zinc-100 bg-zinc-50 p-5">
      <Icon className="h-5 w-5 text-indigo-600" />
      <p className="mt-4 text-sm font-bold text-zinc-950">{title}</p>
      <p className="mt-2 line-clamp-4 text-xs leading-5 text-zinc-500">{copy}</p>
    </div>
  );
}

function WorkflowStep({ icon: Icon, label, copy, state }: { icon: ComponentType<{ className?: string }>; label: string; copy: string; state: "complete" | "active" | "next" }) {
  return (
    <div className={`flex items-center gap-3 border-zinc-100 p-4 sm:border-r sm:last:border-r-0 ${state === "active" ? "bg-indigo-50/70" : ""}`}>
      <div className={`grid h-10 w-10 shrink-0 place-items-center rounded-xl ${
        state === "complete" ? "bg-emerald-100 text-emerald-700" : state === "active" ? "bg-indigo-600 text-white" : "bg-zinc-100 text-zinc-500"
      }`}>
        {state === "complete" ? <CheckCircle2 className="h-5 w-5" /> : <Icon className="h-5 w-5" />}
      </div>
      <div>
        <p className="text-sm font-bold text-zinc-950">{label}</p>
        <p className="mt-0.5 text-xs text-zinc-500">{copy}</p>
      </div>
    </div>
  );
}

function Empty({ text }: { text: string }) {
  return <p className="text-sm leading-6 text-zinc-500">{text}</p>;
}

function DashboardSkeleton() {
  return <main className="mx-auto max-w-7xl space-y-5 px-4 py-10 sm:px-6"><Skeleton className="h-32" /><AnalysisSkeleton /></main>;
}

function AnalysisSkeleton() {
  return (
    <div className="space-y-5" aria-label="Loading analysis">
      <div className="grid gap-4 lg:grid-cols-3"><Skeleton className="h-64" /><Skeleton className="h-64" /><Skeleton className="h-64" /></div>
      <div className="grid gap-4 lg:grid-cols-2"><Skeleton className="h-80" /><Skeleton className="h-80" /></div>
    </div>
  );
}
