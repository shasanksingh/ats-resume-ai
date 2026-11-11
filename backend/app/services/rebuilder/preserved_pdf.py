"""Apply only requested edits to the existing PDF; never rebuild untouched pages."""
import html
import re
import tempfile
import unicodedata
from pathlib import Path

import fitz
from app.services.parser.document_profile import bold_runs


def styled_text(text: str, bold_phrases: list[str], escape=html.escape) -> str:
    phrases = sorted(set(p for p in bold_phrases if p and p in text), key=len, reverse=True)
    if not phrases:
        return escape(text)
    pattern = re.compile(r"(?<!\w)(" + "|".join(re.escape(p) for p in phrases) + r")(?!\w)")
    return "".join(("<b>" + escape(part) + "</b>") if index % 2 else escape(part)
                   for index, part in enumerate(pattern.split(text)))


def preserve_pdf(source: Path, destination: Path, structured: dict, optimization: dict) -> dict:
    changes = [(item["original"], item["improved"]) for item in optimization.get("improved_bullets", [])]
    if optimization.get("improved_summary") and structured.get("summary"):
        changes.insert(0, (structured["summary"], optimization["improved_summary"]))
    changes = [(old, new) for old, new in changes if old.strip() != new.strip()]
    applied, skipped = [], []
    runtime = Path(__file__).resolve().parents[4] / ".local"
    runtime.mkdir(exist_ok=True)
    with fitz.open(source) as doc, tempfile.TemporaryDirectory(prefix="resume-fonts-", dir=runtime) as temp:
        for original, improved in changes:
            matches = [(page.number, page.search_for(original)) for page in doc]
            matches = [(number, rects) for number, rects in matches if rects]
            source_text = " ".join(" ".join(page.get_text().split()) for page in doc)
            if len(matches) != 1 or source_text.count(" ".join(original.split())) > 1:
                skipped.append({"original": original, "reason": "The exact text could not be located uniquely; original retained."})
                continue
            number, rects = matches[0]
            page = doc[number]
            box = fitz.Rect(rects[0])
            for rect in rects[1:]:
                box |= rect
            # Disjoint occurrences or columns must never be erased together.
            spans = [s for b in page.get_text("dict")["blocks"] for line in b.get("lines", []) for s in line["spans"] if (fitz.Rect(s["bbox"]) & box).height > 1 and (fitz.Rect(s["bbox"]) & box).width > .1]
            if not spans or box.height > page.rect.height * .3:
                skipped.append({"original": original, "reason": "Text crosses a layout boundary; original retained."})
                continue
            regular = max(spans, key=lambda s: len(s["text"]) if not s["flags"] & 16 else 0)
            size = regular["size"]
            css_faces = []
            font_names = {}
            for entry in page.get_fonts():
                name, extension, _, buffer = doc.extract_font(entry[0])
                if not buffer:
                    continue
                clean_name = name.split("+")[-1]
                font_names[clean_name] = (entry[0], buffer, extension)
            # Reuse the actual embedded regular/bold fonts, including Latin Modern.
            for weight, span in (("normal", regular), ("bold", next((s for s in spans if s["flags"] & 16), regular))):
                found = font_names.get(span["font"].split("+")[-1])
                if not found and span["font"].lower() in fitz.Base14_fontdict:
                    standard = fitz.Font(fontname=span["font"])
                    found = (weight, standard.buffer, "otf")
                if found:
                    xref, buffer, extension = found
                    filename = f"font-{xref}.{extension}"
                    (Path(temp) / filename).write_bytes(buffer)
                    css_faces.append(f"@font-face{{font-family:original;src:url('{filename}');font-weight:{weight};}}")
            if not css_faces:
                skipped.append({"original": original, "reason": "The original font is not reusable; original retained."})
                continue
            bold = bold_runs([{"spans": spans}])
            content = '<div>' + styled_text(improved, bold) + '</div>'
            color = '#%06x' % regular.get('color', 0)
            css = ''.join(css_faces) + f"*{{margin:0;padding:0}}div{{font-family:original;font-size:{size}pt;line-height:1.04;color:{color}}}"
            # Trial rendering before any redaction. Oversized changes stay out of
            # the PDF instead of deleting data, shrinking the page, or adding pages.
            with fitz.open() as trial:
                canvas = trial.new_page(width=page.rect.width, height=page.rect.height)
                render_box = fitz.Rect(box.x0, box.y0 - size * .2, box.x1 + .1, box.y1 + size * .03)
                spare, _ = canvas.insert_htmlbox(render_box, content, css=css, archive=fitz.Archive(temp), scale_low=1)
                if spare < 0:
                    skipped.append({"original": original, "reason": "Rewrite does not fit at the original font size; shorten it or use the LaTeX layout."})
                    continue
                # A subset font can lack newly introduced glyphs. Verify the
                # rendered text before removing anything from the source.
                normalize = lambda value: re.sub(r"\s+", "", unicodedata.normalize("NFKC", value).replace("\u00ad", "-"))
                if normalize(canvas.get_text(sort=True)) != normalize(improved):
                    skipped.append({"original": original, "reason": "The original font could not render the rewrite completely; original retained."})
                    continue
                trial_spans = [s for b in canvas.get_text("dict")["blocks"] for line in b.get("lines", []) for s in line["spans"]]
                offset = min(s["origin"][1] for s in spans) - min(s["origin"][1] for s in trial_spans)
                shifted = fitz.Rect(0, offset, page.rect.width, page.rect.height + offset)
                for rect in rects:
                    page.add_redact_annot(rect, fill=(1, 1, 1))
                page.apply_redactions(images=0, graphics=0)
                page.show_pdf_page(shifted, trial, 0)
                applied.append({"original": original, "improved": improved})
        destination.parent.mkdir(parents=True, exist_ok=True)
        doc.save(destination, garbage=3, deflate=True)
        count = len(doc)
    return {"page_count": count, "original_page_count": count, "layout_preserved": True,
            "applied_changes": len(applied), "applied_edits": applied, "skipped_changes": skipped}
