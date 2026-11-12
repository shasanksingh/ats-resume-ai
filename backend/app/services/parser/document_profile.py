"""Retain PDF layout metadata alongside the semantic resume representation."""
from collections import Counter
from pathlib import Path
import re

import fitz

from app.services.parser.resume_parser import (
    SECTION_ALIASES, extract_links_from_pdf, extract_resume_data, extract_text_from_pdf,
)


def bold_runs(lines, rects=None):
    """Join adjacent bold glyph spans; do not turn every word into a style rule."""
    runs, run = [], ""
    for line in lines:
        for span in line["spans"]:
            if rects and not any((fitz.Rect(span["bbox"]) & rect).height > 1 and (fitz.Rect(span["bbox"]) & rect).width > .1 for rect in rects):
                continue
            if span["flags"] & 16 or "bold" in span["font"].lower():
                run += span["text"]
            elif run:
                if not span["text"].strip():
                    run += " "
                    continue
                runs.append(" ".join(run.split()))
                run = ""
        if run:
            run += " "
    if run.strip():
        runs.append(" ".join(run.split()))
    return [run for run in runs if len(run) > 1]


def load_pdf_resume(path: str | Path) -> tuple[str, dict]:
    text = extract_text_from_pdf(str(path))
    data = extract_resume_data(text)
    data["links"] = {**data.get("links", {}), **extract_links_from_pdf(str(path))}
    with fitz.open(path) as doc:
        lines = [line for page in doc for block in page.get_text("dict")["blocks"]
                 for line in block.get("lines", [])]
        spans = [span for line in lines for span in line["spans"] if span["text"].strip()]
        body = [s for s in spans if "Awesome" not in s["font"] and not s["flags"] & 16]
        sizes = Counter({})
        for span in body:
            sizes[round(span["size"], 1)] += len(span["text"])
        body_size = sizes.most_common(1)[0][0] if sizes else 10.0
        fonts = Counter()
        for span in body:
            fonts[span["font"]] += len(span["text"])
        font = fonts.most_common(1)[0][0] if fonts else "Helvetica"
        family = "serif" if re.search(r"roman|times|serif|cambria|garamond", font, re.I) else "sans"
        bold = [s["text"].strip() for s in spans if (s["flags"] & 16 or "bold" in s["font"].lower()) and len(s["text"].strip()) > 2]
        data["document_profile"] = {
            "page_count": len(doc), "width": doc[0].rect.width, "height": doc[0].rect.height,
            "font_family": family, "font_name": font, "body_font_size": body_size,
            "name_font_size": max(s["size"] for s in spans) if spans else 18,
            "bold_phrases": list(dict.fromkeys(bold)),
        }
        first_spans = [span for block in doc[0].get_text("dict")["blocks"]
                       for line in block.get("lines", []) for span in line["spans"] if span["text"].strip()]
        if first_spans:
            data["document_profile"]["margins"] = {
                "left": round(max(18, min(54, min(s["bbox"][0] for s in first_spans))), 2),
                "right": round(max(18, min(54, doc[0].rect.width - max(s["bbox"][2] for s in first_spans))), 2),
                "top": round(max(8, min(36, min(s["bbox"][1] for s in first_spans))), 2),
                "bottom": 18,
            }
        # Recover separate role/location columns using their actual coordinates,
        # rather than recognizing a fixed list of cities from one resume.
        for role in data.get("experience", []):
            title = role.get("title", "")
            for line in lines:
                value = " ".join("".join(s["text"] for s in line["spans"]).split())
                if value and title.startswith(value + " "):
                    for other in lines:
                        location = " ".join("".join(s["text"] for s in other["spans"]).split())
                        if (location and abs(line["bbox"][1] - other["bbox"][1]) < 2
                                and other["bbox"][0] > line["bbox"][2] + 12
                                and title == value + " " + location):
                            role["title"], role["location"] = value, location
        texts = [data.get("summary", "")]
        texts.extend(bullet for entry in [*data.get("experience", []), *data.get("projects", [])] for bullet in entry.get("bullets", []))
        styles = {}
        for value in texts:
            if not value:
                continue
            for page in doc:
                rects = page.search_for(value)
                if rects:
                    page_lines = [line for block in page.get_text("dict")["blocks"] for line in block.get("lines", [])]
                    styles[value] = bold_runs(page_lines, rects)
        data["document_profile"]["text_styles"] = styles
        # Table labels in PDFs often have no colon. Recover them from bold spans,
        # instead of treating the entire table as one long comma-separated skill.
        groups = {}
        skill_sizes = Counter()
        in_skills = False
        group = None
        aliases = {alias: section for section, values in SECTION_ALIASES.items() for alias in values}
        heading_sizes = [s["size"] for line in lines
                         if " ".join("".join(s["text"] for s in line["spans"]).split()).lower().rstrip(":") in aliases
                         for s in line["spans"]]
        data["document_profile"]["heading_font_size"] = round(max(heading_sizes), 2) if heading_sizes else round(body_size * 1.15, 2)
        for line in sorted(lines, key=lambda item: (item["bbox"][1], item["bbox"][0])) if len(doc) == 1 else lines:
            parts = line["spans"]
            value = " ".join("".join(s["text"] for s in parts).split())
            section = aliases.get(value.lower().rstrip(":"))
            if section:
                in_skills = section == "skills"
                continue
            if not in_skills:
                continue
            for span in parts:
                skill_sizes[round(span["size"], 1)] += len(span["text"].strip())
            prefix = []
            remainder = []
            for span in parts:
                if not remainder and (span["flags"] & 16 or "bold" in span["font"].lower()):
                    prefix.append(span["text"])
                else:
                    remainder.append(span["text"])
            if prefix:
                group = " ".join("".join(prefix).split()).rstrip(":")
                groups.setdefault(group, "")
            if group:
                groups[group] += " " + "".join(remainder)
        if groups and all(value.strip() for value in groups.values()):
            data["skill_groups"] = {label: [x.strip() for x in re.split(r"[,;]", value) if x.strip()] for label, value in groups.items()}
        data["document_profile"]["skill_font_size"] = skill_sizes.most_common(1)[0][0] if skill_sizes else body_size
        # Keep each project's own hyperlink, rather than discarding it into the
        # global GitHub contact link.
        for project in data.get("projects", []):
            project["name"] = re.sub(r"\s*[§\x00-\x1f\x7f-\x9f]\s*GitHub\s*$", "", project["name"]).strip()
            for page in doc:
                rects = page.search_for(project["name"])
                for rect in rects:
                    for link in page.get_links():
                        if link.get("uri", "").startswith(("https://", "http://")) and abs(link["from"].y0 - rect.y0) < 12:
                            project["url"] = link["uri"]
    return text, data
