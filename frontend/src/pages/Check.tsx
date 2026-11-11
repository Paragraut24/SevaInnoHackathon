import { useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import ResultCard from "../components/ResultCard";
import { ApiError, MAX_TEXT_LENGTH, triage, type Lang, type TriageResult } from "../lib/api";

export default function Check() {
  const { t, i18n } = useTranslation();
  const [text, setText] = useState("");
  const [result, setResult] = useState<TriageResult | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      setResult(await triage(text, i18n.language as Lang));
    } catch (err) {
      setResult(null);
      const known = err instanceof ApiError ? err : null;
      setError(known?.message || t(known?.code === "network" ? "error_network" : "error_generic"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <form
        onSubmit={submit}
        className="bg-white border border-slate-200 rounded-xl p-6 space-y-3 shadow-xs"
      >
        <h2 className="text-lg font-semibold text-slate-900">{t("check_title")}</h2>
        <label htmlFor="message" className="block text-base text-slate-700 leading-relaxed">
          {t("check_hint")}
        </label>
        <textarea
          id="message"
          value={text}
          onChange={(e) => setText(e.target.value)}
          maxLength={MAX_TEXT_LENGTH}
          rows={6}
          placeholder={t("check_placeholder")}
          className="w-full rounded-lg border border-slate-300 p-3 text-base text-slate-900 focus:outline-none focus:ring-2 focus:ring-[#0f4c81]"
        />
        <div className="flex items-center justify-between gap-4">
          <span className="text-sm text-slate-600">
            {t("char_count", { used: text.length, max: MAX_TEXT_LENGTH })}
          </span>
          <button
            type="submit"
            disabled={loading || !text.trim()}
            className="min-h-12 px-6 py-2 rounded-lg bg-[#0f4c81] text-white text-base font-semibold hover:bg-[#0c3c66] focus:outline-none focus:ring-2 focus:ring-[#0f4c81] disabled:bg-slate-300 disabled:text-slate-600 disabled:cursor-not-allowed"
          >
            {loading ? t("check_loading") : t("check_submit")}
          </button>
        </div>
        {error && (
          <p role="alert" className="text-base text-red-800 bg-red-50 border border-red-200 rounded-lg p-3">
            {error}
          </p>
        )}
      </form>
      {result && <ResultCard result={result} />}
    </>
  );
}
