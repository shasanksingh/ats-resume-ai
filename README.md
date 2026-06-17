# ATS Resume Studio

ATS Resume Studio is a local-first resume analysis and optimization platform for ATS-focused job applications. It uploads a PDF resume, compares it with a target job description, explains the match score, recommends truthful improvements, and exports optimized DOCX, PDF, and Jake's Resume LaTeX output.

The project does not use OpenAI APIs, Gemini APIs, or paid services.

## Features

- PDF resume upload with validation, drag/drop support, and progress feedback.
- Resume parsing for contact details, skills, experience, projects, education, links, and sections.
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
- LaTeX preview: MiKTeX, TeX Live, or Tectonic when installed; built-in PDF fallback otherwise.

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
```

## Frontend Setup

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

The results page generates Jake's Resume LaTeX source and can preview it beside the source editor.

For native compilation, install one of:

- MiKTeX
- TeX Live
- Tectonic

If no local compiler is available, the app uses a built-in PDF fallback so users can still preview and download a PDF.

## Workflow

1. Upload a text-based PDF resume.
2. Paste the complete target job description.
3. Run ATS analysis.
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
