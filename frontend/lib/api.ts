const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "/api/backend";
export const SESSION_STORAGE_KEY = "ats-session";
export const AUTH_SKIP_STORAGE_KEY = "ats-auth-skip";
export const VISITOR_ID_STORAGE_KEY = "ats-visitor-id";
export const FEEDBACK_SUBMITTED_STORAGE_KEY = "ats-feedback-submitted";

export type WorkflowState = {
  filename: string;
  jobDescription: string;
};

export type AtsResult = {
  score: number;
  ats_score: number;
  strengths: string[];
  weaknesses: string[];
  missing_keywords: string[];
  missing_terms: string[];
  matched_keywords: string[];
  resume_skills: string[];
  jd_skills: string[];
  section_scores: Record<string, number>;
  score_explanations: {
    category: string;
    label: string;
    score: number;
    weight: number;
    contribution: number;
    evidence: string;
  }[];
  recommendations: string[];
};

export type ExperienceItem = {
  title?: string;
  company?: string;
  dates?: string;
  bullets?: string[];
};

export type ProjectItem = {
  name?: string;
  date?: string;
  technologies?: string;
  description?: string;
  bullets?: string[];
};

export type EducationItem = {
  institution?: string;
  dates?: string;
  degree?: string;
  details?: string;
};

export type ResumeData = {
  name?: string;
  email?: string;
  phone?: string;
  summary?: string;
  skills?: string[];
  skill_groups?: Record<string, string[]>;
  experience?: ExperienceItem[];
  projects?: ProjectItem[];
  education?: string[];
  education_entries?: EducationItem[];
  certifications?: string[];
  links?: Record<string, string>;
  sections?: Record<string, string>;
  [key: string]: unknown;
};

export type AnalysisResponse = {
  filename: string;
  resume_data: ResumeData;
  raw_text_chars: number;
  ats?: AtsResult;
};

export type OptimizationResponse = {
  structured_resume: ResumeData;
  baseline_ats: AtsResult;
  ats: AtsResult;
  optimization: {
    improved_summary: string;
    improved_bullets: { original: string; improved: string; reason: string }[];
    keyword_suggestions: string[];
    keyword_decisions: {
      keyword: string;
      status: "added_from_evidence" | "added_after_confirmation" | "recommendation_only";
      reason: string;
      evidence: string;
    }[];
    rag_guidance: string[];
    local_model_hint: { success: boolean; text: string; error?: string };
    warnings: string[];
  };
};

export type UploadResponse = {
  filename: string;
  original_filename: string;
  status: string;
  size_bytes: number;
};

export type LatexResponse = {
  filename: string;
  path: string;
  download_url: string;
  format: "tex";
  template: "jakes";
  latex_source: string;
};

export type LatexCompilerStatus = {
  available: boolean;
  compiler: string | null;
  native_compiler?: boolean;
  message: string;
};

export type LatexCompileResponse = {
  filename: string;
  path: string;
  download_url: string;
  format: "pdf";
  compiler: string;
  native_compiler?: boolean;
  fallback?: boolean;
  log_excerpt: string;
};

export type RagSearchResponse = {
  results: string[];
  sources: { source: string; retrieval: string }[];
};

export type UserProfile = {
  id: number;
  name: string;
  email: string;
  created_at: string;
};

export type AuthResponse = {
  token: string;
  user: UserProfile;
};

export type FeedbackResponse = {
  id: number;
  status: string;
  created_at: string;
};

type ErrorPayload = {
  detail?: string | { msg?: string }[];
  message?: string;
};

export class ApiError extends Error {
  status: number;

  constructor(message: string, status = 0) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function errorMessage(payload: ErrorPayload | null, fallback: string) {
  if (typeof payload?.detail === "string") return payload.detail;
  if (Array.isArray(payload?.detail)) {
    return payload.detail.map((item) => item.msg).filter(Boolean).join(". ") || fallback;
  }
  return payload?.message || fallback;
}

async function responseError(response: Response) {
  const fallback = `Request failed (${response.status})`;
  try {
    const payload = (await response.json()) as ErrorPayload;
    return new ApiError(errorMessage(payload, fallback), response.status);
  } catch {
    return new ApiError(fallback, response.status);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    const token = getStoredSessionToken();
    response = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { "X-Session-Token": token } : {}),
        ...(init?.headers || {})
      }
    });
  } catch {
    throw new ApiError("Cannot reach the ATS backend. Confirm that the FastAPI server is running.");
  }
  if (!response.ok) {
    throw await responseError(response);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export function uploadResume(file: File, onProgress?: (percent: number) => void) {
  return new Promise<UploadResponse>((resolve, reject) => {
    const form = new FormData();
    form.append("file", file, file.name);

    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_BASE}/upload/resume`);
    xhr.responseType = "json";
    xhr.timeout = 120000;
    const token = getStoredSessionToken();
    if (token) xhr.setRequestHeader("X-Session-Token", token);

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        onProgress?.(Math.round((event.loaded / event.total) * 100));
      }
    };
    xhr.onerror = () => reject(new ApiError("Cannot reach the ATS backend. Confirm that FastAPI is running."));
    xhr.ontimeout = () => reject(new ApiError("The upload timed out. Try a smaller PDF."));
    xhr.onload = () => {
      const payload = (xhr.response || {}) as UploadResponse & ErrorPayload;
      if (xhr.status >= 200 && xhr.status < 300) {
        onProgress?.(100);
        resolve(payload);
        return;
      }
      reject(new ApiError(errorMessage(payload, `Upload failed (${xhr.status})`), xhr.status));
    };

    xhr.send(form);
  });
}

export function analyzeResume(filename: string, jobDescription: string) {
  return request<AnalysisResponse>("/analyze/resume", {
    method: "POST",
    body: JSON.stringify({ filename, job_description: jobDescription })
  });
}

export function optimizeResume(filename: string, jobDescription: string, confirmedKeywords: string[] = []) {
  return request<OptimizationResponse>("/optimize/resume", {
    method: "POST",
    body: JSON.stringify({ filename, job_description: jobDescription, confirmed_keywords: confirmedKeywords })
  });
}

export function rebuildResume(filename: string, jobDescription: string, outputFormat: "docx" | "pdf", confirmedKeywords: string[] = []) {
  return request<{ filename: string; path: string; download_url: string; format: string }>("/optimize/rebuild", {
    method: "POST",
    body: JSON.stringify({ filename, job_description: jobDescription, output_format: outputFormat, confirmed_keywords: confirmedKeywords })
  });
}

export function generateLatex(filename: string, jobDescription: string, confirmedKeywords: string[] = []) {
  return request<LatexResponse>("/optimize/latex", {
    method: "POST",
    body: JSON.stringify({ filename, job_description: jobDescription, template: "jakes", confirmed_keywords: confirmedKeywords })
  });
}

export function getLatexCompilerStatus() {
  return request<LatexCompilerStatus>("/optimize/latex/status");
}

export function compileLatex(filename: string, jobDescription: string, confirmedKeywords: string[] = []) {
  return request<LatexCompileResponse>("/optimize/latex/compile", {
    method: "POST",
    body: JSON.stringify({ filename, job_description: jobDescription, template: "jakes", confirmed_keywords: confirmedKeywords })
  });
}

export function searchRag(query: string, k = 6) {
  return request<RagSearchResponse>("/rag/search", {
    method: "POST",
    body: JSON.stringify({ query, k })
  });
}

export function signup(name: string, email: string, password: string) {
  return request<AuthResponse>("/auth/signup", {
    method: "POST",
    body: JSON.stringify({ name, email, password })
  });
}

export function login(email: string, password: string) {
  return request<AuthResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password })
  });
}

export function getMe() {
  return request<UserProfile>("/auth/me");
}

export function logout() {
  return request<void>("/auth/logout", { method: "POST" });
}

export function submitFeedback(rating: number, message: string, page: string) {
  return request<FeedbackResponse>("/feedback", {
    method: "POST",
    body: JSON.stringify({
      visitor_id: getVisitorId(),
      rating,
      message,
      page
    })
  });
}

export function apiUrl(path: string) {
  return path.startsWith("http") ? path : `${API_BASE}${path}`;
}

function getStoredSessionToken() {
  if (typeof window === "undefined") return "";
  try {
    const value = window.localStorage.getItem(SESSION_STORAGE_KEY);
    if (!value) return "";
    return (JSON.parse(value) as { token?: string }).token || "";
  } catch {
    window.localStorage.removeItem(SESSION_STORAGE_KEY);
    return "";
  }
}

function getVisitorId() {
  if (typeof window === "undefined") return "server-render";
  const existing = window.localStorage.getItem(VISITOR_ID_STORAGE_KEY);
  if (existing) return existing;
  const generated = typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : `visitor-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  window.localStorage.setItem(VISITOR_ID_STORAGE_KEY, generated);
  return generated;
}
