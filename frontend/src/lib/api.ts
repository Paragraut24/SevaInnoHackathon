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
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  code: string;

  constructor(code: string, message: string) {
    super(message);
    this.code = code;
  }
}

export async function triage(text: string, lang: Lang): Promise<TriageResult> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}/api/triage`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Lang": lang },
      body: JSON.stringify({ text, lang }),
    });
  } catch {
    throw new ApiError("network", "");
  }
  const data = await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(data?.error_code ?? "internal", data?.message ?? "");
  return data as TriageResult;
}
