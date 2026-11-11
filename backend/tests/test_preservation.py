import tempfile
from pathlib import Path
from unittest.mock import patch

import fitz

from app.services.ats.ats_score import calculate_ats_score
from app.services.llm.resume_optimizer import project_selected_text, rewrite_bullet
from app.services.parser.resume_parser import extract_resume_data
from app.services.rebuilder.latex_compiler import LatexCompilationError, compile_latex_source
from app.services.rebuilder.latex_resume import build_jakes_resume, styled_latex
from app.services.rebuilder.preserved_pdf import preserve_pdf


def test_pipe_project_titles_and_uppercase_bullet_continuations():
    text = """Taylor Kim
Projects
Acme | Enterprise AI SQL Copilot
Python, FastAPI, LangGraph, SQL
- Modeled 20 tables and added 80,034
SPIDER examples to retrieval, retaining evaluation evidence.
Acme | Enterprise FSD & Capital-Markets Conversational Platform
Rasa, FastAPI, Python SDKs, MCP, AWS
- Automated a 4-stage service workflow.
Education
Bachelor of Science
"""
    data = extract_resume_data(text)
    assert len(data["projects"]) == 2
    assert "80,034 SPIDER examples" in data["projects"][0]["bullets"][0]
    latex = build_jakes_resume(data, {})
    assert "Enterprise AI SQL Copilot" in latex
    assert "Enterprise FSD" in latex
    assert "Bachelor of Science" in latex


def test_unselected_score_preserves_source_and_does_not_add_sections():
    text = "Taylor Kim\nSkills\nPython\nProjects\nDashboard\n- Built Python APIs.\nCertifications\nExample Certificate"
    data = extract_resume_data(text)
    assert project_selected_text(text, data, {}) == text
    score = calculate_ats_score(text, "Java and Python")
    assert "java" not in score["matched_keywords"]
    assert score == calculate_ats_score(project_selected_text(text, data, {}), "Java and Python")


def test_keyword_matching_does_not_award_substring_matches():
    score = calculate_ats_score("Taylor Kim\nSkills\nJavaScript\nBuilt services.", "Java")
    assert "java" in score["missing_terms"]


def test_rewrite_retains_metrics_and_avoids_fake_ownership():
    result = rewrite_bullet("Responsible for developing Python APIs used by 120 teams.", [])
    assert result["improved"] == "Developed Python APIs used by 120 teams."
    unchanged = "Helped a team evaluate their model."
    assert rewrite_bullet(unchanged, ["AWS"])["improved"] == unchanged


def test_latex_bold_runs_keep_spaces_and_word_boundaries():
    original = "Built Python APIs with retrieval."
    data = {"document_profile": {"text_styles": {original: ["Python APIs", "with", "API"]}}}
    result = styled_latex(original, data)
    assert result == r"Built \textbf{Python APIs} \textbf{with} retrieval."


def test_pdf_keeps_original_pages_and_unselected_content_when_rewrite_cannot_fit(tmp_path):
    source = tmp_path / "source.pdf"
    dest = tmp_path / "output.pdf"
    with fitz.open() as doc:
        page = doc.new_page()
        page.insert_text((50, 50), "Taylor Kim\nBuilt Python APIs.\nSecond project stays here.")
        doc.save(source)
    result = preserve_pdf(source, dest, {}, {"improved_bullets": [{"original": "Built Python APIs.", "improved": "Very long replacement. " * 100}]})
    assert result["page_count"] == 1
    assert result["applied_changes"] == 0
    assert result["skipped_changes"]
    with fitz.open(source) as old, fitz.open(dest) as new:
        assert old[0].get_text() == new[0].get_text()
        assert old[0].get_pixmap().samples == new[0].get_pixmap().samples


def test_native_compile_rejects_page_growth(tmp_path):
    class Success:
        returncode = 0
        stdout = stderr = ""

    def compile_fake(command, **kwargs):
        with fitz.open() as doc:
            doc.new_page()
            doc.new_page()
            doc.save(Path(kwargs["cwd"]) / "resume.pdf")
        return Success()

    with patch("app.services.rebuilder.latex_compiler.find_latex_compiler", return_value={"name": "test", "path": "test", "executable": "tectonic"}), patch("app.services.rebuilder.latex_compiler.subprocess.run", side_effect=compile_fake):
        try:
            compile_latex_source("test", "test", max_pages=1)
        except LatexCompilationError as exc:
            assert "needs 2 pages" in str(exc)
        else:
            raise AssertionError("A two-page output must not be returned for a one-page input")


def test_standard_pdf_font_allows_shorter_edits_without_changing_other_text(tmp_path):
    source, dest = tmp_path / "original.pdf", tmp_path / "edited.pdf"
    original = "Responsible for developing Python APIs used by 120 teams."
    improved = "Developed Python APIs used by 120 teams."
    with fitz.open() as doc:
        page = doc.new_page()
        page.insert_text((50, 50), "Taylor Kim\n- " + original + "\nSecond project remains.", fontsize=10)
        doc.save(source)
    result = preserve_pdf(source, dest, {}, {"improved_bullets": [{"original": original, "improved": improved}]})
    assert result["applied_changes"] == 1, result
    with fitz.open(dest) as doc:
        text = doc[0].get_text(sort=True)
        assert improved in text
        assert "- " + improved in text, "The bullet marker and rewrite must remain on the same baseline"
        assert "Second project remains." in text and "Taylor Kim" in text
        assert len(doc) == 1
