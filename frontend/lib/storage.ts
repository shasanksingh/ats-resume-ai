import type { WorkflowState } from "@/lib/api";

export function readStoredJson<T>(key: string): T | null {
  try {
    const value = window.localStorage.getItem(key);
    return value ? (JSON.parse(value) as T) : null;
  } catch {
    window.localStorage.removeItem(key);
    return null;
  }
}

export function readActiveWorkflow(): WorkflowState | null {
  const workflow = readStoredJson<WorkflowState>("ats-workflow");
  if (!workflow?.expiresAt) return workflow;
  const expiresAt = Date.parse(workflow.expiresAt);
  if (!Number.isFinite(expiresAt) || expiresAt > Date.now()) return workflow;
  clearWorkflowData();
  return null;
}

export function clearWorkflowData() {
  window.localStorage.removeItem("ats-workflow");
  window.localStorage.removeItem("ats-analysis");
  window.localStorage.removeItem("ats-optimized");
}
