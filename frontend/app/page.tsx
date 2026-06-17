import Link from "next/link";
import type { ComponentType } from "react";
import {
  ArrowRight,
  BriefcaseBusiness,
  Check,
  FileCheck2,
  FileSearch,
  LockKeyhole
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  CareerFlowIllustration,
  ExportCubeIcon,
  InsightStackIcon,
  MatchOrbitIcon,
  ResumePrismIcon
} from "@/components/visuals/product-icons";

export default function Home() {
  const features = [
    { icon: MatchOrbitIcon, title: "ATS scoring", copy: "Measure keyword alignment, section quality, action language, and quantified impact." },
    { icon: ResumePrismIcon, title: "Job matching", copy: "Compare your resume with a target role and identify missing skills and recruiter signals." },
    { icon: InsightStackIcon, title: "Role guidance", copy: "Retrieve local guidance for engineering, analytics, support, business, and non-technical profiles." },
    { icon: ExportCubeIcon, title: "Truthful optimization", copy: "Improve summaries and bullets without inventing employers, tools, degrees, or metrics." }
  ];
  const workflow = [
    ["01", "Upload", "Add a text-based PDF resume securely."],
    ["02", "Match", "Paste the job description you want to target."],
    ["03", "Analyze", "Review ATS score, gaps, strengths, and risks."],
    ["04", "Optimize", "Generate focused improvements and export a new draft."]
  ];
  const roles = ["Machine Learning Engineer", "Backend Engineer", "Software Engineer", "Data Analyst", "Technical Support", "Civil Engineer"];

  return (
    <main className="overflow-hidden bg-white">
      <section className="relative isolate border-b border-zinc-200">
        <div className="landing-grid absolute inset-0 -z-20" />
        <div className="aurora absolute -left-24 top-0 -z-10 h-[620px] w-[calc(100%+12rem)] opacity-80" />
        <div className="mx-auto grid max-w-7xl items-center gap-12 px-4 py-14 sm:px-6 sm:py-28 lg:grid-cols-[1.02fr_0.98fr] lg:py-32">
          <div className="fade-up">
            <div className="inline-flex items-center gap-2 rounded-full border border-indigo-200 bg-white/80 px-3 py-1.5 text-xs font-semibold text-indigo-700 shadow-sm backdrop-blur">
              <ResumePrismIcon className="h-5 w-5" />
              Local-first resume intelligence
            </div>
            <h1 className="mt-7 max-w-3xl text-4xl font-bold tracking-[-0.045em] text-zinc-950 min-[380px]:text-5xl sm:text-6xl lg:text-7xl">
              Build a resume that gets through the first scan.
            </h1>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-zinc-600">
              ATS Resume Studio turns your PDF and target job description into a clear score, skill-gap plan, recruiter-grade recommendations, and an optimized downloadable resume.
            </p>
            <div className="mt-9 flex flex-col gap-3 sm:flex-row">
              <Button asChild variant="secondary" className="h-12 w-full justify-center px-6 sm:w-auto">
                <Link href="/upload">
                  Upload your resume
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
              <Button asChild variant="outline" className="h-12 w-full justify-center px-6 sm:w-auto">
                <Link href="/upload#job-description">
                  Analyze a job description
                  <FileSearch className="h-4 w-4" />
                </Link>
              </Button>
            </div>
            <div className="mt-8 flex flex-wrap gap-x-6 gap-y-3 text-sm text-zinc-600">
              {["No paid services", "Local role guidance", "DOCX, PDF, and LaTeX export"].map((item) => (
                <span className="flex items-center gap-2" key={item}>
                  <Check className="h-4 w-4 text-emerald-600" />
                  {item}
                </span>
              ))}
            </div>
          </div>

          <div className="fade-up relative mx-auto w-full max-w-xl [animation-delay:120ms]">
            <div className="absolute -inset-5 rounded-[2rem] bg-gradient-to-br from-indigo-500/20 via-violet-400/10 to-cyan-400/20 blur-2xl" />
            <div className="relative rounded-[1.75rem] border border-white/80 bg-zinc-950 p-3 shadow-2xl shadow-indigo-950/20">
              <div className="rounded-2xl bg-white p-5 sm:p-7">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-indigo-600">Candidate fit</p>
                    <p className="mt-1 text-lg font-bold text-zinc-950">Backend Engineer</p>
                  </div>
                  <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">Ready to improve</span>
                </div>
                <div className="mt-7 grid gap-4 sm:grid-cols-[0.8fr_1.2fr]">
                  <div className="grid place-items-center rounded-2xl bg-zinc-950 p-5 text-white">
                    <div className="grid h-28 w-28 place-items-center rounded-full border-[9px] border-indigo-400/25 border-r-cyan-400 border-t-indigo-400">
                      <div className="text-center">
                        <p className="text-3xl font-bold">82</p>
                        <p className="text-[10px] uppercase tracking-widest text-zinc-400">ATS score</p>
                      </div>
                    </div>
                  </div>
                  <div className="space-y-3">
                    {[
                      ["Skills match", "88%", "w-[88%]"],
                      ["Keyword coverage", "76%", "w-[76%]"],
                      ["Impact signals", "64%", "w-[64%]"]
                    ].map(([label, value, width]) => (
                      <div className="rounded-xl border border-zinc-100 p-3" key={label}>
                        <div className="flex justify-between text-xs font-medium text-zinc-600">
                          <span>{label}</span>
                          <span className="text-zinc-950">{value}</span>
                        </div>
                        <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-zinc-100">
                          <div className={`h-full rounded-full bg-gradient-to-r from-indigo-600 to-cyan-500 ${width}`} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="mt-4 flex flex-wrap gap-2">
                  {["FastAPI", "Python", "PostgreSQL", "Docker"].map((skill) => (
                    <span className="rounded-lg bg-indigo-50 px-2.5 py-1.5 text-xs font-semibold text-indigo-700" key={skill}>{skill}</span>
                  ))}
                  <span className="rounded-lg bg-amber-50 px-2.5 py-1.5 text-xs font-semibold text-amber-700">+ Kubernetes</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="features" className="mx-auto max-w-7xl px-4 py-20 sm:px-6 sm:py-24">
        <SectionHeading eyebrow="One focused workspace" title="Everything needed to move from resume to shortlist" copy="A practical workflow for understanding what an ATS sees and improving the evidence recruiters care about." />
        <div className="mt-12 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {features.map(({ icon: Icon, title, copy }) => (
            <article className="reveal-card rounded-2xl border border-zinc-200 bg-white p-6" key={title}>
              <div className="grid h-12 w-12 place-items-center rounded-xl bg-indigo-50"><Icon className="h-9 w-9" /></div>
              <h3 className="mt-5 font-bold text-zinc-950">{title}</h3>
              <p className="mt-2 text-sm leading-6 text-zinc-600">{copy}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="border-y border-zinc-200 bg-zinc-950 py-20 text-white sm:py-24">
        <div className="mx-auto max-w-7xl px-4 sm:px-6">
          <SectionHeading dark eyebrow="ATS analysis workflow" title="From PDF to a targeted plan in four steps" copy="Keep the process simple, inspectable, and grounded in the experience already on your resume." />
          <div className="mt-12 grid gap-px overflow-hidden rounded-2xl border border-white/10 bg-white/10 md:grid-cols-4">
            {workflow.map(([number, title, copy]) => (
              <div className="bg-zinc-950 p-6 transition hover:bg-zinc-900" key={number}>
                <span className="font-mono text-xs text-cyan-300">{number}</span>
                <h3 className="mt-8 text-lg font-bold">{title}</h3>
                <p className="mt-2 text-sm leading-6 text-zinc-400">{copy}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto grid max-w-7xl gap-12 px-4 py-20 sm:px-6 sm:py-24 lg:grid-cols-2 lg:items-center">
        <div>
          <SectionHeading eyebrow="Role-based guidance" title="Advice that understands the role you are targeting" copy="The local career knowledge base retrieves profile-specific ATS and recruiter guidance instead of returning generic resume advice." />
          <div className="mt-8 flex flex-wrap gap-2.5">
            {roles.map((role) => <span className="rounded-xl border border-zinc-200 bg-white px-4 py-2.5 text-sm font-semibold text-zinc-700 shadow-sm" key={role}>{role}</span>)}
          </div>
        </div>
        <div className="rounded-[1.75rem] border border-indigo-100 bg-indigo-50/60 p-5 sm:p-8">
          <div className="rounded-2xl bg-white p-6 shadow-xl shadow-indigo-900/5">
            <div className="flex gap-4">
              <div className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-zinc-950 text-white"><BriefcaseBusiness className="h-5 w-5" /></div>
              <div><p className="font-bold text-zinc-950">Machine Learning Engineer guidance</p><p className="mt-1 text-sm text-zinc-500">Retrieved from the local career knowledge base</p></div>
            </div>
            <div className="mt-6 space-y-3">
              {["Show model evaluation and measurable quality outcomes.", "Connect MLOps tooling to deployment reliability.", "Prioritize Python, vector search, and data pipeline evidence."].map((item) => (
                <p className="flex gap-3 rounded-xl bg-zinc-50 p-3 text-sm leading-6 text-zinc-700" key={item}><Check className="mt-1 h-4 w-4 shrink-0 text-indigo-600" />{item}</p>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="bg-zinc-50 py-20 sm:py-24">
        <div className="mx-auto grid max-w-7xl gap-8 px-4 sm:px-6 lg:grid-cols-2">
          <ProductPanel icon={InsightStackIcon} eyebrow="Resume optimization" title="Turn weak wording into stronger evidence" copy="Review targeted summary suggestions, action-led bullet rewrites, missing keywords, and clear truthfulness warnings before rebuilding." items={["Improved professional summary", "Impact-focused bullet suggestions", "Keyword and skill-gap recommendations"]} />
          <ProductPanel icon={ExportCubeIcon} eyebrow="Download resume" title="Export a practical draft you can keep editing" copy="Rebuild the optimized content into DOCX, PDF, or Jake's Resume LaTeX using the existing local document pipeline." items={["Editable DOCX output", "Recruiter-friendly PDF output", "Editable LaTeX source"]} />
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 py-20 sm:px-6 sm:py-24">
        <div className="relative overflow-hidden rounded-[2rem] border border-white/10 bg-zinc-950 p-2 text-white shadow-2xl shadow-zinc-950/20">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(99,102,241,0.38),transparent_35%),radial-gradient(circle_at_80%_10%,rgba(34,211,238,0.18),transparent_34%)]" />
          <div className="relative grid gap-10 rounded-[1.65rem] border border-white/10 bg-white/[0.03] px-6 py-12 sm:px-10 lg:grid-cols-[1fr_0.72fr] lg:items-center lg:px-12">
            <div className="text-left">
              <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/10 px-3 py-1.5 text-xs font-bold uppercase tracking-[0.18em] text-cyan-200">
                <LockKeyhole className="h-3.5 w-3.5" />
                Private local workflow
              </div>
              <h2 className="mt-5 max-w-2xl text-3xl font-bold tracking-tight sm:text-4xl">Make the next application more deliberate.</h2>
              <p className="mt-4 max-w-xl text-sm leading-7 text-zinc-300">Upload a resume, match it to the role, and leave with a recruiter-ready improvement plan plus editable exports. No paid service required.</p>
              <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                <Button asChild className="w-full justify-center bg-white text-zinc-950 hover:bg-zinc-100 sm:w-auto">
                  <Link href="/upload">Upload resume <ArrowRight className="h-4 w-4" /></Link>
                </Button>
                <Button asChild variant="outline" className="w-full justify-center border-white/15 bg-white/5 text-white hover:bg-white/10 sm:w-auto">
                  <Link href="/upload#job-description">Analyze a job description</Link>
                </Button>
              </div>
            </div>
            <div className="overflow-hidden rounded-3xl border border-white/10 bg-white/10 p-4 backdrop-blur">
              <CareerFlowIllustration className="h-52 w-full sm:h-60" />
              <div className="grid gap-3 sm:grid-cols-2">
                {["ATS score and skill match", "Explainable recommendations", "DOCX, PDF, and LaTeX outputs", "Optional local account"].map((item) => (
                  <div className="rounded-2xl border border-white/10 bg-zinc-950/35 p-4 text-sm font-semibold text-zinc-100" key={item}>
                    {item}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      <footer className="border-t border-zinc-200 bg-zinc-50">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-8 text-sm text-zinc-500 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <div>
            <div className="flex items-center gap-2 font-bold text-zinc-900"><FileCheck2 className="h-4 w-4 text-indigo-600" />ATS Resume Studio</div>
            <p className="mt-1 text-xs text-zinc-500">Resume matching, explainable scoring, and editable exports.</p>
          </div>
          <p>Local-first analysis. Truthful optimization. No paid API dependency.</p>
        </div>
      </footer>
    </main>
  );
}

function SectionHeading({ eyebrow, title, copy, dark = false }: { eyebrow: string; title: string; copy: string; dark?: boolean }) {
  return (
    <div className="max-w-2xl">
      <p className={`text-xs font-bold uppercase tracking-[0.2em] ${dark ? "text-cyan-300" : "text-indigo-600"}`}>{eyebrow}</p>
      <h2 className={`mt-4 text-3xl font-bold tracking-[-0.03em] sm:text-4xl ${dark ? "text-white" : "text-zinc-950"}`}>{title}</h2>
      <p className={`mt-4 text-base leading-7 ${dark ? "text-zinc-400" : "text-zinc-600"}`}>{copy}</p>
    </div>
  );
}

function ProductPanel({ icon: Icon, eyebrow, title, copy, items }: { icon: ComponentType<{ className?: string }>; eyebrow: string; title: string; copy: string; items: string[] }) {
  return (
    <article className="reveal-card rounded-[1.75rem] border border-zinc-200 bg-white p-7 sm:p-9">
      <div className="grid h-14 w-14 place-items-center rounded-2xl bg-gradient-to-br from-indigo-50 to-cyan-50 shadow-lg shadow-indigo-600/10"><Icon className="h-11 w-11" /></div>
      <p className="mt-7 text-xs font-bold uppercase tracking-[0.18em] text-indigo-600">{eyebrow}</p>
      <h2 className="mt-3 text-2xl font-bold tracking-tight text-zinc-950">{title}</h2>
      <p className="mt-3 text-sm leading-7 text-zinc-600">{copy}</p>
      <div className="mt-6 space-y-3">
        {items.map((item) => <p className="flex items-center gap-3 text-sm font-medium text-zinc-700" key={item}><Check className="h-4 w-4 text-emerald-600" />{item}</p>)}
      </div>
    </article>
  );
}
