import { useTranslation } from "react-i18next";
import type { TokenWeight } from "../lib/api";

export default function TokenHighlights({ tokens }: { tokens: TokenWeight[] }) {
  const { t } = useTranslation();

  if (tokens.length === 0) return null;

  return (
    <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 space-y-2">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h4 className="text-sm font-semibold text-slate-900">{t("token_highlights_title")}</h4>
        <div className="flex flex-wrap items-center gap-3 text-xs text-slate-600">
          <span className="inline-flex items-center gap-1">
            <span className="inline-block w-2.5 h-2.5 rounded-full bg-red-600" aria-hidden="true" />
            {t("token_highlight_higher")}
          </span>
          <span className="inline-flex items-center gap-1">
            <span className="inline-block w-2.5 h-2.5 rounded-full bg-slate-500" aria-hidden="true" />
            {t("token_highlight_lower")}
          </span>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        {tokens.map((item) => {
          const higher = item.weight > 0;
          const pct = Math.round(Math.abs(item.weight) * 100);
          return (
            <span
              key={item.token}
              title={higher ? t("token_highlight_higher") : t("token_highlight_lower")}
              className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-medium border transition-colors ${
                higher
                  ? "bg-red-50 border-red-200 text-red-900 hover:bg-red-100"
                  : "bg-slate-100 border-slate-300 text-slate-800 hover:bg-slate-200"
              }`}
            >
              <span>{item.token}</span>
              <span className="text-xs font-mono opacity-80">
                {higher ? `+${pct}%` : `-${pct}%`}
              </span>
            </span>
          );
        })}
      </div>
    </div>
  );
}
