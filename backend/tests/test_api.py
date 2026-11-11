import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import fitz
from fastapi.testclient import TestClient
from fastapi.staticfiles import StaticFiles

from app.main import app
from app.core.retention import cleanup_expired_files
from app.services.llm.resume_optimizer import optimize_resume
from app.services.parser.resume_parser import extract_resume_data
from app.services.rebuilder.latex_resume import build_jakes_resume


def make_resume_pdf() -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text(
        (72, 72),
        (
            "Jordan Patel\n"
            "jordan@example.com | +1 555 123 4567\n\n"
            "SUMMARY\n"
            "Backend engineer building reliable Python APIs and data services.\n\n"
            "SKILLS\n"
            "Python, FastAPI, PostgreSQL, Docker, AWS\n\n"
            "EXPERIENCE\n"
            "Backend Engineer\n"
            "Built FastAPI services that improved response time by 35%.\n\n"
            "EDUCATION\n"
            "Bachelor of Technology"
        ),
    )
    content = document.tobytes()
    document.close()
    return content


class ApiContractTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.upload_dir = Path(self.temp_dir.name)
        (self.upload_dir / "optimized").mkdir(parents=True, exist_ok=True)
        self.pdf = make_resume_pdf()
        self.static_mount = next(route for route in app.routes if getattr(route, "path", None) == "/files/optimized")
        self.original_static_app = self.static_mount.app
        self.static_mount.app = StaticFiles(directory=self.upload_dir / "optimized")
        self.client = TestClient(app)
        self.patchers = [
            patch("app.core.files.UPLOAD_DIR", self.upload_dir),
            patch("app.api.routes.upload.UPLOAD_DIR", self.upload_dir),
            patch("app.core.retention.UPLOAD_DIR", self.upload_dir),
            patch("app.services.rebuilder.resume_rebuilder.OUTPUT_DIR", self.upload_dir / "optimized"),
            patch("app.services.rebuilder.latex_resume.OUTPUT_DIR", self.upload_dir / "optimized"),
            patch("app.services.rebuilder.latex_compiler.OUTPUT_DIR", self.upload_dir / "optimized"),
        ]
        for patcher in self.patchers:
            patcher.start()

    def tearDown(self):
        for patcher in reversed(self.patchers):
            patcher.stop()
        self.static_mount.app = self.original_static_app
        self.temp_dir.cleanup()

    def upload(self, filename="resume.pdf"):
        return self.client.post(
            "/upload/resume",
            files={"file": (filename, self.pdf, "application/pdf")},
        )

    def test_swagger_and_openapi_are_available(self):
        self.assertEqual(self.client.get("/docs").status_code, 200)
        response = self.client.get("/openapi.json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("/upload/resume", response.json()["paths"])
        self.assertIn("/optimize/latex", response.json()["paths"])
        self.assertIn("/optimize/latex/compile", response.json()["paths"])
        self.assertIn("/auth/signup", response.json()["paths"])
        self.assertIn("/feedback", response.json()["paths"])

    def test_cors_allows_localhost_and_vercel_frontend(self):
        for origin in ("http://localhost:3000", "http://127.0.0.1:3000", "https://ats-resume-ai-alpha.vercel.app"):
            response = self.client.options(
                "/upload/resume",
                headers={
                    "Origin": origin,
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "content-type",
                },
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers["access-control-allow-origin"], origin)

    def test_upload_saves_valid_pdf_with_collision_safe_name(self):
        first = self.upload()
        second = self.upload()

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertNotEqual(first.json()["filename"], second.json()["filename"])
        self.assertTrue((self.upload_dir / first.json()["filename"]).is_file())
        self.assertEqual(first.json()["size_bytes"], len(self.pdf))
        self.assertIn("expires_at", first.json())

    def test_upload_rejects_invalid_extension_and_spoofed_pdf(self):
        wrong_extension = self.client.post(
            "/upload/resume",
            files={"file": ("resume.docx", b"not a pdf", "application/octet-stream")},
        )
        spoofed_pdf = self.client.post(
            "/upload/resume",
            files={"file": ("resume.pdf", b"not a pdf", "application/pdf")},
        )

        self.assertEqual(wrong_extension.status_code, 415)
        self.assertEqual(spoofed_pdf.status_code, 415)

    def test_optional_auth_signup_login_me_and_logout(self):
        db_path = self.upload_dir / "auth-test.db"
        with patch("app.services.auth.store.DATABASE_PATH", db_path):
            created = self.client.post(
                "/auth/signup",
                json={"name": "Jordan Patel", "email": "Jordan@Example.com", "password": "strong-pass-123"},
            )
            duplicate = self.client.post(
                "/auth/signup",
                json={"name": "Jordan Patel", "email": "jordan@example.com", "password": "strong-pass-123"},
            )
            logged_in = self.client.post(
                "/auth/login",
                json={"email": "jordan@example.com", "password": "strong-pass-123"},
            )

            token = created.json()["token"]
            profile = self.client.get("/auth/me", headers={"X-Session-Token": token})
            logged_out = self.client.post("/auth/logout", headers={"X-Session-Token": token})
            after_logout = self.client.get("/auth/me", headers={"X-Session-Token": token})

        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.json()["user"]["email"], "jordan@example.com")
        self.assertTrue(db_path.is_file())
        self.assertEqual(duplicate.status_code, 400)
        self.assertEqual(logged_in.status_code, 200)
        self.assertEqual(profile.status_code, 200)
        self.assertEqual(profile.json()["name"], "Jordan Patel")
        self.assertEqual(logged_out.status_code, 204)
        self.assertEqual(after_logout.status_code, 401)

    def test_feedback_is_stored_for_guest_and_signed_in_user(self):
        db_path = self.upload_dir / "feedback-test.db"
        with patch("app.services.auth.store.DATABASE_PATH", db_path):
            guest = self.client.post(
                "/feedback",
                json={"visitor_id": "guest-visitor-123", "rating": 5, "message": "Useful flow", "page": "/results"},
            )
            created = self.client.post(
                "/auth/signup",
                json={"name": "Feedback User", "email": "feedback@example.com", "password": "strong-pass-123"},
            )
            signed_in = self.client.post(
                "/feedback",
                headers={"X-Session-Token": created.json()["token"]},
                json={"visitor_id": "known-visitor-123", "rating": 4, "message": "Mobile menu worked", "page": "/results"},
            )
            invalid = self.client.post(
                "/feedback",
                json={"visitor_id": "guest-visitor-123", "rating": 9, "message": "bad", "page": "/results"},
            )

        self.assertEqual(guest.status_code, 200)
        self.assertEqual(guest.json()["status"], "saved")
        self.assertEqual(signed_in.status_code, 200)
        self.assertEqual(invalid.status_code, 422)

    def test_upload_enforces_size_limit(self):
        with patch("app.api.routes.upload.MAX_UPLOAD_SIZE_BYTES", 32):
            response = self.upload()
        self.assertEqual(response.status_code, 413)

    def test_analyze_resume_returns_structured_data_and_ats_score(self):
        uploaded = self.upload().json()
        response = self.client.post(
            "/analyze/resume",
            json={
                "filename": uploaded["filename"],
                "job_description": "Backend Engineer with Python, FastAPI, Docker, AWS, and PostgreSQL.",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["resume_data"]["email"], "jordan@example.com")
        self.assertIn("ats", payload)
        self.assertGreaterEqual(payload["ats"]["score"], 0)

    def test_analyze_rejects_missing_and_unsafe_filenames(self):
        missing = self.client.post(
            "/analyze/resume",
            json={"filename": "missing.pdf", "job_description": "Python engineer"},
        )
        unsafe = self.client.post(
            "/analyze/resume",
            json={"filename": "../resume.pdf", "job_description": "Python engineer"},
        )

        self.assertEqual(missing.status_code, 404)
        self.assertEqual(unsafe.status_code, 422)

    def test_optimize_and_rebuild_complete_without_paid_api(self):
        uploaded = self.upload().json()
        request = {
            "filename": uploaded["filename"],
            "job_description": "Backend Engineer with Python, FastAPI, Kubernetes, Docker, and AWS.",
        }
        local_model_result = {"success": False, "provider": "local-model", "text": "model unavailable in test"}

        with (
            patch("app.api.routes.optimize.search_rag", return_value=["Use measurable backend outcomes."]),
            patch("app.services.llm.resume_optimizer.generate_resume_optimization", return_value=local_model_result) as local_model,
        ):
            optimized = self.client.post("/optimize/resume", json=request)
            rebuilt = self.client.post("/optimize/rebuild", json={**request, "output_format": "docx"})
            rebuilt_pdf = self.client.post("/optimize/rebuild", json={**request, "output_format": "pdf"})
            latex = self.client.post("/optimize/latex", json={**request, "template": "jakes"})

        self.assertEqual(optimized.status_code, 200)
        self.assertIn("optimization", optimized.json())
        self.assertEqual(rebuilt.status_code, 200)
        self.assertTrue((self.upload_dir / "optimized" / rebuilt.json()["filename"]).is_file())
        self.assertEqual(rebuilt_pdf.status_code, 200)
        rebuilt_pdf_path = self.upload_dir / "optimized" / rebuilt_pdf.json()["filename"]
        with fitz.open(rebuilt_pdf_path) as document:
            rebuilt_text = "\n".join(page.get_text() for page in document)
        self.assertNotIn("Preserved Original Resume Content", rebuilt_text)
        self.assertNotIn("Original Summary", rebuilt_text)
        self.assertEqual(latex.status_code, 200)
        self.assertIn("\\documentclass", latex.json()["latex_source"])
        self.assertIn("\\resumeSubheading", latex.json()["latex_source"])
        self.assertNotIn("Preserved Original Resume Content", latex.json()["latex_source"])
        self.assertTrue((self.upload_dir / "optimized" / latex.json()["filename"]).is_file())
        local_model.assert_called_once()

    def test_latex_compile_contract_and_fallback_renderer(self):
        uploaded = self.upload().json()
        request = {
            "filename": uploaded["filename"],
            "job_description": "Backend Engineer with Python, FastAPI, Docker, and AWS.",
            "template": "jakes",
        }
        compiled_result = {
            "filename": "resume_latex.pdf",
            "path": "optimized/resume_latex.pdf",
            "download_url": "/files/optimized/resume_latex.pdf",
            "format": "pdf",
            "compiler": "pdfLaTeX",
            "log_excerpt": "compiled",
        }
        (self.upload_dir / "optimized").mkdir(exist_ok=True)
        (self.upload_dir / "optimized" / "resume_latex.pdf").write_bytes(self.pdf)
        with (
            patch("app.api.routes.optimize.search_rag", return_value=[]),
            patch("app.api.routes.optimize.compile_latex_source", return_value=compiled_result),
        ):
            compiled = self.client.post("/optimize/latex/compile", json=request)
        self.assertEqual(compiled.status_code, 200)
        self.assertEqual(compiled.json()["compiler"], "pdfLaTeX")

        fallback_result = {
            "filename": "resume_latex_preview.pdf",
            "path": "optimized/resume_latex_preview.pdf",
            "download_url": "/files/optimized/resume_latex_preview.pdf",
            "format": "pdf",
            "compiler": "Built-in PDF renderer",
            "native_compiler": False,
            "fallback": True,
            "log_excerpt": "compiler missing",
        }
        with (
            patch("app.api.routes.optimize.search_rag", return_value=[]),
            patch(
                "app.api.routes.optimize.compile_latex_source",
                side_effect=__import__(
                    "app.services.rebuilder.latex_compiler",
                    fromlist=["LatexCompilerUnavailable"],
                ).LatexCompilerUnavailable("compiler missing"),
            ),
        ):
            fallback = self.client.post("/optimize/latex/compile", json=request)
        self.assertEqual(fallback.status_code, 200)
        self.assertTrue(fallback.json()["fallback"])
        self.assertEqual(fallback.json()["compiler"], "Original PDF layout")
        self.assertTrue(fallback.json()["layout_preserved"])
        self.assertEqual(fallback.json()["page_count"], 1)
        self.assertEqual(fallback.json()["ats"]["score"], fallback.json()["baseline_ats"]["score"])

    def test_automatic_ai_optimization_is_explicit_and_handles_provider_failure(self):
        uploaded = self.upload().json()
        request = {"filename": uploaded["filename"], "job_description": "Python FastAPI engineer", "use_ai": True}
        original = "Built FastAPI services that improved response time by 35%."
        refined = {"summary": None, "bullets": [{"original": original, "improved": original, "reason": "Evidence retained"}], "provider": "test-nvidia"}
        with patch("app.api.routes.optimize.search_rag", return_value=[]), patch("app.api.routes.optimize.refine_selected_changes", return_value=refined) as ai:
            response = self.client.post("/optimize/resume", json=request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["optimization"]["refinement_provider"], "test-nvidia")
        ai.assert_called_once()
        from app.services.llm.nvidia_mistral_service import NvidiaServiceError
        with patch("app.api.routes.optimize.search_rag", return_value=[]), patch("app.api.routes.optimize.refine_selected_changes", side_effect=NvidiaServiceError("test provider unavailable")):
            response = self.client.post("/optimize/resume", json=request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any("NVIDIA optimization unavailable" in warning for warning in response.json()["optimization"]["warnings"]))

    def test_selected_changes_are_the_only_changes_applied_to_latex(self):
        uploaded = self.upload().json()
        original = "Built FastAPI services that improved response time by 35%."
        response = self.client.post(
            "/optimize/latex",
            json={
                "filename": uploaded["filename"],
                "job_description": "Backend Engineer with Python and FastAPI.",
                "template": "jakes",
                "selected_summary": "Selected summary focused on reliable backend delivery.",
                "selected_bullets": [
                    {
                        "original": original,
                        "improved": "Optimized FastAPI services, improving response time by 35%.",
                        "reason": "Approved rewrite",
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["applied_changes"], 2)
        self.assertIn("Selected summary focused", payload["latex_source"])
        self.assertIn("Optimized FastAPI services", payload["latex_source"])

    def test_nvidia_refinement_route_returns_structured_selected_changes(self):
        refined = {
            "summary": "Concise backend summary.",
            "bullets": [
                {
                    "original": "Built APIs.",
                    "improved": "Built reliable APIs.",
                    "reason": "More specific",
                }
            ],
            "provider": "mistralai/mistral-large-4-1t-a52b",
            "cached": False,
            "latency_ms": 420,
        }
        with patch("app.api.routes.optimize.refine_selected_changes", return_value=refined) as refine:
            response = self.client.post(
                "/optimize/refine",
                json={
                    "job_description": "Backend Engineer",
                    "instruction": "Make this concise",
                    "summary": "Long backend summary.",
                    "bullets": [
                        {
                            "original": "Built APIs.",
                            "improved": "Developed APIs.",
                            "reason": "Initial suggestion",
                        }
                    ],
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["summary"], "Concise backend summary.")
        self.assertEqual(response.json()["bullets"][0]["original"], "Built APIs.")
        refine.assert_called_once()

    def test_retention_cleanup_removes_only_expired_resume_artifacts(self):
        old_pdf = self.upload_dir / "old.pdf"
        fresh_pdf = self.upload_dir / "fresh.pdf"
        ignored = self.upload_dir / "notes.txt"
        old_pdf.write_bytes(self.pdf)
        fresh_pdf.write_bytes(self.pdf)
        ignored.write_text("keep", encoding="utf-8")
        now = time.time()
        os.utime(old_pdf, (now - 25 * 3600, now - 25 * 3600))
        os.utime(ignored, (now - 25 * 3600, now - 25 * 3600))

        with (
            patch("app.core.retention.UPLOAD_DIR", self.upload_dir),
            patch("app.core.retention.UPLOAD_RETENTION_HOURS", 24),
        ):
            result = cleanup_expired_files(now=now)

        self.assertEqual(result["removed"], 1)
        self.assertFalse(old_pdf.exists())
        self.assertTrue(fresh_pdf.exists())
        self.assertTrue(ignored.exists())

    def test_refinement_rejects_empty_selection_before_calling_provider(self):
        with patch("app.api.routes.optimize.refine_selected_changes") as refine:
            response = self.client.post(
                "/optimize/refine",
                json={"job_description": "Backend Engineer", "instruction": "Make concise"},
            )
        self.assertEqual(response.status_code, 422)
        refine.assert_not_called()

    def test_rag_routes_return_expected_contracts(self):
        rag_result = [{"content": "Local role guidance", "source": "test_rules.txt", "retrieval": "keyword"}]
        with (
            patch("app.api.routes.rag.create_vector_db") as build,
            patch("app.api.routes.rag.search_rag_detailed", return_value=rag_result) as search,
        ):
            built = self.client.post("/rag/build")
            searched = self.client.post("/rag/search", json={"query": "backend engineer", "k": 2})

        self.assertEqual(built.status_code, 200)
        self.assertEqual(searched.status_code, 200)
        self.assertEqual(searched.json()["results"], ["Local role guidance"])
        self.assertEqual(searched.json()["sources"][0]["source"], "test_rules.txt")
        build.assert_called_once()
        search.assert_called_once_with("backend engineer", 2)

    def test_rag_build_falls_back_to_keyword_mode_when_embeddings_are_unavailable(self):
        with (
            patch("app.api.routes.rag.create_vector_db", side_effect=RuntimeError("model unavailable")),
            patch("app.api.routes.rag.guidance_corpus_available", return_value=True),
        ):
            response = self.client.post("/rag/build")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["mode"], "keyword")
        self.assertIn("keyword", response.json()["message"].lower())

    def test_schema_validation_rejects_bad_requests(self):
        invalid_optimize = self.client.post(
            "/optimize/resume",
            json={"filename": "resume.pdf", "job_description": " "},
        )
        invalid_rebuild = self.client.post(
            "/optimize/rebuild",
            json={"filename": "resume.pdf", "job_description": "Python", "output_format": "txt"},
        )
        invalid_rag = self.client.post("/rag/search", json={"query": "Python", "k": 50})
        invalid_latex = self.client.post(
            "/optimize/latex",
            json={"filename": "resume.pdf", "job_description": "Python", "template": "modern"},
        )

        self.assertEqual(invalid_optimize.status_code, 422)
        self.assertEqual(invalid_rebuild.status_code, 422)
        self.assertEqual(invalid_rag.status_code, 422)
        self.assertEqual(invalid_latex.status_code, 422)

    def test_parser_preserves_dated_resume_entries_and_skill_groups(self):
        text = """
        Alex Morgan
        alex@example.com
        Skills
        Languages: Python, SQL
        Support: Active Directory, Microsoft 365
        Experience
        Example Company
        Jan 2024 - Present
        IT Support Engineer
        • Resolved user incidents across Windows and Microsoft 365.
        • Managed Active Directory onboarding and access requests.
        Projects
        Service Desk Dashboard
        Mar 2024
        Power BI, Excel
        • Built an SLA dashboard for support leadership.
        Education
        Example University
        Aug 2019 - May 2023
        Bachelor of Technology
        CGPA: 8.1
        """
        parsed = extract_resume_data(text)

        self.assertEqual(parsed["experience"][0]["company"], "Example Company")
        self.assertEqual(parsed["experience"][0]["title"], "IT Support Engineer")
        self.assertEqual(parsed["projects"][0]["name"], "Service Desk Dashboard")
        self.assertEqual(parsed["projects"][0]["technologies"], "Power BI, Excel")
        self.assertEqual(parsed["education_entries"][0]["institution"], "Example University")
        self.assertEqual(parsed["skill_groups"]["Support"], ["Active Directory", "Microsoft 365"])

    def test_parser_and_latex_preserve_dash_bullets_and_undated_projects(self):
        text = """
        Shashank Singh
        singhshasank50@gmail.com
        Skills
        Programming: Python, Java, SQL
        Experience
        Tata Consultancy Services Ltd.
        Oct 2024 – Present
        Product Engineer
        Gurugram, Haryana
        – Developed AI-driven applications using Self-Attention CASUALLM models and FAISS-based semantic retrieval systems.
        – Integrated backend AI services with REST APIs and automation pipelines for scalable enterprise solutions.
        Soven Developer
        Jun 2024 – Sept 2024
        Frontend Developer Intern (Remote)
        – Built responsive UI components and integrated them with backend APIs for data-driven web applications.
        Projects
        AI-Powered SQL Copilot
        Python, FastAPI, RAG, FAISS, LLMs
        – Built a Text-to-SQL AI Copilot using retrieval, hybrid search, and schema-aware SQL generation.
        – Implemented embedding-based semantic retrieval using FAISS and cosine similarity.
        AI Conversational Platform
        Rasa, FastAPI, Flask, FAISS, LangChain
        – Built an enterprise conversational platform using Rasa and retrieval workflows.
        – Developed custom Python SDKs from Java SDK components for backend interoperability.
        Education
        Siksha O Anusandhan University
        Aug 2020 – Jul 2024
        B.Tech in Computer Science
        """
        parsed = extract_resume_data(text)
        latex = build_jakes_resume(parsed, {"improved_bullets": []})

        self.assertEqual(len(parsed["experience"]), 2)
        self.assertEqual(len(parsed["experience"][0]["bullets"]), 2)
        self.assertEqual(len(parsed["projects"]), 2)
        self.assertEqual(parsed["projects"][0]["technologies"], "Python, FastAPI, RAG, FAISS, LLMs")
        self.assertEqual(parsed["projects"][1]["name"], "AI Conversational Platform")
        self.assertIn("Developed AI-driven applications", latex)
        self.assertIn(r"\usepackage{fontawesome5}", latex)
        self.assertIn(r"\faEnvelope", latex)
        self.assertIn(r"\textbf{AI-Powered SQL Copilot}", latex)
        self.assertIn(r"\textbf{AI Conversational Platform}", latex)

    def test_parser_handles_inline_dates_heading_variants_and_contact_links(self):
        text = """
        TAYLOR KIM
        taylor.kim@example.com | +1 (415) 555-0199 | San Francisco, USA
        linkedin.com/in/taylorkim | github.com/taylorkim
        PROFESSIONAL PROFILE
        Platform engineer focused on reliable cloud services and developer productivity.
        CORE COMPETENCIES: Python | AWS | Kubernetes | PostgreSQL
        EMPLOYMENT HISTORY
        Senior Software Engineer | Northstar Labs | Jan 2022 - Present
        • Built an internal deployment platform used by 40 engineering teams.
        • Reduced production recovery time by 35% through automated runbooks.
        ACADEMIC QUALIFICATIONS
        State University | Bachelor of Science in Computer Science | 2017 - 2021
        """

        parsed = extract_resume_data(text)

        self.assertEqual(parsed["name"], "Taylor Kim")
        self.assertEqual(parsed["phone"], "+1 (415) 555-0199")
        self.assertEqual(parsed["location"], "San Francisco, USA")
        self.assertEqual(parsed["experience"][0]["company"], "Northstar Labs")
        self.assertEqual(parsed["experience"][0]["title"], "Senior Software Engineer")
        self.assertEqual(parsed["education_entries"][0]["institution"], "State University")
        self.assertEqual(parsed["education_entries"][0]["degree"], "Bachelor of Science in Computer Science")
        self.assertIn("linkedin", parsed["links"])
        self.assertIn("github", parsed["links"])
        self.assertGreaterEqual(parsed["extraction_quality"]["score"], 80)
        self.assertIn("experience", parsed["extraction_quality"]["detected_sections"])

    def test_optimizer_promotes_supported_keywords_and_requires_confirmation_for_missing_skills(self):
        resume_text = """
        Casey Shah
        casey@example.com
        Skills
        Automation Testing: Cypress, API Testing
        Experience
        QA Engineer
        - Built Playwright test coverage for critical browser workflows.
        Education
        Bachelor of Technology
        """
        structured = extract_resume_data(resume_text)
        unconfirmed = optimize_resume(
            resume_text,
            "QA Engineer with Cypress, Playwright, and Selenium.",
            "",
            include_local_model=False,
            structured_resume=structured,
        )
        self.assertIn("Playwright", unconfirmed["structured_resume"]["skill_groups"]["Automation Testing"])
        self.assertNotIn(
            "Selenium",
            unconfirmed["structured_resume"]["skill_groups"].get("Automation Testing", []),
        )
        self.assertIn(
            "recommendation_only",
            [
                item["status"]
                for item in unconfirmed["optimization"]["keyword_decisions"]
                if item["keyword"] == "Selenium"
            ],
        )

        confirmed = optimize_resume(
            resume_text,
            "QA Engineer with Cypress, Playwright, and Selenium.",
            "",
            include_local_model=False,
            structured_resume=structured,
            confirmed_keywords=["selenium"],
        )
        self.assertIn(
            "Selenium",
            confirmed["structured_resume"]["skill_groups"]["Automation Testing"],
        )

    def test_optimized_file_download(self):
        path = self.upload_dir / "optimized" / "api_contract_test.pdf"
        path.write_bytes(self.pdf)
        response = self.client.get(f"/files/optimized/{path.name}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, self.pdf)


if __name__ == "__main__":
    unittest.main()
