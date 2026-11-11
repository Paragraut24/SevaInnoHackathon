import { useTranslation } from "react-i18next";
import type { Risk, TriageResult } from "../lib/api";

const RISK_STYLES: Record<Risk, { card: string; badge: string; bar: string }> = {
  low: { card: "border-sky-200", badge: "bg-sky-100 text-sky-900", bar: "bg-sky-600" },
  medium: { card: "border-amber-300", badge: "bg-amber-100 text-amber-900", bar: "bg-amber-600" },
  high: { card: "border-red-300", badge: "bg-red-100 text-red-900", bar: "bg-red-700" },
};

export default function ResultCard({ result }: { result: TriageResult }) {
  const { t } = useTranslation();
  const style = RISK_STYLES[result.risk];
  const confidence = Math.round(result.confidence * 100);

  return (
    <section
      aria-live="polite"
      className={`bg-white border-2 ${style.card} rounded-xl p-6 space-y-4 shadow-xs`}
    >
      <div className="flex flex-wrap items-center gap-2">
        <span className={`px-3 py-1 rounded-full text-base font-semibold ${style.badge}`}>
          {t(`risk_${result.risk}`)}
        </span>
        {result.mode === "quick" && (
          <span className="px-3 py-1 rounded-full text-sm font-medium bg-slate-100 text-slate-700">
            {t("quick_label")}
          </span>
        )}
      </div>

      <p className="text-base text-slate-900">
        <span className="text-sm text-slate-600">{t("scam_type_label")}: </span>
        <span className="font-semibold">{result.scam_type}</span>
      </p>

      <div className="space-y-2">
        <h3 className="text-base font-semibold text-slate-900">{t("reasons_title")}</h3>
        <ul className="list-disc pl-5 space-y-1 text-base text-slate-700 leading-relaxed">
          {result.reasons.map((r) => (
            <li key={r}>{r}</li>
          ))}
        </ul>
      </div>

      <div className="space-y-2">
        <h3 className="text-base font-semibold text-slate-900">{t("steps_title")}</h3>
        <ol className="list-decimal pl-5 space-y-1 text-base text-slate-700 leading-relaxed">
          {result.next_steps.map((s) => (
            <li key={s}>{s}</li>
          ))}
        </ol>
      </div>

      <div className="space-y-1">
        <p className="text-sm text-slate-600">
          {t("confidence_label")}: {confidence}%
        </p>
        <div
          role="progressbar"
          aria-valuenow={confidence}
          aria-valuemin={0}
          aria-valuemax={100}
          className="h-2 w-full rounded-full bg-slate-100"
        >
          <div className={`h-2 rounded-full ${style.bar}`} style={{ width: `${confidence}%` }} />
        </div>
      </div>

      {result.show_helpline && (
        <a
          href="tel:1930"
          className="flex items-center justify-center min-h-12 px-4 py-3 rounded-lg bg-red-700 text-white text-base font-semibold hover:bg-red-800 focus:outline-none focus:ring-2 focus:ring-red-600"
        >
          {t("call_1930")}
        </a>
      )}
    </section>
  );
}
