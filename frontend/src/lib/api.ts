export type Lang = "mr" | "hi" | "en";
export type Risk = "low" | "medium" | "high";

export interface TriageResult {
  risk: Risk;
  scam_type: string;
  reasons: string[];
  next_steps: string[];
  confidence: number;
  lang: Lang;
  mode: "full" | "quick";
  show_helpline: boolean;
}

export const MAX_TEXT_LENGTH = 2000;
const FETCH_TIMEOUT_MS = 20000;

const rawBase = (import.meta.env.VITE_API_BASE_URL || "").trim().replace(/\/$/, "");
export const API_BASE =
  rawBase && rawBase !== "https://sajag-api.onrender.com"
    ? rawBase
    : "https://sajag-api-xqj5.onrender.com";

export class ApiError extends Error {
  code: string;

  constructor(code: string, message: string) {
    super(message);
    this.code = code;
  }
}

export async function triage(text: string, lang: Lang): Promise<TriageResult> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
  let res: Response;
  try {
    res = await fetch(`${API_BASE}/api/triage`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Lang": lang },
      body: JSON.stringify({ text, lang }),
      signal: controller.signal,
    });
  } catch {
    throw new ApiError("network", "");
  } finally {
    clearTimeout(timer);
  }
  const data = await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(data?.error_code ?? "internal", data?.message ?? "");
  return data as TriageResult;
}
