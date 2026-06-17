from pathlib import Path
from typing import Dict

from app.core.config import UPLOAD_DIR


OUTPUT_DIR = UPLOAD_DIR / "optimized"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

LATEX_REPLACEMENTS = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
    "–": "--",
    "—": "---",
    "’": "'",
    "“": "``",
    "”": "''",
    "–": "--",
    "—": "---",
    "’": "'",
    "“": "``",
    "”": "''",
}


def generate_latex_resume(
    structured: Dict,
    optimized: Dict,
    basename: str,
    template: str = "jakes",
) -> Dict:
    if template != "jakes":
        raise ValueError("Only the Jake's Resume template is currently supported")

    source = build_jakes_resume(structured, optimized)
    path = unique_output_path(Path(basename).stem, "tex")
    path.write_text(source, encoding="utf-8")
    return {
        "filename": path.name,
        "path": f"optimized/{path.name}",
        "download_url": f"/files/optimized/{path.name}",
        "format": "tex",
        "template": "jakes",
        "latex_source": source,
    }


def unique_output_path(stem: str, extension: str) -> Path:
    base = OUTPUT_DIR / f"{stem}_optimized.{extension}"
    if not base.exists():
        return base
    for index in range(1, 1000):
        candidate = OUTPUT_DIR / f"{stem}_optimized_{index}.{extension}"
        if not candidate.exists():
            return candidate
    raise RuntimeError("Unable to allocate a unique optimized LaTeX filename")


def build_jakes_resume(structured: Dict, optimized: Dict) -> str:
    name = latex_escape(structured.get("name") or "Candidate Name")
    phone = latex_escape(structured.get("phone") or "")
    email = structured.get("email") or ""
    links = structured.get("links") or {}
    contact_items = []

    if phone:
        contact_items.append(rf"\faPhone\ {phone}")
    if email:
        safe_email = latex_escape(email)
        contact_items.append(rf"\faEnvelope\ \href{{mailto:{safe_email}}}{{\underline{{{safe_email}}}}}")
    link_icons = {"linkedin": r"\faLinkedin", "github": r"\faGithub", "portfolio": r"\faGlobe"}
    for key, label in (("linkedin", "LinkedIn"), ("github", "GitHub"), ("portfolio", "Portfolio")):
        if links.get(key):
            contact_items.append(
                rf"{link_icons[key]}\ \href{{{latex_escape(links[key])}}}{{\underline{{{label}}}}}"
            )

    sections = [
        build_summary_section(structured, optimized),
        build_skills_section(structured),
        build_experience_section(structured, optimized),
        build_projects_section(structured, optimized),
        build_education_section(structured),
        build_certifications_section(structured),
    ]

    contact = r" $|$ ".join(contact_items)
    body = "\n\n".join(section for section in sections if section)

    return rf"""\documentclass[letterpaper,10pt]{{article}}

\usepackage[empty]{{fullpage}}
\usepackage{{titlesec}}
\usepackage{{enumitem}}
\usepackage[hidelinks]{{hyperref}}
\usepackage{{fancyhdr}}
\usepackage[english]{{babel}}
\usepackage{{tabularx}}
\usepackage{{fontawesome5}}
\input{{glyphtounicode}}

\pagestyle{{fancy}}
\fancyhf{{}}
\renewcommand{{\headrulewidth}}{{0pt}}
\renewcommand{{\footrulewidth}}{{0pt}}

\addtolength{{\oddsidemargin}}{{-0.65in}}
\addtolength{{\evensidemargin}}{{-0.65in}}
\addtolength{{\textwidth}}{{1.30in}}
\addtolength{{\topmargin}}{{-0.78in}}
\addtolength{{\textheight}}{{1.55in}}
\setlength{{\tabcolsep}}{{0in}}
\urlstyle{{same}}
\raggedbottom
\raggedright
\pdfgentounicode=1

\titleformat{{\section}}{{\vspace{{-5pt}}\scshape\raggedright\large\bfseries}}{{}}{{0em}}{{}}[\titlerule \vspace{{-5pt}}]

\newcommand{{\resumeItem}}[1]{{\item\small{{#1 \vspace{{-2pt}}}}}}
\newcommand{{\resumeSubheading}}[4]{{
  \vspace{{-2pt}}\item
  \begin{{tabular*}}{{0.97\textwidth}}[t]{{l@{{\extracolsep{{\fill}}}}r}}
    \textbf{{#1}} & #2 \\
    \textit{{\small #3}} & \textit{{\small #4}} \\
  \end{{tabular*}}\vspace{{-7pt}}
}}
\newcommand{{\resumeProjectHeading}}[2]{{
  \item
  \begin{{tabular*}}{{0.97\textwidth}}{{l@{{\extracolsep{{\fill}}}}r}}
    \small #1 & #2 \\
  \end{{tabular*}}\vspace{{-7pt}}
}}
\newcommand{{\resumeSubHeadingListStart}}{{\begin{{itemize}}[leftmargin=0.15in,label={{}}]}}
\newcommand{{\resumeSubHeadingListEnd}}{{\end{{itemize}}}}
\newcommand{{\resumeItemListStart}}{{\begin{{itemize}}[leftmargin=0.22in]}}
\newcommand{{\resumeItemListEnd}}{{\end{{itemize}}\vspace{{-5pt}}}}

\begin{{document}}

\begin{{center}}
  \textbf{{\Huge \scshape {name}}} \\ \vspace{{2pt}}
  \small {contact}
\end{{center}}

{body}

\end{{document}}
"""


def build_summary_section(structured: Dict, optimized: Dict) -> str:
    summary = optimized.get("improved_summary") or structured.get("summary") or ""
    if not summary:
        return ""
    return "\\section{Professional Summary}\n" + latex_escape(summary)


def build_skills_section(structured: Dict) -> str:
    groups = structured.get("skill_groups") or {}
    if groups:
        lines = [
            rf"\textbf{{{latex_escape(label)}}}: {latex_escape(', '.join(values))}"
            for label, values in groups.items()
            if values
        ]
    else:
        skills = structured.get("skills") or []
        lines = [rf"\textbf{{Core Skills}}: {latex_escape(', '.join(skills))}"] if skills else []
    if not lines:
        return ""
    return "\\section{Skills}\n" + "\\\\\n".join(lines)


def build_experience_section(structured: Dict, optimized: Dict) -> str:
    experience = structured.get("experience") or []
    if not experience:
        return ""
    rewrites = rewrite_lookup(optimized)
    entries = []
    for role in experience:
        heading = (
            rf"\resumeSubheading"
            rf"{{{latex_escape(role.get('company') or role.get('title') or '')}}}"
            rf"{{{latex_escape(role.get('dates') or '')}}}"
            rf"{{{latex_escape(role.get('title') or '')}}}{{}}"
        )
        bullets = [
            rf"\resumeItem{{{latex_escape(rewrites.get(bullet, bullet))}}}"
            for bullet in role.get("bullets", [])
        ]
        if bullets:
            heading += "\n\\resumeItemListStart\n" + "\n".join(bullets) + "\n\\resumeItemListEnd"
        entries.append(heading)
    return "\\section{Experience}\n\\resumeSubHeadingListStart\n" + "\n".join(entries) + "\n\\resumeSubHeadingListEnd"


def build_projects_section(structured: Dict, optimized: Dict) -> str:
    projects = structured.get("projects") or []
    if not projects:
        return ""
    rewrites = rewrite_lookup(optimized)
    entries = []
    for project in projects:
        name = latex_escape(project.get("name") or "")
        technologies = latex_escape(project.get("technologies") or "")
        title = rf"\textbf{{{name}}}"
        if technologies:
            title += rf" $|$ \emph{{{technologies}}}"
        heading = rf"\resumeProjectHeading{{{title}}}{{{latex_escape(project.get('date') or '')}}}"
        project_bullets = project.get("bullets", [])
        if not project_bullets and project.get("description"):
            project_bullets = [project.get("description")]
        bullets = [
            rf"\resumeItem{{{latex_escape(rewrites.get(bullet, bullet))}}}"
            for bullet in project_bullets
        ]
        if bullets:
            heading += "\n\\resumeItemListStart\n" + "\n".join(bullets) + "\n\\resumeItemListEnd"
        entries.append(heading)
    return "\\section{Projects}\n\\resumeSubHeadingListStart\n" + "\n".join(entries) + "\n\\resumeSubHeadingListEnd"


def build_education_section(structured: Dict) -> str:
    education = structured.get("education_entries") or []
    if not education:
        return ""
    entries = [
        (
            rf"\resumeSubheading"
            rf"{{{latex_escape(item.get('institution') or '')}}}"
            rf"{{{latex_escape(item.get('dates') or '')}}}"
            rf"{{{latex_escape(item.get('degree') or '')}}}"
            rf"{{{latex_escape(item.get('details') or '')}}}"
        )
        for item in education
    ]
    return "\\section{Education}\n\\resumeSubHeadingListStart\n" + "\n".join(entries) + "\n\\resumeSubHeadingListEnd"


def build_certifications_section(structured: Dict) -> str:
    certifications = structured.get("certifications") or []
    if not certifications:
        return ""
    items = "\n".join(rf"\resumeItem{{{latex_escape(item)}}}" for item in certifications)
    return "\\section{Certifications}\n\\resumeItemListStart\n" + items + "\n\\resumeItemListEnd"


def rewrite_lookup(optimized: Dict) -> Dict[str, str]:
    return {
        item.get("original", ""): item.get("improved", "")
        for item in optimized.get("improved_bullets", [])
        if item.get("original") and item.get("improved")
    }


def latex_escape(value: object) -> str:
    normalized = " ".join(str(value).split())
    return "".join(LATEX_REPLACEMENTS.get(char, char) for char in normalized)
