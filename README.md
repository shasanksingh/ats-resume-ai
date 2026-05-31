# ATS Resume AI

🧠 **ATS Resume AI** is a full-stack resume analysis and optimization app. It uploads a PDF resume, compares it with a target job description, scores ATS alignment, retrieves role-specific guidance from local RAG data, and can rebuild an optimized DOCX or PDF draft.

## ✨ Features

- 📄 PDF resume upload and parsing
- 🎯 ATS score with matched and missing JD keywords
- 🧩 Section health scoring for skills, summary, experience, education, action verbs, length, and quantified impact
- 🔎 Local RAG knowledge base with profile rules for AI Engineer, Backend Engineer, Software Engineer, Data Analyst, SQL Developer, Python Developer, and Digital Marketing
- 🛠️ Resume optimization suggestions with improved summary and bullet rewrites
- 📥 Rebuilt DOCX/PDF downloads through backend static file routes
- 🖥️ Next.js frontend with a guided upload, dashboard, and results workflow

## 🧱 Tech Stack

- ⚡ Frontend: Next.js, React, TypeScript, Tailwind CSS, lucide-react
- 🚀 Backend: FastAPI, Pydantic, python-docx, ReportLab
- 🔎 RAG: LangChain, ChromaDB, Hugging Face sentence-transformer embeddings
- 📄 Parsing: PDF text extraction service in `backend/app/services/parser`

## 📁 Project Structure

```text
ats-resume-ai/
  backend/
    app/
      api/routes/          FastAPI routes
      data/skills.py       ATS keyword taxonomy
      services/            Parser, scoring, RAG, optimizer, rebuilder
    rag-data/              Role rules and profile samples
    uploads/               Uploaded and generated resumes
  frontend/
    app/                   Next.js routes
    components/ui/         Shared UI primitives
    lib/api.ts             Backend API client
```

## ⚙️ Backend Setup

```powershell
cd backend
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend runs at:

```text
http://127.0.0.1:8000
```

Useful endpoints:

- `POST /upload/resume`
- `POST /analyze/resume`
- `POST /optimize/resume`
- `POST /optimize/rebuild`
- `POST /rag/build`
- `POST /rag/search`
- `GET /files/optimized/{filename}`

## 🖥️ Frontend Setup

```powershell
cd frontend
npm install
npm run dev
```

Frontend runs at:

```text
http://localhost:3000
```

Optional frontend environment variable:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

## 🧠 RAG Dataset

Role guidance lives in `backend/rag-data`.

Current corpus includes:

- 🤖 AI Engineer rules
- 🧰 Backend Engineer rules
- 💻 Software Engineer rules
- 📊 Data Analyst rules
- 🗄️ SQL Developer rules
- 🐍 Python Developer rules
- 📣 Digital Marketing rules
- 👤 Multi-profile sample summaries and bullets

The backend now checks whether RAG text files are newer than the Chroma vector store. If the corpus changes, the next RAG search rebuilds the vector DB automatically.

## 🚦 Workflow

1. 📤 Upload a PDF resume and paste a target job description.
2. 📈 Run analysis to score ATS match and inspect parsed resume data.
3. ✨ Run optimization to generate summary, bullet, keyword, and RAG-backed recommendations.
4. 📥 Rebuild and download a DOCX or PDF optimized draft.

## ✅ Notes

- Keep resume recommendations truthful. The optimizer should not invent employers, tools, degrees, certifications, dates, or metrics.
- The app is configured for local development with frontend CORS allowed from `localhost:3000` and `127.0.0.1:3000`.
- If embedding model files are not already available locally, set `MODEL_LOCAL_FILES_ONLY=0` and allow model download before building the vector DB.
