const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

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
  recommendations: string[];
};

export type AnalysisResponse = {
  filename: string;
  resume_data: Record<string, any>;
  raw_text_chars: number;
  ats?: AtsResult;
};

export type OptimizationResponse = {
  structured_resume: Record<string, any>;
  ats: AtsResult;
  optimization: {
    improved_summary: string;
    improved_bullets: { original: string; improved: string; reason: string }[];
    keyword_suggestions: string[];
    rag_guidance: string[];
    local_model_hint: { success: boolean; text: string; error?: string };
    warnings: string[];
  };
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {})
    }
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function uploadResume(file: File) {
  const form = new FormData();
  form.append("file", file);
  const response = await fetch(`${API_BASE}/upload/resume`, {
    method: "POST",
    body: form
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json() as Promise<{ filename: string; status: string; size_bytes: number }>;
}

export function analyzeResume(filename: string, jobDescription: string) {
  return request<AnalysisResponse>("/analyze/resume", {
    method: "POST",
    body: JSON.stringify({ filename, job_description: jobDescription })
  });
}

export function optimizeResume(filename: string, jobDescription: string) {
  return request<OptimizationResponse>("/optimize/resume", {
    method: "POST",
    body: JSON.stringify({ filename, job_description: jobDescription })
  });
}

export function rebuildResume(filename: string, jobDescription: string, outputFormat: "docx" | "pdf") {
  return request<{ filename: string; path: string; download_url: string; format: string }>("/optimize/rebuild", {
    method: "POST",
    body: JSON.stringify({ filename, job_description: jobDescription, output_format: outputFormat })
  });
}

export function apiUrl(path: string) {
  return path.startsWith("http") ? path : `${API_BASE}${path}`;
}
