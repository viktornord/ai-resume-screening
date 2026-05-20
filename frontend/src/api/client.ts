import type { HealthResponse, ScreenResponse } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "";

export async function checkHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error("Health check failed");
  return res.json();
}

export async function screenResumes(
  jobDescription: File,
  resumes: File[],
): Promise<ScreenResponse> {
  const form = new FormData();
  form.append("job_description", jobDescription);
  for (const file of resumes) {
    form.append("resumes", file);
  }

  const res = await fetch(`${API_BASE}/api/screen`, {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: res.statusText }));
    const msg =
      typeof detail.detail === "string"
        ? detail.detail
        : JSON.stringify(detail.detail ?? detail);
    throw new Error(msg || "Screening failed");
  }

  return res.json();
}
