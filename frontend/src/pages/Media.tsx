import { useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { API_BASE } from "../lib/api";

const BAND_STYLES = {
  unlikely: { card: "border-sky-200 bg-sky-50", label: "text-sky-900 bg-sky-100" },
  unclear: { card: "border-amber-300 bg-amber-50", label: "text-amber-900 bg-amber-100" },
  possible_synthetic: { card: "border-red-300 bg-red-50", label: "text-red-900 bg-red-100" },
  could_not_check: { card: "border-slate-200 bg-slate-50", label: "text-slate-700 bg-slate-100" },
};

const ACCEPT = "image/jpeg,image/png,image/webp,image/gif,audio/wav,audio/mpeg,audio/mp4,audio/ogg";

interface MediaResult {
  band: string;
  score?: number;
  limits_note: string;
  reason?: string;
  filename?: string;
  mime_type?: string;
}

export default function Media() {
  const { t } = useTranslation();
  const inputRef = useRef<HTMLInputElement>(null);
  const [result, setResult] = useState<MediaResult | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [fileName, setFileName] = useState("");

  const submit = async (file: File) => {
    setLoading(true);
    setError("");
    setResult(null);
    const form = new FormData();
    form.append("file", file);
    try {
      const res = await fetch(`${API_BASE}/api/media-check`, { method: "POST", body: form });
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const data: any = await res.json().catch(() => null);
      if (!res.ok) {
        setError(data?.message || t("error_generic"));
      } else {
        setResult(data as MediaResult);
      }
    } catch {
      setError(t("error_network"));
    } finally {
      setLoading(false);
    }
  };

  const onChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setFileName(file.name);
    submit(file);
  };

  const band = result?.band ?? "";
  const style = BAND_STYLES[band as keyof typeof BAND_STYLES] ?? BAND_STYLES.could_not_check;

  return (
    <div className="space-y-6">
      <section className="bg-white border border-slate-200 rounded-xl p-6 space-y-4 shadow-xs">
        <h2 className="text-lg font-semibold text-slate-900">{t("media_title")}</h2>
        <p className="text-base text-slate-700 leading-relaxed">{t("media_desc")}</p>

        <input
          ref={inputRef}
          type="file"
          accept={ACCEPT}
          onChange={onChange}
          className="sr-only"
          aria-label={t("media_pick_file")}
        />
        <button
          onClick={() => inputRef.current?.click()}
          disabled={loading}
          className="min-h-12 w-full px-6 py-2 rounded-lg bg-[#0f4c81] text-white text-base font-semibold hover:bg-[#0c3c66] focus:outline-none focus:ring-2 focus:ring-[#0f4c81] disabled:bg-slate-300 disabled:text-slate-600"
        >
          {loading ? t("media_checking") : t("media_pick_file")}
        </button>
        {fileName && <p className="text-sm text-slate-600">{fileName}</p>}

        {error && (
          <p role="alert" className="text-base text-red-800 bg-red-50 border border-red-200 rounded-lg p-3">
            {error}
          </p>
        )}

        {result && (
          <div className={`border-2 ${style.card} rounded-xl p-5 space-y-3`} aria-live="polite">
            <span className={`inline-block px-3 py-1 rounded-full text-base font-semibold ${style.label}`}>
              {t(`band_${band}`)}
            </span>
            {typeof result.score === "number" && (
              <p className="text-sm text-slate-600">{t("media_score_label")}: {Math.round(result.score * 100)}%</p>
            )}
            <p className="text-sm text-slate-600 leading-relaxed">{result.limits_note}</p>
            {result.reason && (
              <p className="text-sm text-slate-500">{t("media_reason")}: {result.reason}</p>
            )}          </div>
        )}

        <p className="text-xs text-slate-500 leading-relaxed">{t("media_disclaimer")}</p>
      </section>
    </div>
  );
}
