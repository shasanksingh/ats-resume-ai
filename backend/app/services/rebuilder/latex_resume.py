from pathlib import Path
from typing import Dict

from app.core.config import UPLOAD_DIR
from app.services.rebuilder.preserved_pdf import styled_text


OUTPUT_DIR = UPLOAD_DIR / "optimized"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

LATEX_REPLACEMENTS = {
    "→": r"\(\rightarrow\)",
    "≥": r"\(\geq\)",
    "≤": r"\(\leq\)",
    "•": r"\textbullet{}",
    "ﬁ": "fi",
    "ﬂ": "fl",
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
        contact_items.append(rf"\faPhone\ \href{{tel:{phone}}}{{{phone}}}")
    if email:
        safe_email = latex_escape(email)
        contact_items.append(rf"\faEnvelope\ \href{{mailto:{safe_email}}}{{\underline{{{safe_email}}}}}")
    link_icons = {"linkedin": r"\faLinkedin", "github": r"\faGithub", "portfolio": r"\faGlobe"}
    for key, label in (("linkedin", "LinkedIn"), ("github", "GitHub"), ("portfolio", "Portfolio")):
        if links.get(key):
            contact_items.append(
                rf"{link_icons[key]}\ \href{{{latex_escape(links[key])}}}{{\underline{{{label}}}}}"
            )
    if structured.get("location"):
        contact_items.append(latex_escape(structured["location"]))

    builders = {
        "summary": lambda: build_summary_section(structured, optimized),
        "skills": lambda: build_skills_section(structured),
        "experience": lambda: build_experience_section(structured, optimized),
        "projects": lambda: build_projects_section(structured, optimized),
        "education": lambda: build_education_section(structured),
        "certifications": lambda: build_certifications_section(structured),
    }
    order = list(dict.fromkeys([*structured.get("sections", {}), *builders]))
    sections = [builders[key]() for key in order if key in builders]

    contact = r" $|$ ".join(contact_items)
    body = "\n\n".join(section for section in sections if section)

    profile = structured.get("document_profile", {})
    size = profile.get("body_font_size", 9)
    leading = round(size * 1.08, 2)
    name_size = profile.get("name_font_size", 18.8)
    font = profile.get("font_name", "").lower()
    font_setup = r"\usepackage{lmodern}"
    if "times" in font:
        font_setup = r"\usepackage{newtxtext}"
    elif profile.get("font_family") == "sans":
        font_setup = r"\usepackage{helvet}\renewcommand{\familydefault}{\sfdefault}"
    return rf"""\documentclass[letterpaper]{{article}}

\usepackage[T1]{{fontenc}}
{font_setup}
\usepackage[paperwidth={profile.get('width', 612)}bp,paperheight={profile.get('height', 792)}bp,left=0.43in,right=0.43in,top=0.15in,bottom=0.12in]{{geometry}}
\usepackage{{titlesec}}
\usepackage{{enumitem}}
\usepackage[hidelinks]{{hyperref}}
\usepackage{{fancyhdr}}
\usepackage[english]{{babel}}
\usepackage{{tabularx}}
\usepackage{{fontawesome5}}
\usepackage{{microtype}}
\ifdefined\pdfgentounicode
  \input{{glyphtounicode}}
  \pdfgentounicode=1
\fi

\pagestyle{{fancy}}
\fancyhf{{}}
\renewcommand{{\headrulewidth}}{{0pt}}
\renewcommand{{\footrulewidth}}{{0pt}}

\setlength{{\tabcolsep}}{{0in}}
\setlength{{\parindent}}{{0pt}}
\setlength{{\parskip}}{{0pt}}
\setlength{{\emergencystretch}}{{1em}}
\urlstyle{{same}}
\raggedbottom
\raggedright

\titleformat{{\section}}{{\fontsize{{9.4}}{{10}}\selectfont\bfseries}}{{}}{{0em}}{{}}[\titlerule]
\titlespacing*{{\section}}{{0pt}}{{4pt}}{{2pt}}

\newcommand{{\resumeItem}}[1]{{\item #1}}
\newcommand{{\resumeSubheading}}[4]{{
  \item
  \begin{{tabularx}}{{\linewidth}}[t]{{@{{}}Xr@{{}}}}
    \textbf{{#1}} & #2 \\
    \textit{{#3}} & \textit{{#4}} \\
  \end{{tabularx}}
}}
\newcommand{{\resumeProjectHeading}}[2]{{
  \item
  \begin{{tabularx}}{{\linewidth}}{{@{{}}Xr@{{}}}}
    #1 & #2 \\
  \end{{tabularx}}
}}
\newcommand{{\resumeSubHeadingListStart}}{{\begin{{itemize}}[leftmargin=0pt,label={{}},itemsep=1pt,topsep=0pt,parsep=0pt,partopsep=0pt]}}
\newcommand{{\resumeSubHeadingListEnd}}{{\end{{itemize}}}}
\newcommand{{\resumeItemListStart}}{{\begin{{itemize}}[leftmargin=12pt,label=\textbullet,itemsep=0pt,topsep=0pt,parsep=0pt,partopsep=0pt]}}
\newcommand{{\resumeItemListEnd}}{{\end{{itemize}}}}

\begin{{document}}
\fontsize{{{size}}}{{{leading}}}\selectfont

{{\centering
  {{\fontsize{{{name_size}}}{{{name_size + 1}}}\selectfont\scshape {name}}} \\[1pt]
  {contact}\par}}

{body}

\end{{document}}
"""


def build_summary_section(structured: Dict, optimized: Dict) -> str:
    summary = optimized.get("improved_summary") or structured.get("summary") or ""
    if not summary:
        return ""
    return "\\section{Professional Summary}\n" + styled_latex(summary, structured, structured.get("summary", ""))


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
    size = structured.get("document_profile", {}).get("skill_font_size", 9)
    return rf"\section{{Technical Skills}}" + "\n" + rf"{{\fontsize{{{size}}}{{{round(size * 1.04, 2)}}}\selectfont" + "\n" + "\\\\\n".join(lines) + "\\par}"


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
            rf"{{{latex_escape(role.get('title') or '')}}}{{{latex_escape(role.get('location') or '')}}}"
        )
        bullets = [
            rf"\resumeItem{{{styled_latex(rewrites.get(bullet, bullet), structured, bullet)}}}"
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
        if project.get("url"):
            title += rf"\ \href{{{latex_escape(project['url'])}}}{{\faGithub\ GitHub}}"
        if technologies:
            title += rf"\newline\emph{{{technologies}}}"
        heading = rf"\resumeProjectHeading{{{title}}}{{{latex_escape(project.get('date') or '')}}}"
        project_bullets = project.get("bullets", [])
        if not project_bullets and project.get("description"):
            project_bullets = [project.get("description")]
        bullets = [
            rf"\resumeItem{{{styled_latex(rewrites.get(bullet, bullet), structured, bullet)}}}"
            for bullet in project_bullets
        ]
        if bullets:
            heading += "\n\\resumeItemListStart\n" + "\n".join(bullets) + "\n\\resumeItemListEnd"
        entries.append(heading)
    return "\\section{Projects}\n\\resumeSubHeadingListStart\n" + "\n".join(entries) + "\n\\resumeSubHeadingListEnd"


def build_education_section(structured: Dict) -> str:
    education = structured.get("education_entries") or []
    if not education:
        lines = structured.get("education") or []
        return "\\section{Education}\n" + "\\\\\n".join(latex_escape(item) for item in lines) if lines else ""
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


def styled_latex(value: str, structured: Dict, original: str = "") -> str:
    escape = lambda text: "".join(LATEX_REPLACEMENTS.get(char, char) for char in text)
    phrases = structured.get("document_profile", {}).get("text_styles", {}).get(original or value, [])
    return styled_text(value, phrases, escape).replace("<b>", r"\textbf{").replace("</b>", "}")
