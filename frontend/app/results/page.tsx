"use client";

import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  ArrowRight,
  Bot,
  Braces,
  Check,
  CheckSquare2,
  CheckCircle2,
  Clipboard,
  Download,
  Eye,
  FileDown,
  FileText,
  Lightbulb,
  Loader2,
  RefreshCw,
  Sparkles,
  Square,
  ShieldCheck,
  Target,
  TriangleAlert,
  UploadCloud
} from "lucide-react";
import { useRouter } from "next/navigation";
import {
  AnalysisResponse,
  LATEX_PREVIEW_READY_EVENT,
  AtsResult,
  ExportDetails,
  scoreSelectedChanges,
  apiUrl,
  BulletRewrite,
  compileLatex,
  generateLatex,
  getLatexCompilerStatus,
  LatexCompileResponse,
  LatexCompilerStatus,
  LatexResponse,
  OptimizationResponse,
  optimizeResume,
  RagSearchResponse,
  rebuildResume,
  refineSelectedChanges,
  searchRag,
  WorkflowState
} from "@/lib/api";
import { readActiveWorkflow, readStoredJson } from "@/lib/storage";
import { ScoreGauge } from "@/components/score-gauge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { Toast } from "@/components/ui/toast";
import { Textarea } from "@/components/ui/textarea";
import { InsightStackIcon } from "@/components/visuals/product-icons";

type Notice = { message: string; tone: "success" | "error" | "info" } | null;

export default function ResultsPage() {
  const router = useRouter();
  const [workflow, setWorkflow] = useState<WorkflowState | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [optimized, setOptimized] = useState<OptimizationResponse | null>(null);
  const [download, setDownload] = useState<{ href: string; label: string } | null>(null);
  const [latex, setLatex] = useState<LatexResponse | null>(null);
  const [latexPreview, setLatexPreview] = useState<LatexCompileResponse | null>(null);
  const [compilerStatus, setCompilerStatus] = useState<LatexCompilerStatus | null>(null);
  const [rag, setRag] = useState<RagSearchResponse | null>(null);
  const [ragLoading, setRagLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [hydrated, setHydrated] = useState(false);
  const [confirmedSkills, setConfirmedSkills] = useState<string[]>([]);
  const [selectedSummary, setSelectedSummary] = useState(false);
  const [selectedBulletOriginals, setSelectedBulletOriginals] = useState<string[]>([]);
  const [instruction, setInstruction] = useState("");
  const [refinementMeta, setRefinementMeta] = useState<{ provider: string; cached: boolean; latencyMs: number } | null>(null);
  const [loading, setLoading] = useState<"" | "optimize" | "refine" | "docx" | "pdf" | "latex" | "compile">("");
  const [notice, setNotice] = useState<Notice>(null);
  const [selectionScore, setSelectionScore] = useState<{ key: string; ats: AtsResult; baseline_ats: AtsResult } | null>(null);
  const [exportResult, setExportResult] = useState<{ key: string; details: ExportDetails } | null>(null);
  const [scoreError, setScoreError] = useState("");

  useEffect(() => {
    const savedWorkflow = readActiveWorkflow();
    setWorkflow(savedWorkflow);
    const savedAnalysis = readStoredJson<AnalysisResponse>("ats-analysis");
    const savedOptimization = readStoredJson<OptimizationResponse>("ats-optimized");
    setAnalysis(savedAnalysis?.filename === savedWorkflow?.filename ? savedAnalysis : null);
    setOptimized(savedOptimization?.filename === savedWorkflow?.filename && savedOptimization?.optimization_version === 2 ? savedOptimization : null);
    if (savedOptimization && savedOptimization.filename === savedWorkflow?.filename && savedOptimization.optimization_version !== 2) {
      setNotice({ message: "Optimization has been updated. Run Optimize resume to generate fresh rewrites.", tone: "info" });
    }
    setHydrated(true);
    void getLatexCompilerStatus()
      .then(setCompilerStatus)
      .catch(() => setCompilerStatus({
        available: false,
        compiler: null,
        message: "Compiler status is unavailable."
      }));
    if (savedWorkflow?.jobDescription) {
      void loadRagInsights(savedWorkflow.jobDescription);
    }
  }, []);

  async function loadRagInsights(jobDescription: string) {
    setRagLoading(true);
    try {
      setRag(await searchRag(jobDescription, 6));
    } catch (exc) {
      setNotice({ message: exc instanceof Error ? exc.message : "Role guidance is unavailable.", tone: "error" });
    } finally {
      setRagLoading(false);
    }
  }

  async function runOptimization() {
    if (!workflow) return;
    setLoading("optimize");
    setNotice(null);
    try {
      const result = await optimizeResume(workflow.filename, workflow.jobDescription, confirmedSkills);
      setOptimized(result);
      setDownload(null);
      setExportResult(null);
      setSelectedSummary(false);
      setSelectedBulletOriginals([]);
      setRefinementMeta(null);
      setLatex(null);
      setLatexPreview(null);
      localStorage.setItem("ats-optimized", JSON.stringify(result));
      setNotice({ message: result.optimization.refinement_provider ? `${result.optimization.changed_count ?? 0} suggested changes ready for review.` : result.optimization.ai_message || "Local suggestions are ready.", tone: result.optimization.ai_status === "fallback" ? "error" : "success" });
    } catch (exc) {
      setNotice({ message: exc instanceof Error ? exc.message : "Optimization failed.", tone: "error" });
    } finally {
      setLoading("");
    }
  }

  async function rebuild(format: "docx" | "pdf") {
    if (!workflow) return;
    setLoading(format);
    setNotice(null);
    try {
      const result = await rebuildResume(workflow.filename, workflow.jobDescription, format, confirmedSkills, selectedSummaryText, selectedBullets);
      setExportResult({ key: selectionKey, details: result });
      setDownload({ href: apiUrl(result.download_url), label: result.filename });
      setNotice({ message: `${format.toUpperCase()} resume built successfully.`, tone: "success" });
    } catch (exc) {
      setNotice({ message: exc instanceof Error ? exc.message : "Resume rebuild failed.", tone: "error" });
    } finally {
      setLoading("");
    }
  }

  async function createLatex() {
    if (!workflow) return;
    setLoading("latex");
    setNotice(null);
    try {
      const result = await generateLatex(
        workflow.filename,
        workflow.jobDescription,
        confirmedSkills,
        selectedSummaryText,
        selectedBullets
      );
      setLatex(result);
      setLatexPreview(null);
      setNotice({ message: "LaTeX source generated with your resume's font styling.", tone: "success" });
    } catch (exc) {
      setNotice({ message: exc instanceof Error ? exc.message : "LaTeX generation failed.", tone: "error" });
    } finally {
      setLoading("");
    }
  }

  async function compileGeneratedLatex() {
    if (!workflow) return;
    setLoading("compile");
    setNotice(null);
    try {
      const result = await compileLatex(
        workflow.filename,
        workflow.jobDescription,
        confirmedSkills,
        selectedSummaryText,
        selectedBullets
      );
      setLatexPreview(result);
      if (result.latex_source && result.source_download_url && result.source_filename) {
        setLatex((previous) => previous ? { ...previous, latex_source: result.latex_source!,
          filename: result.source_filename!, download_url: result.source_download_url!,
          path: `optimized/${result.source_filename}` } : previous);
      }
      window.dispatchEvent(new CustomEvent(LATEX_PREVIEW_READY_EVENT, { detail: { filename: workflow.filename } }));
      setExportResult({ key: selectionKey, details: result });
      setNotice({
        message: result.fallback
          ? "Original PDF layout retained. Review the export notes below."
          : `LaTeX compiled with ${result.compiler}.`,
        tone: "success"
      });
    } catch (exc) {
      setNotice({ message: exc instanceof Error ? exc.message : "LaTeX compilation failed.", tone: "error" });
    } finally {
      setLoading("");
    }
  }

  function toggleConfirmedSkill(skill: string) {
    setConfirmedSkills((current) => (
      current.includes(skill)
        ? current.filter((item) => item !== skill)
        : [...current, skill]
    ));
    setLatex(null);
    setLatexPreview(null);
    setDownload(null);
  }

  function invalidateLatex() {
    setLatex(null);
    setLatexPreview(null);
    setDownload(null);
    setExportResult(null);
  }

  function toggleSummarySelection() {
    setSelectedSummary((current) => !current);
    invalidateLatex();
  }

  function toggleBulletSelection(original: string) {
    setSelectedBulletOriginals((current) => (
      current.includes(original)
        ? current.filter((item) => item !== original)
        : [...current, original]
    ));
    invalidateLatex();
  }

  function selectAllChanges() {
    if (!optimized) return;
    setSelectedSummary(Boolean(optimized.optimization.improved_summary && optimized.optimization.improved_summary.trim() !== optimized.structured_resume.summary?.trim()));
    setSelectedBulletOriginals(optimized.optimization.improved_bullets.filter((item) => item.original.trim() !== item.improved.trim()).map((item) => item.original));
    invalidateLatex();
  }

  function clearSelectedChanges() {
    setSelectedSummary(false);
    setSelectedBulletOriginals([]);
    invalidateLatex();
  }

  async function applyInstruction() {
    if (!workflow || !optimized || instruction.trim().length < 3 || selectionCount === 0) return;
    setLoading("refine");
    setNotice(null);
    try {
      const result = await refineSelectedChanges(
        workflow.jobDescription,
        instruction.trim(),
        selectedSummaryText,
        selectedBullets
      );
      const replacementBullets = new Map(result.bullets.map((item) => [item.original, item]));
      const updated: OptimizationResponse = {
        ...optimized,
        optimization: {
          ...optimized.optimization,
          improved_summary: result.summary || optimized.optimization.improved_summary,
          improved_bullets: optimized.optimization.improved_bullets.map(
            (item) => replacementBullets.get(item.original) || item
          )
        }
      };
      setOptimized(updated);
      localStorage.setItem("ats-optimized", JSON.stringify(updated));
      setRefinementMeta({ provider: result.provider, cached: result.cached, latencyMs: result.latency_ms });
      invalidateLatex();
      setNotice({ message: "Selected changes were refined with your instruction.", tone: "success" });
    } catch (exc) {
      setNotice({ message: exc instanceof Error ? exc.message : "AI refinement failed.", tone: "error" });
    } finally {
      setLoading("");
    }
  }

  async function copyLatex() {
    if (!latex) return;
    await navigator.clipboard.writeText(latex.latex_source);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1800);
  }

  const selectedBullets: BulletRewrite[] = useMemo(
    () => (optimized?.optimization.improved_bullets || []).filter((item) => selectedBulletOriginals.includes(item.original)),
    [optimized, selectedBulletOriginals]
  );
  const selectedSummaryText = selectedSummary ? optimized?.optimization.improved_summary || null : null;
  const selectionCount = selectedBullets.length + (selectedSummaryText ? 1 : 0);
  const availableChangeCount = (optimized?.optimization.improved_bullets || []).filter((item) => item.original.trim() !== item.improved.trim()).length
    + Number(Boolean(optimized?.optimization.improved_summary && optimized.optimization.improved_summary.trim() !== optimized.structured_resume.summary?.trim()));
  const selectionKey = JSON.stringify([workflow?.filename, workflow?.jobDescription, confirmedSkills, selectedSummaryText, selectedBullets]);
  const currentScore = selectionScore?.key === selectionKey ? selectionScore : null;
  const currentExport = exportResult?.key === selectionKey ? exportResult.details : null;
  const baseline = currentScore?.baseline_ats || optimized?.baseline_ats || analysis?.ats;
  const ats = currentExport?.ats || currentScore?.ats || baseline;
  const scoreTitle = currentExport?.ats ? "Exported resume score" : currentScore ? (selectionCount || confirmedSkills.length ? "Selected changes · estimated score" : "Original resume score") : "Original score · recalculating";

  useEffect(() => {
    if (!workflow) return;
    let active = true;
    setScoreError("");
    const timer = window.setTimeout(() => {
      void scoreSelectedChanges(workflow.filename, workflow.jobDescription, confirmedSkills, selectedSummaryText, selectedBullets)
        .then((result) => { if (active) setSelectionScore({ key: selectionKey, ...result }); })
        .catch((exc) => { if (active) setScoreError(exc instanceof Error ? exc.message : "Score calculation failed."); });
    }, 250);
    return () => { active = false; window.clearTimeout(timer); };
  }, [workflow, confirmedSkills, selectedSummaryText, selectedBullets, selectionKey]);
  const skillMatch = useMemo(() => {
    if (!ats?.jd_skills?.length) return ats?.score ?? 0;
    return Math.round(((ats.matched_keywords?.length || 0) / ats.jd_skills.length) * 100);
  }, [ats]);
  const sectionScores = useMemo(() => Object.entries(ats?.section_scores || {}), [ats]);
  const scoreExplanations = useMemo(
    () => new Map((ats?.score_explanations || []).map((item) => [item.category, item])),
    [ats]
  );
  const ragInsights = rag?.results?.length
    ? rag.results
    : optimized?.optimization.rag_guidance || [];

  if (!hydrated) return <ResultsSkeleton />;

  if (!workflow) {
    return (
      <main className="grid min-h-[calc(100vh-4rem)] place-items-center px-4">
        <Card className="max-w-md text-center">
          <CardContent className="p-8">
            <div className="mx-auto grid h-12 w-12 place-items-center rounded-2xl bg-indigo-50 text-indigo-700"><UploadCloud className="h-5 w-5" /></div>
            <h1 className="mt-5 text-2xl font-bold text-zinc-950">No analysis found</h1>
            <p className="mt-3 text-sm leading-6 text-zinc-600">Upload a resume and run ATS analysis before opening recruiter-grade results.</p>
            <Button className="mt-6 w-full" variant="secondary" onClick={() => router.push("/upload")}>Start analysis <ArrowRight className="h-4 w-4" /></Button>
          </CardContent>
        </Card>
      </main>
    );
  }

  return (
    <main className="mx-auto w-full max-w-[1600px] space-y-6 overflow-x-hidden px-4 py-8 sm:px-6 sm:py-10">
      <section className="flex flex-col justify-between gap-5 rounded-2xl bg-zinc-950 p-6 text-white shadow-xl shadow-zinc-950/10 sm:p-8 lg:flex-row lg:items-center">
        <div className="min-w-0">
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-cyan-300">Recruiter-grade results</p>
          <h1 className="mt-2 truncate text-2xl font-bold tracking-tight sm:text-3xl">{workflow.filename}</h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-zinc-400">ATS fit, skill evidence, resume quality, optimization guidance, and export in one review.</p>
        </div>
        <div className="flex shrink-0 flex-col gap-2 sm:flex-row">
          <Button className="w-full justify-center bg-white text-zinc-950 hover:bg-zinc-100 sm:w-auto" onClick={runOptimization} disabled={Boolean(loading)}>
            {loading === "optimize" ? <Loader2 className="h-4 w-4 animate-spin" /> : <InsightStackIcon className="h-5 w-5" />}
            {optimized ? "Optimize again" : "Optimize resume"}
          </Button>
          <Button className="w-full justify-center border-white/15 bg-white/5 text-white hover:border-white/25 hover:bg-white/10 sm:w-auto" variant="outline" onClick={() => router.push("/dashboard")}>
            <RefreshCw className="h-4 w-4" />
            Back to analysis
          </Button>
        </div>
      </section>

      {optimized?.optimization.ai_status === "fallback" ? (
        <div role="alert" className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-950">
          <p className="font-bold">NVIDIA optimization did not finish</p>
          <p className="mt-1">{optimized.optimization.ai_message}</p>
          <p className="mt-1">Your resume is unchanged. Local suggestions are available below; use Optimize again to retry.</p>
        </div>
      ) : optimized?.optimization.ai_status === "partial" ? (
        <p role="status" className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-950">NVIDIA completed part of the review · {availableChangeCount} suggested changes are available. Retry optimization to review the retained content.</p>
      ) : optimized?.optimization.ai_status === "success" ? (
        <p role="status" className="rounded-2xl border border-emerald-100 bg-emerald-50 p-4 text-sm text-emerald-900">NVIDIA review complete · {availableChangeCount} suggested changes. Select the changes you want to export.</p>
      ) : null}

      <section className="grid gap-4 md:grid-cols-[0.85fr_1.075fr_1.075fr]">
        <Card className="reveal-card">
          <CardContent className="grid min-h-72 place-items-center">
            <p className="mb-3 text-center text-xs font-semibold text-zinc-600" aria-live="polite">{scoreTitle}</p>
            <ScoreGauge value={ats?.score ?? 0} label="ATS score" />
            <div className="mt-5 text-center">
              <p className="text-sm font-bold text-zinc-950">{scoreLabel(ats?.score ?? 0)}</p>
              <p className="mt-1 text-xs text-zinc-500">Overall resume and role alignment</p>
              {optimized && !selectionCount && !confirmedSkills.length ? <p className="mt-2 text-xs text-zinc-600">No edits selected. Choose changes below to calculate their effect on your score.</p> : null}
              {baseline ? (
                <p className="mt-2 text-xs font-semibold text-emerald-700">
                  Original: {baseline.score}/100 · {currentExport?.ats ? "Exported" : "Selected"}: {currentExport?.ats || currentScore ? `${ats?.score}/100` : "calculating"}. Scores are estimates from this app, not a hiring guarantee.
                </p>
              ) : null}
              {scoreError ? <p role="alert" className="mt-2 text-xs text-amber-700">Selected score unavailable: {scoreError}</p> : null}
            </div>
          </CardContent>
        </Card>

        <MetricCard icon={Target} title="Skill match" value={`${skillMatch}%`} copy={`${ats?.matched_keywords?.length || 0} of ${ats?.jd_skills?.length || 0} detected JD skills are supported.`}>
          <Progress value={skillMatch} />
          <div className="mt-5 flex flex-wrap gap-2">
            {(ats?.matched_keywords || []).slice(0, 10).map((skill) => <Tag key={skill} label={skill} tone="positive" />)}
            {!ats?.matched_keywords?.length ? <Empty text="Run analysis to detect matching skills." /> : null}
          </div>
        </MetricCard>

        <MetricCard icon={TriangleAlert} title="Missing skills" value={`${ats?.missing_keywords?.length || 0}`} copy="Select a skill only if you can demonstrate it in an interview. Confirmed skills are included in exports.">
          <div className="flex flex-wrap gap-2">
            {(baseline?.missing_keywords || []).slice(0, 12).map((skill) => (
              <button
                type="button"
                aria-pressed={confirmedSkills.includes(skill)}
                disabled={Boolean(loading)}
                className={`rounded-lg border px-2.5 py-1.5 text-xs font-semibold transition ${
                  confirmedSkills.includes(skill)
                    ? "border-indigo-300 bg-indigo-50 text-indigo-700"
                    : "border-amber-200 bg-amber-50 text-amber-700 hover:border-amber-300"
                }`}
                key={skill}
                onClick={() => toggleConfirmedSkill(skill)}
              >
                {confirmedSkills.includes(skill) ? <Check className="mr-1 inline h-3 w-3" /> : null}
                {skill}
              </button>
            ))}
            {!ats?.missing_keywords?.length ? <Empty text="No missing role skills detected." /> : null}
          </div>
          {confirmedSkills.length ? <p className="mt-4 text-xs font-medium text-indigo-700">{confirmedSkills.length} skill(s) confirmed for the next optimization or export.</p> : null}
        </MetricCard>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><CheckCircle2 className="h-5 w-5 text-emerald-600" />Resume strengths</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {(ats?.strengths || []).map((item) => <Insight key={item} text={item} tone="positive" />)}
            {!ats?.strengths?.length ? <Empty text="Strengths appear after ATS analysis." /> : null}
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><AlertTriangle className="h-5 w-5 text-amber-600" />Resume weaknesses</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {(ats?.weaknesses || []).map((item) => <Insight key={item} text={item} tone="warning" />)}
            {!ats?.weaknesses?.length ? <Empty text="Weaknesses appear after ATS analysis." /> : null}
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-4 lg:grid-cols-[1.05fr_0.95fr]">
        <Card>
          <CardHeader>
            <CardTitle>Why this score</CardTitle>
            <p className="mt-1 text-xs leading-5 text-zinc-500">Each category shows its weight, point contribution, and the evidence used.</p>
          </CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-2">
            {[...sectionScores].sort((a, b) => a[1] - b[1]).map(([label, value]) => {
              const meta = categoryMeta(label);
              const explanation = scoreExplanations.get(label);
              return (
                <div className="rounded-2xl border border-zinc-200 bg-zinc-50/70 p-4" key={label}>
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-bold text-zinc-950">{meta.label}</p>
                      <p className="mt-1 text-[11px] font-semibold uppercase tracking-[0.12em] text-zinc-400">{explanation?.weight ?? meta.weight}% weight | {explanation?.contribution ?? 0} points</p>
                    </div>
                    <span className={`rounded-full px-2.5 py-1 text-xs font-bold ${categoryTone(value)}`}>{value}%</span>
                  </div>
                  <Progress value={value} className="mt-3" />
                  <p className="mt-3 text-xs leading-5 text-zinc-500">{explanation?.evidence || meta.description}</p>
                </div>
              );
            })}
            {!sectionScores.length ? <Empty text="Category scores appear after analysis." /> : null}
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><Lightbulb className="h-5 w-5 text-indigo-600" />Priority recommendations</CardTitle></CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-2">
            {(ats?.recommendations || []).map((item, index) => (
              <div className="rounded-xl border border-zinc-100 bg-zinc-50 p-4" key={`${item}-${index}`}>
                <span className="text-xs font-bold text-indigo-600">{String(index + 1).padStart(2, "0")}</span>
                <p className="mt-2 text-sm leading-6 text-zinc-700">{item}</p>
              </div>
            ))}
            {!ats?.recommendations?.length ? <Empty text="Recommendations appear after ATS analysis." /> : null}
          </CardContent>
        </Card>
      </section>

      {optimized ? (
        <section className="flex flex-col justify-between gap-4 rounded-2xl border border-indigo-200 bg-gradient-to-r from-indigo-50 via-white to-cyan-50 p-5 sm:flex-row sm:items-center">
          <div className="flex items-start gap-3">
            <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-indigo-600 text-white"><CheckSquare2 className="h-5 w-5" /></div>
            <div>
              <p className="text-sm font-black text-zinc-950">Review and approve changes</p>
              <p className="mt-1 text-xs leading-5 text-zinc-600">Choose which edits to include in your exports. Unselected content is retained.</p>
              <p className="mt-2 text-xs font-bold text-indigo-700">{selectionCount} change{selectionCount === 1 ? "" : "s"} selected</p>
            </div>
          </div>
          <div className="flex shrink-0 gap-2">
            <Button variant="outline" className="flex-1 justify-center sm:flex-none" onClick={clearSelectedChanges} disabled={Boolean(loading) || selectionCount === 0}>Clear</Button>
            <Button variant="secondary" className="flex-1 justify-center sm:flex-none" onClick={selectAllChanges} disabled={Boolean(loading) || availableChangeCount === 0}>Select all</Button>
          </div>
        </section>
      ) : null}

      <section className="grid min-w-0 gap-4 xl:grid-cols-[minmax(0,1.08fr)_minmax(340px,0.92fr)]">
        <div className="min-w-0 space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between gap-3">
                <CardTitle className="flex items-center gap-2"><InsightStackIcon className="h-7 w-7" />Summary review</CardTitle>
                <button
                  type="button"
                  aria-pressed={selectedSummary}
                  disabled={Boolean(loading) || !optimized?.optimization.improved_summary || optimized.optimization.improved_summary.trim() === optimized.structured_resume.summary?.trim()}
                  onClick={toggleSummarySelection}
                  className={`inline-flex shrink-0 items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs font-bold transition disabled:cursor-not-allowed disabled:opacity-40 ${selectedSummary ? "border-indigo-300 bg-indigo-50 text-indigo-700" : "border-zinc-200 bg-white text-zinc-500 hover:border-indigo-200"}`}
                >
                  {selectedSummary ? <CheckSquare2 className="h-4 w-4" /> : <Square className="h-4 w-4" />}
                  {optimized && optimized.optimization.improved_summary.trim() === optimized.structured_resume.summary?.trim() ? "Original retained" : selectedSummary ? "Selected" : "Use change"}
                </button>
              </div>
            </CardHeader>
            <CardContent>
              {loading === "optimize" ? <Skeleton className="h-28" /> : (
                <p className={`rounded-2xl p-5 text-sm leading-7 transition ${selectedSummary ? "bg-indigo-950 text-white ring-2 ring-indigo-300" : "bg-zinc-950 text-zinc-100"}`}>
                  {optimized?.optimization.improved_summary || "Run optimization to generate a role-targeted professional summary."}
                </p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><InsightStackIcon className="h-7 w-7" />Role-specific guidance</CardTitle>
              <p className="mt-1 text-xs leading-5 text-zinc-500">Practical guidance retrieved from the local career knowledge base.</p>
            </CardHeader>
            <CardContent>
              <div className="max-h-[420px] space-y-3 overflow-y-auto pr-1">
                {ragLoading ? <><Skeleton className="h-20" /><Skeleton className="h-20" /><Skeleton className="h-20" /></> : null}
                {!ragLoading && ragInsights.map((item, index) => (
                  <div className="rounded-xl border border-cyan-100 bg-cyan-50/70 p-3" key={`${item}-${index}`}>
                    <p className="text-sm leading-6 text-cyan-950">{item}</p>
                    {rag?.sources?.[index] ? (
                      <p className="mt-2 text-[10px] font-bold uppercase tracking-[0.12em] text-cyan-700">
                        {rag.sources[index].source.replace("_rules.txt", "").replaceAll("_", " ")} | {rag.sources[index].retrieval}
                      </p>
                    ) : null}
                  </div>
                ))}
                {!ragLoading && !ragInsights.length ? <Empty text="No role guidance was retrieved for this job description." /> : null}
              </div>
            </CardContent>
          </Card>

          {optimized?.optimization.warnings?.length ? (
            <Card>
              <CardHeader><CardTitle>Truthfulness checks</CardTitle></CardHeader>
              <CardContent className="space-y-2">
                {optimized.optimization.warnings.map((warning) => <p className="flex gap-2 text-xs leading-5 text-zinc-600" key={warning}><ShieldCheck className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-600" />{warning}</p>)}
              </CardContent>
            </Card>
          ) : null}

          {optimized?.optimization.keyword_decisions?.length ? (
            <Card>
              <CardHeader>
                <CardTitle>Keyword decisions</CardTitle>
                <p className="mt-1 text-xs leading-5 text-zinc-500">See exactly what was added to the export and what remains a recommendation.</p>
              </CardHeader>
              <CardContent className="grid gap-3 sm:grid-cols-2">
                {optimized.optimization.keyword_decisions.slice(0, 14).map((item) => {
                  const added = item.status !== "recommendation_only";
                  return (
                    <div className={`rounded-xl border p-3 ${added ? "border-emerald-100 bg-emerald-50/70" : "border-zinc-200 bg-zinc-50"}`} key={`${item.keyword}-${item.status}`}>
                      <div className="flex items-center justify-between gap-3">
                        <p className="text-sm font-bold text-zinc-950">{item.keyword}</p>
                        <span className={`rounded-full px-2 py-1 text-[10px] font-bold uppercase tracking-wide ${added ? "bg-emerald-100 text-emerald-700" : "bg-zinc-200 text-zinc-600"}`}>
                          {added ? "Added" : "Not added"}
                        </span>
                      </div>
                      <p className="mt-2 text-xs leading-5 text-zinc-600">{item.reason}</p>
                      {item.evidence ? <p className="mt-2 line-clamp-2 text-[11px] italic leading-5 text-zinc-500">Evidence: {item.evidence}</p> : null}
                    </div>
                  );
                })}
              </CardContent>
            </Card>
          ) : null}

          <Card>
            <CardHeader>
              <CardTitle>Experience and project rewrites</CardTitle>
              <p className="mt-1 text-xs leading-5 text-zinc-500">Select only the rewrites you want included in the LaTeX resume.</p>
            </CardHeader>
            <CardContent className="space-y-4">
              {loading === "optimize" ? <><Skeleton className="h-32" /><Skeleton className="h-32" /></> : null}
              {loading !== "optimize" && (optimized?.optimization.improved_bullets || []).map((item, index) => {
                const selected = selectedBulletOriginals.includes(item.original);
                const unchanged = item.original.trim() === item.improved.trim();
                return (
                <article className={`rounded-2xl border p-4 transition ${selected ? "border-indigo-300 bg-indigo-50/40 shadow-sm" : "border-zinc-200"}`} key={`${item.original}-${index}`}>
                  <div className="flex items-start justify-between gap-3">
                    <p className="text-xs font-bold uppercase tracking-[0.14em] text-zinc-400">Original</p>
                    <button
                      type="button"
                      aria-pressed={selected}
                      disabled={Boolean(loading) || unchanged}
                      onClick={() => toggleBulletSelection(item.original)}
                      className={`inline-flex shrink-0 items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs font-bold transition ${selected ? "border-indigo-300 bg-white text-indigo-700" : "border-zinc-200 bg-white text-zinc-500 hover:border-indigo-200"}`}
                    >
                      {selected ? <CheckSquare2 className="h-4 w-4" /> : <Square className="h-4 w-4" />}
                      {unchanged ? "Original retained" : selected ? "Selected" : "Use change"}
                    </button>
                  </div>
                  <p className="mt-2 text-sm leading-6 text-zinc-500">{item.original}</p>
                  {!unchanged ? <>
                    <div className="my-4 h-px bg-zinc-100" />
                    <p className="text-xs font-bold uppercase tracking-[0.14em] text-indigo-600">Suggested rewrite</p>
                    <p className="mt-2 text-sm font-medium leading-6 text-zinc-950">{item.improved}</p>
                  </> : null}
                  <p className="mt-3 text-xs leading-5 text-zinc-500">{item.reason}</p>
                </article>
              );})}
              {loading !== "optimize" && !optimized?.optimization.improved_bullets?.length ? <Empty text="Improved bullets appear after optimization." /> : null}
            </CardContent>
          </Card>
        </div>

        <div className="min-w-0 space-y-4 xl:sticky xl:top-24 xl:self-start">
          <Card className="overflow-hidden border-indigo-200">
            <div className="border-b border-indigo-100 bg-gradient-to-r from-indigo-600 to-violet-600 px-5 py-4 text-white">
              <div className="flex items-center gap-2"><Bot className="h-5 w-5" /><p className="text-sm font-black">Refine selected changes</p></div>
              <p className="mt-1 text-xs leading-5 text-indigo-100">NVIDIA refines only the changes you approved.</p>
            </div>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between gap-3 text-xs">
                <span className="font-bold text-zinc-700">Custom instruction</span>
                <span className="rounded-full bg-indigo-50 px-2.5 py-1 font-bold text-indigo-700">{selectionCount} selected</span>
              </div>
              <Textarea
                value={instruction}
                onChange={(event) => setInstruction(event.target.value)}
                className="min-h-28 resize-y"
                maxLength={2000}
                disabled={loading === "refine"}
                placeholder="Example: Make these changes more concise, use stronger action language, and keep every fact unchanged."
              />
              <div className="flex items-center justify-between gap-3 text-[11px] text-zinc-500">
                <span>{instruction.length.toLocaleString()} / 2,000</span>
                <span>API key remains on the backend</span>
              </div>
              <Button
                className="w-full justify-center"
                variant="secondary"
                onClick={applyInstruction}
                disabled={Boolean(loading) || instruction.trim().length < 3 || selectionCount === 0}
              >
                {loading === "refine" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
                {loading === "refine" ? "Refining selected changes" : "Apply instruction with Mistral"}
              </Button>
              {refinementMeta ? (
                <p className="rounded-xl bg-emerald-50 p-3 text-xs leading-5 text-emerald-800">
                  Updated with {refinementMeta.provider.split("/").pop()} in {refinementMeta.cached ? "a cached response" : `${(refinementMeta.latencyMs / 1000).toFixed(1)}s`}.
                </p>
              ) : null}
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>Build and export resume</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              <p className="text-sm leading-6 text-zinc-600">All exports use your {selectionCount} selected change{selectionCount === 1 ? "" : "s"}. PDF preserves the original layout, icons, fonts, and page count. LaTeX uses the compact layout with your content and font styling.</p>
              <p className="text-xs leading-5 text-zinc-500">Changes that do not fit the original PDF stay unchanged and are listed below. Additional confirmed skills are included in LaTeX and DOCX.</p>
              <div className="grid gap-2 sm:grid-cols-3">
                <Button variant="outline" onClick={() => rebuild("docx")} disabled={Boolean(loading)}>
                  {loading === "docx" ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileText className="h-4 w-4" />}
                  DOCX
                </Button>
                <Button variant="outline" onClick={() => rebuild("pdf")} disabled={Boolean(loading)}>
                  {loading === "pdf" ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileDown className="h-4 w-4" />}
                  PDF
                </Button>
                <Button variant="outline" onClick={createLatex} disabled={Boolean(loading)}>
                  {loading === "latex" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Braces className="h-4 w-4" />}
                  Build LaTeX
                </Button>
              </div>
              <p className="flex items-start gap-2 rounded-xl bg-zinc-50 p-3 text-xs leading-5 text-zinc-600"><ShieldCheck className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-600" />Uploaded and generated resume files are automatically removed after 24 hours.</p>
              {download ? (
                <a className="flex items-center gap-2 rounded-xl bg-emerald-50 p-3 text-sm font-semibold text-emerald-800 transition hover:bg-emerald-100" href={download.href} download>
                  <Download className="h-4 w-4" />
                  Download {download.label}
                </a>
              ) : null}
              {currentExport ? (
                <div role="status" className="space-y-2 rounded-xl bg-zinc-50 p-3 text-xs leading-5 text-zinc-700">
                  {currentExport.page_count ? <p>{currentExport.page_count} page{currentExport.page_count === 1 ? "" : "s"} · original: {currentExport.original_page_count} · exported score: {currentExport.ats?.score}/100</p> : null}
                  {currentExport.applied_changes !== undefined ? <p>{currentExport.applied_changes} text changes applied.</p> : null}
                  {currentExport.warnings?.map((warning) => <p key={warning} className="text-amber-800">{warning}</p>)}
                  {currentExport.skipped_changes?.map((item) => <p key={item.original}>Kept original: {item.original}</p>)}
                </div>
              ) : null}
            </CardContent>
          </Card>
        </div>
      </section>

      {latex ? (
        <section className="min-w-0 overflow-hidden rounded-[1.75rem] border border-zinc-200 bg-white shadow-sm">
          <div className="flex flex-col justify-between gap-4 border-b border-zinc-200 bg-gradient-to-r from-zinc-950 to-indigo-950 p-4 text-white lg:flex-row lg:items-center">
            <div className="min-w-0">
              <p className="text-xs font-bold uppercase tracking-[0.18em] text-cyan-300">Overleaf-style preview</p>
              <h2 className="mt-1 truncate text-xl font-bold">Resume LaTeX</h2>
              <p className="mt-1 text-xs leading-5 text-zinc-400">{latex.applied_changes} approved change{latex.applied_changes === 1 ? "" : "s"} applied | {compilerStatus?.message || "Checking for a local LaTeX compiler..."}</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button variant="outline" className="h-9 border-white/15 bg-white/5 px-3 text-white hover:bg-white/10" onClick={copyLatex}>
                {copied ? <Check className="h-4 w-4" /> : <Clipboard className="h-4 w-4" />}
                {copied ? "Copied" : "Copy"}
              </Button>
              <Button asChild variant="outline" className="h-9 border-white/15 bg-white/5 px-3 text-white hover:bg-white/10">
                <a href={apiUrl(latex.download_url)} download><Download className="h-4 w-4" />Download .tex</a>
              </Button>
              <Button className="h-9 bg-white px-3 text-zinc-950 hover:bg-zinc-100" onClick={compileGeneratedLatex} disabled={Boolean(loading)}>
                {loading === "compile" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Eye className="h-4 w-4" />}
                Preview PDF
              </Button>
            </div>
          </div>
          <div className="grid min-w-0 lg:grid-cols-2">
            <div className="min-w-0 border-b border-zinc-200 lg:border-b-0 lg:border-r">
              <div className="flex items-center justify-between border-b border-zinc-100 px-4 py-3">
                <p className="text-sm font-bold text-zinc-950">LaTeX source</p>
                <span className="rounded-full bg-indigo-50 px-2.5 py-1 text-[11px] font-bold text-indigo-700">Download to edit</span>
              </div>
              <pre className="h-[420px] max-w-full overflow-auto bg-zinc-950 p-4 text-xs leading-5 text-zinc-200 sm:h-[62vh]">
                <code>{latex.latex_source}</code>
              </pre>
            </div>
            <div className="min-w-0 bg-zinc-50">
              <div className="flex items-center justify-between gap-3 border-b border-zinc-200 px-4 py-3">
                <p className="text-sm font-bold text-zinc-950">{latexPreview?.fallback ? "Original layout preview" : "PDF preview"}</p>
                {latexPreview ? (
                  <a className="rounded-full bg-white px-3 py-1.5 text-xs font-bold text-indigo-700 shadow-sm hover:text-indigo-900" href={apiUrl(latexPreview.download_url)} download>
                    Download PDF
                  </a>
                ) : null}
              </div>
              {latexPreview ? (
                <iframe className="h-[70vh] min-h-[420px] w-full bg-zinc-100" src={`${apiUrl(latexPreview.download_url)}#view=Fit&navpanes=0`} title="Compiled LaTeX resume preview" />
              ) : (
                <div className="grid h-[420px] place-items-center p-6 text-center sm:h-[62vh]">
                  <div className="max-w-sm rounded-2xl border border-indigo-100 bg-white p-6 shadow-sm">
                    <Eye className="mx-auto h-8 w-8 text-indigo-600" />
                    <p className="mt-4 text-sm font-bold text-zinc-950">Preview not generated yet</p>
                    <p className="mt-2 text-xs leading-5 text-zinc-500">Compile LaTeX locally. If compilation fails or exceeds the original page count, the preview keeps your original PDF layout.</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </section>
      ) : null}

      {notice ? <Toast message={notice.message} tone={notice.tone} onClose={() => setNotice(null)} /> : null}
    </main>
  );
}

function MetricCard({ icon: Icon, title, value, copy, children }: { icon: typeof Target; title: string; value: string; copy: string; children: React.ReactNode }) {
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

function Tag({ label, tone }: { label: string; tone: "positive" | "warning" }) {
  return <span className={`rounded-lg px-2.5 py-1.5 text-xs font-semibold ${tone === "positive" ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"}`}>{label}</span>;
}

function Insight({ text, tone }: { text: string; tone: "positive" | "warning" }) {
  const Icon = tone === "positive" ? CheckCircle2 : AlertTriangle;
  return <p className={`flex gap-3 rounded-xl p-3 text-sm leading-6 ${tone === "positive" ? "bg-emerald-50 text-emerald-950" : "bg-amber-50 text-amber-950"}`}><Icon className={`mt-1 h-4 w-4 shrink-0 ${tone === "positive" ? "text-emerald-600" : "text-amber-600"}`} />{text}</p>;
}

function Empty({ text }: { text: string }) {
  return <p className="text-sm leading-6 text-zinc-500">{text}</p>;
}

function scoreLabel(score: number) {
  if (score >= 85) return "Strong alignment";
  if (score >= 70) return "Competitive foundation";
  if (score >= 50) return "Needs targeted improvements";
  return "Significant gaps detected";
}

function categoryMeta(key: string) {
  const categories: Record<string, { label: string; weight: number; description: string }> = {
    skills_match: { label: "Skills match", weight: 30, description: "Direct overlap between resume skills and role requirements." },
    keyword_density: { label: "Keyword coverage", weight: 20, description: "Important job-description terms found naturally in the resume." },
    section_completeness: { label: "Section completeness", weight: 15, description: "Presence of contact, summary, skills, experience, and education." },
    resume_length: { label: "Resume length", weight: 5, description: "Readable content volume for recruiter and ATS scanning." },
    action_verbs: { label: "Action language", weight: 15, description: "Use of clear ownership verbs at the start of accomplishment bullets." },
    quantified_impact: { label: "Measured impact", weight: 15, description: "Evidence of scale, quality, speed, savings, revenue, or other outcomes." }
  };
  return categories[key] || { label: key.replaceAll("_", " "), weight: 0, description: "Supporting ATS quality signal." };
}

function categoryTone(value: number) {
  if (value >= 80) return "bg-emerald-100 text-emerald-700";
  if (value >= 60) return "bg-indigo-100 text-indigo-700";
  return "bg-amber-100 text-amber-700";
}

function ResultsSkeleton() {
  return (
    <main className="mx-auto max-w-7xl space-y-5 px-4 py-10 sm:px-6" aria-label="Loading results">
      <Skeleton className="h-36" />
      <div className="grid gap-4 lg:grid-cols-3"><Skeleton className="h-72" /><Skeleton className="h-72" /><Skeleton className="h-72" /></div>
      <div className="grid gap-4 lg:grid-cols-2"><Skeleton className="h-72" /><Skeleton className="h-72" /></div>
    </main>
  );
}
