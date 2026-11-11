import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { API_BASE } from "../lib/api";

interface DashboardData {
  sample: boolean;
  summary: { total_reports: number; resolved: number; pending: number; top_category: string };
  by_category: { category: string; label: string; count: number }[];
  monthly_trend: { month: string; reports: number }[];
  by_district: { district: string; reports: number; top_category: string }[];
}

const BAR_COLORS = ["bg-[#0f4c81]", "bg-blue-500", "bg-sky-500", "bg-cyan-500", "bg-teal-500", "bg-indigo-500", "bg-violet-500"];

export default function Dashboard() {
  const { t } = useTranslation();
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${API_BASE}/api/dashboard`)
      .then((r) => r.json())
      .then(setData)
      .catch(() => setError(t("error_network")));
  }, [t]);

  if (error) return <p role="alert" className="text-red-800 bg-red-50 border border-red-200 rounded-xl p-4">{error}</p>;
  if (!data) return <p className="text-slate-600 text-center py-12">{t("loading")}</p>;

  const maxCat = Math.max(...data.by_category.map((c) => c.count), 1);
  const maxTrend = Math.max(...data.monthly_trend.map((m) => m.reports), 1);

  return (
    <div className="space-y-6">
      {data.sample && (
        <div className="bg-amber-50 border border-amber-300 rounded-xl p-3 text-sm font-medium text-amber-900">
          {t("dashboard_sample_banner")}
        </div>
      )}

      {/* Summary cards */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        {[
          { label: t("dashboard_total"), value: data.summary.total_reports },
          { label: t("dashboard_resolved"), value: data.summary.resolved },
          { label: t("dashboard_pending"), value: data.summary.pending },
        ].map(({ label, value }) => (
          <div key={label} className="bg-white border border-slate-200 rounded-xl p-4 text-center shadow-xs">
            <p className="text-2xl font-bold text-[#0f4c81]">{value.toLocaleString()}</p>
            <p className="text-xs text-slate-600 mt-1">{label}</p>
          </div>
        ))}
      </div>

      {/* By category */}
      <section className="bg-white border border-slate-200 rounded-xl p-6 space-y-4 shadow-xs">
        <h3 className="text-base font-semibold text-slate-900">{t("dashboard_by_category")}</h3>
        <div className="space-y-2">
          {data.by_category.map(({ label, count }, i) => (
            <div key={label} className="space-y-1">
              <div className="flex justify-between text-sm text-slate-700">
                <span>{label}</span>
                <span className="font-medium">{count}</span>
              </div>
              <div className="h-3 w-full rounded-full bg-slate-100">
                <div
                  className={`h-3 rounded-full ${BAR_COLORS[i % BAR_COLORS.length]}`}
                  style={{ width: `${(count / maxCat) * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Monthly trend */}
      <section className="bg-white border border-slate-200 rounded-xl p-6 space-y-4 shadow-xs">
        <h3 className="text-base font-semibold text-slate-900">{t("dashboard_monthly_trend")}</h3>
        <div className="flex items-end gap-2 h-32">
          {data.monthly_trend.map(({ month, reports }) => (
            <div key={month} className="flex-1 flex flex-col items-center gap-1">
              <div
                className="w-full rounded-t bg-[#0f4c81]"
                style={{ height: `${(reports / maxTrend) * 100}%` }}
                title={`${month}: ${reports}`}
              />
              <span className="text-xs text-slate-500">{month.slice(0, 3)}</span>
            </div>
          ))}
        </div>
      </section>

      {/* By district */}
      <section className="bg-white border border-slate-200 rounded-xl p-6 space-y-3 shadow-xs">
        <h3 className="text-base font-semibold text-slate-900">{t("dashboard_by_district")}</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left text-slate-700">
            <thead>
              <tr className="border-b border-slate-200 text-xs text-slate-500 uppercase">
                <th className="pb-2 pr-4">{t("dashboard_col_district")}</th>
                <th className="pb-2 pr-4">{t("dashboard_col_reports")}</th>
                <th className="pb-2">{t("dashboard_col_top")}</th>
              </tr>
            </thead>
            <tbody>
              {data.by_district.map(({ district, reports, top_category }) => (
                <tr key={district} className="border-b border-slate-100 last:border-0">
                  <td className="py-2 pr-4 font-medium">{district}</td>
                  <td className="py-2 pr-4">{reports}</td>
                  <td className="py-2 text-slate-500">{top_category.replace(/_/g, " ")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

