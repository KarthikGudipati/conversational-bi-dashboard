/**
 * API service — handles all communication with the FastAPI backend.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ── Types ───────────────────────────────────────────────────────────

export interface ChartConfig {
  type: "bar" | "line" | "pie" | "metric" | "table";
  xAxis: string | null;
  yAxis: string[];
  title: string;
}

export interface QueryResult {
  prompt: string;
  sql: string;
  data: Record<string, unknown>[];
  chart_config: ChartConfig;
  summary: string;
  session_id: string;
}

export interface UploadResult {
  message: string;
  table_name: string;
  rows_loaded: number;
  columns_detected: string[];
}

// ── API calls ───────────────────────────────────────────────────────

export async function submitQuery(
  prompt: string,
  sessionId?: string | null,
): Promise<QueryResult> {
  const body: Record<string, string> = { prompt };
  if (sessionId) {
    body.session_id = sessionId;
  }

  const res = await fetch(`${API_BASE}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Query failed");
  }
  return res.json();
}

export async function uploadCsv(file: File): Promise<UploadResult> {
  const form = new FormData();
  form.append("file", file);

  const res = await fetch(`${API_BASE}/upload_csv`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Upload failed");
  }
  return res.json();
}

export async function clearSession(sessionId: string): Promise<void> {
  await fetch(`${API_BASE}/session/clear`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId }),
  });
}
