import shutil
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict
import fitz

from app.services.rebuilder.latex_resume import OUTPUT_DIR, unique_output_path


class LatexCompilerUnavailable(RuntimeError):
    pass


class LatexCompilationError(RuntimeError):
    pass


def compiler_status() -> Dict:
    compiler = find_latex_compiler()
    if not compiler:
        return {
            "available": True,
            "compiler": "Original PDF layout",
            "native_compiler": False,
            "message": "Original-layout PDF preview is ready. Install MiKTeX, TeX Live, or Tectonic for native LaTeX compilation.",
        }
    return {
        "available": True,
        "compiler": compiler["name"],
        "native_compiler": True,
        "message": f"{compiler['name']} is ready for local PDF compilation.",
    }


def compile_latex_source(source: str, basename: str, max_pages: int | None = None) -> Dict:
    compiler = find_latex_compiler()
    if not compiler:
        raise LatexCompilerUnavailable(
            "Native LaTeX compiler not found; the original PDF layout is retained."
        )

    destination = unique_output_path(f"{Path(basename).stem}_latex", "pdf")
    output_name = destination.name
    runtime = Path(__file__).resolve().parents[4] / ".local"
    runtime.mkdir(exist_ok=True)
    cache = runtime / "tectonic-cache"
    cache.mkdir(exist_ok=True)
    environment = {**os.environ, "TECTONIC_CACHE_DIR": str(cache), "XDG_CACHE_HOME": str(cache)}
    with tempfile.TemporaryDirectory(prefix="ats-latex-", dir=runtime) as temp:
        temp_dir = Path(temp)
        tex_path = temp_dir / "resume.tex"
        tex_path.write_text(source, encoding="utf-8")
        command = build_command(compiler, tex_path, temp_dir)
        try:
            result = subprocess.run(
                command,
                cwd=temp_dir,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=240,
                check=False,
                env=environment,
            )
        except subprocess.TimeoutExpired as exc:
            raise LatexCompilationError("LaTeX compilation exceeded the 240-second limit.") from exc

        pdf_path = temp_dir / "resume.pdf"
        log = "\n".join(part for part in (result.stdout, result.stderr) if part).strip()
        if result.returncode != 0 or not pdf_path.is_file():
            detail = log[-1800:] if log else "The compiler did not produce a PDF."
            raise LatexCompilationError(f"LaTeX compilation failed: {detail}")

        with fitz.open(pdf_path) as pdf:
            page_count = len(pdf)
        if max_pages and page_count > max_pages:
            raise LatexCompilationError(f"LaTeX needs {page_count} pages; the original has {max_pages}. Original layout retained to preserve all content and font sizes.")

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(pdf_path, destination)

    return {
        "filename": output_name,
        "path": f"optimized/{output_name}",
        "download_url": f"/files/optimized/{output_name}",
        "format": "pdf",
        "compiler": compiler["name"],
        "native_compiler": True,
        "fallback": False,
        "log_excerpt": log[-600:],
        "page_count": page_count,
        "original_page_count": max_pages,
    }


def render_latex_preview_pdf(
    structured: Dict,
    optimized: Dict,
    basename: str,
    reason: str = "Native LaTeX compiler unavailable; rendered with the built-in PDF preview engine.",
) -> Dict:
    from app.services.rebuilder.resume_rebuilder import build_pdf

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"{Path(basename).stem}_latex_preview.pdf"
    build_pdf(path, structured, optimized)
    return {
        "filename": path.name,
        "path": f"optimized/{path.name}",
        "download_url": f"/files/optimized/{path.name}",
        "format": "pdf",
        "compiler": "Built-in PDF renderer",
        "native_compiler": False,
        "fallback": True,
        "log_excerpt": reason,
    }


def find_latex_compiler() -> Dict | None:
    portable = Path(__file__).resolve().parents[4] / ".local/tectonic/tectonic.exe"
    if portable.is_file():
        return {"name": "Tectonic", "path": str(portable), "executable": "tectonic"}
    candidates = [
        ("Tectonic", "tectonic"),
        ("pdfLaTeX", "pdflatex"),
        ("LaTeXmk", "latexmk"),
    ]
    for name, executable in candidates:
        path = shutil.which(executable)
        if path:
            return {"name": name, "path": path, "executable": executable}

    common_paths = [
        Path.home() / "AppData/Local/Programs/MiKTeX/miktex/bin/x64/pdflatex.exe",
        Path("C:/Program Files/MiKTeX/miktex/bin/x64/pdflatex.exe"),
    ]
    texlive_root = Path("C:/texlive")
    if texlive_root.is_dir():
        common_paths.extend(sorted(texlive_root.glob("*/bin/windows/pdflatex.exe"), reverse=True))

    for path in common_paths:
        if path.is_file():
            return {"name": "pdfLaTeX", "path": str(path), "executable": "pdflatex"}
    return None


def build_command(compiler: Dict, tex_path: Path, output_dir: Path) -> list[str]:
    if compiler["executable"] == "tectonic":
        return [
            compiler["path"],
            "--keep-logs",
            "--outdir",
            str(output_dir),
            str(tex_path),
        ]
    if compiler["executable"] == "latexmk":
        return [
            compiler["path"],
            "-pdf",
            "-interaction=nonstopmode",
            "-halt-on-error",
            f"-outdir={output_dir}",
            str(tex_path),
        ]
    return [
        compiler["path"],
        "--enable-installer",
        "-interaction=nonstopmode",
        "-halt-on-error",
        f"-output-directory={output_dir}",
        str(tex_path),
    ]
