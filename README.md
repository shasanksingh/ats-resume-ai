# ATS Resume Studio

ATS Resume Studio analyzes a PDF resume against a target job description, explains the match score, and uses NVIDIA Mistral to suggest stronger wording. Users select which changes to apply before exporting PDF, DOCX, or compact LaTeX output.

Core analysis and local suggestions work without an AI service. Automatic optimization and custom refinement use an NVIDIA API key configured only on the backend.

## Features

- PDF resume upload with validation, drag/drop support, and progress feedback.
- Layout-aware resume parsing for contact details, location, skills, experience, projects, education, links, and varied section headings.
- Extraction confidence, detected-section diagnostics, and actionable parsing warnings in the analysis dashboard.
- Per-change approval for summaries and bullets across PDF, DOCX, and LaTeX exports.
- The Optimize resume button uses NVIDIA Mistral for stronger suggestions. Selected changes can also be refined with a custom instruction. Resume excerpts and the job description are sent to NVIDIA; the key stays on the backend. Local suggestions remain available if NVIDIA fails.
- Automatic deletion of uploaded PDFs and generated resume files after 24 hours.
- ATS score generation with category breakdown and explainable scoring evidence.
- Job-description matching with matched skills, missing skills, and keyword coverage.
- Local role guidance for software, data, support, electrical, mechanical, civil, business, operations, healthcare, and other roles.
- Truthful optimization that avoids inventing employers, tools, degrees, dates, certifications, or metrics.
- Resume rebuild exports for DOCX, PDF, and Jake's Resume LaTeX.
- Optional local account signup/login backed by SQLite. Guests can still use the full resume workflow.
- End-of-flow feedback capture stored in the local SQLite database for guests and signed-in users.
- Modern Next.js UI with responsive landing, upload, analysis, results, and account pages.

## Tech Stack

- Frontend: Next.js, React, TypeScript, Tailwind CSS, lucide-react.
- Backend: FastAPI, Pydantic, PyMuPDF, python-docx, ReportLab.
- Local retrieval: LangChain, ChromaDB, sentence-transformer embeddings.
- Storage: local filesystem uploads plus optional SQLite account database.
- LaTeX preview: MiKTeX, TeX Live, or Tectonic when installed; original-layout PDF fallback otherwise.

## Project Structure

```text
ats-resume-ai/
  backend/
    app/
      api/routes/              FastAPI route modules
      core/                    Configuration and file safety helpers
      data/                    ATS skill taxonomy
      schemas/                 Pydantic request and response models
      services/
        ats/                   ATS scoring
        auth/                  Optional SQLite account store
        llm/                   Local deterministic optimizer and optional local model helper
        parser/                PDF text extraction and parsing
        rag/                   Local role-guidance retrieval
        rebuilder/             DOCX, PDF, and LaTeX rebuilders
    rag-data/                  Role guidance text corpus
    tests/                     Backend API and service contract tests
  frontend/
    app/                       Next.js routes
      account/                 Optional login/signup
      dashboard/               Analysis workspace
      results/                 Recruiter-grade results and exports
      upload/                  Resume/JD upload flow
    components/                Shared UI, navigation, gauges, visuals
    lib/                       API client and browser storage helpers
```

## Backend Setup

```powershell
cd backend
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend URL:

```text
http://127.0.0.1:8000
```

Useful endpoints:

- `POST /upload/resume`
- `POST /analyze/resume`
- `POST /optimize/resume`
- `POST /optimize/rebuild`
- `POST /optimize/latex`
- `POST /optimize/latex/compile`
- `GET /optimize/latex/status`
- `POST /rag/build`
- `POST /rag/search`
- `POST /auth/signup`
- `POST /auth/login`
- `GET /auth/me`
- `POST /auth/logout`
- `POST /feedback`
- `GET /files/optimized/{filename}`

Optional backend settings:

```env
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
MAX_UPLOAD_SIZE_BYTES=10485760
UPLOAD_DIR=backend/uploads
RAG_DATA_DIR=backend/rag-data
CHROMA_PATH=backend/vector_db
DATABASE_PATH=backend/data/ats_resume.db
MODEL_LOCAL_FILES_ONLY=1
UPLOAD_RETENTION_HOURS=24
CLEANUP_INTERVAL_SECONDS=3600
NVIDIA_API_KEY=replace-with-your-nvidia-api-key
NVIDIA_MODEL=mistralai/mistral-large-4-1t-a52b
NVIDIA_FALLBACK_MODEL=nvidia/nemotron-3.5-super-vl-120b-a12b
NVIDIA_TIMEOUT_SECONDS=120
NVIDIA_MAX_TOKENS=4096
```

## Frontend Setup

For the restored Windows installation, both runtimes and dependencies live on D:.
Start both servers from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1
```

This uses the existing Node installation in `D:\NodeJS\node-v22.23.2-win-x64`
and Python environment in `.local\venv`. Logs, temporary files, and application
caches stay in `.local` on D:. The older `backend\venv` still points to the
removed C: Python installation and should not be used.

To recreate the Python environment using the existing D: Python installation:

```powershell
$env:TEMP = "$PWD\.local\tmp"
$env:TMP = $env:TEMP
$env:PIP_CACHE_DIR = "$PWD\.local\pip-cache"
New-Item -ItemType Directory -Force $env:TEMP | Out-Null
& D:\Software_Install\python.exe -m venv .local\venv
& .\.local\venv\Scripts\python.exe -m pip install -r backend\requirements.txt pytest httpx
```

The NVIDIA request timeout defaults to 120 seconds; the frontend proxy allows
150 seconds so the API can return its own timeout message. Update an existing
`backend/.env` timeout if it still uses 25 seconds.

```powershell
cd frontend
npm install
npm run dev
```

Frontend URL:

```text
http://localhost:3000
```

The frontend uses the same-origin `/api/backend` proxy by default. Use `NEXT_PUBLIC_API_BASE_URL` only when the browser should call FastAPI directly:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

## Optional Accounts

Accounts are optional. Upload, analysis, optimization, and export all work for guest users.

When a user signs up, the backend stores:

- name
- normalized email
- salted password hash
- session token
- creation timestamp

The SQLite database defaults to:

```text
backend/data/ats_resume.db
```

Feedback submitted from the results page is stored in the same SQLite database with the visitor id, optional signed-in user id, rating, message, page, and timestamp.

## LaTeX Preview

The results page generates LaTeX source using the uploaded resume's page size, margins, font family, sizes, bold emphasis, and section order. It retains separate projects, contact icons, links, and source data. For one-page inputs, compilation measures content height and adjusts line and section spacing within bounded limits to use the page without changing font sizes or dropping content. The downloadable source is updated to match the compiled preview. Sparse resumes keep reasonable spacing rather than stretching indefinitely.

Feedback appears beneath the results only after a PDF preview is generated successfully, once per uploaded resume after submission (or once per browser session after dismissal). Optimization reports NVIDIA failures explicitly, labels unchanged suggestions as retained originals without duplicating them as rewrites, and recalculates scores only for selected or exported content.

AI rewrites run in batches of two bullets (up to four concurrent requests). The primary model gets at most 45 seconds before NVIDIA Nemotron Super is tried with reasoning disabled within the same total timeout. The key and both models remain on the backend. Empty, truncated, or incomplete responses are treated as failures; authentication errors are reported directly. Set `NVIDIA_FALLBACK_MODEL` to an empty value to disable the fallback.

For native compilation, install one of:

- MiKTeX
- TeX Live
- Tectonic

On the restored Windows setup, the portable compiler is at `.local/tectonic/tectonic.exe`; its downloaded packages stay in `.local/tectonic-cache` on D:. These local installations are not committed.

PDF export edits the original document at its original font size. If a rewrite does not fit or its font cannot render it faithfully, the original text remains and the UI lists the skipped edit. LaTeX compilation checks page count and content retention; if it fails those checks or no compiler is available, the preview uses the original PDF layout. A one-page input is never returned as a two-page PDF. DOCX pagination depends on the word processor.

The score card distinguishes the original score, an estimate for selected changes, and the score extracted from the exported document. Deselecting or refining changes recalculates the estimate; unselected suggestions do not improve it. Additional confirmed skills are included in the LaTeX and DOCX layouts, while original-layout PDF export retains the existing skills section.

## Workflow

1. Upload a text-based PDF resume.
2. Paste the complete target job description.
3. ATS analysis starts automatically and reports extraction confidence.
4. Review score, skill match, missing skills, strengths, weaknesses, and role guidance.
5. Confirm any missing skills only when the candidate can defend them in an interview.
6. Optimize the resume.
7. Export DOCX, PDF, or Jake's Resume LaTeX.

## QA Commands

Backend:

```powershell
python -m pytest backend/tests
```

Frontend:

```powershell
cd frontend
npm run lint
npm run build
```

## Notes

- Keep optimization truthful and evidence-based.
- Do not add paid services or external AI API dependencies.
- Uploaded files, generated resumes, SQLite databases, logs, vector stores, and build output should stay out of git.
- If embedding model files are not available locally, set `MODEL_LOCAL_FILES_ONLY=0` only when you intentionally allow model download.
