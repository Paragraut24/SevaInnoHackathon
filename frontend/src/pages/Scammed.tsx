import { useState } from "react";
import { useTranslation } from "react-i18next";
import { downloadIncidentPdf } from "../lib/pdf";

const STEPS = ["step_call_1930", "step_evidence", "step_portal", "step_form"] as const;

const EVIDENCE_ITEMS = [
  "evidence_screenshots",
  "evidence_transaction",
  "evidence_contact",
  "evidence_messages",
] as const;

type Step = (typeof STEPS)[number];

const PORTAL_URL = "https://cybercrime.gov.in";

export default function Scammed() {
  const { t } = useTranslation();
  const [current, setCurrent] = useState<Step>(STEPS[0]);
  const [evidence, setEvidence] = useState<string[]>([]);
  const [form, setForm] = useState({ date: "", amount: "", account: "", description: "", phone: "" });

  const stepIdx = STEPS.indexOf(current);

  const toggleEvidence = (item: string) =>
    setEvidence((prev) => prev.includes(item) ? prev.filter((e) => e !== item) : [...prev, item]);

  const download = () => {
    downloadIncidentPdf({ ...form, evidence: evidence.map((e) => t(e)) });
  };

  return (
    <div className="space-y-6">
      {/* Stepper header */}
      <div className="flex gap-1">
        {STEPS.map((s, i) => (
          <div
            key={s}
            className={`flex-1 h-2 rounded-full transition-colors ${
              i <= stepIdx ? "bg-[#0f4c81]" : "bg-slate-200"
            }`}
          />
        ))}
      </div>

      {/* Step: Call 1930 */}
      {current === "step_call_1930" && (
        <section className="bg-white border border-slate-200 rounded-xl p-6 space-y-4 shadow-xs">
          <h2 className="text-lg font-semibold text-red-900">{t("scammed_step1_title")}</h2>
          <p className="text-base text-slate-700 leading-relaxed">{t("scammed_step1_body")}</p>
          <a
            href="tel:1930"
            className="flex items-center justify-center min-h-14 rounded-lg bg-red-700 text-white text-xl font-bold hover:bg-red-800 focus:outline-none focus:ring-2 focus:ring-red-600"
          >
            1930
          </a>
          <button
            onClick={() => setCurrent("step_evidence")}
            className="w-full min-h-12 px-4 py-2 rounded-lg border border-slate-300 text-base text-slate-700 font-medium hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-[#0f4c81]"
          >
            {t("scammed_already_called")}
          </button>
        </section>
      )}

      {/* Step: Collect evidence */}
      {current === "step_evidence" && (
        <section className="bg-white border border-slate-200 rounded-xl p-6 space-y-4 shadow-xs">
          <h2 className="text-lg font-semibold text-slate-900">{t("scammed_step2_title")}</h2>
          <p className="text-base text-slate-700 leading-relaxed">{t("scammed_step2_body")}</p>
          <ul className="space-y-3">
            {EVIDENCE_ITEMS.map((item) => (
              <li key={item}>
                <label className="flex items-start gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    className="mt-1 w-5 h-5 accent-[#0f4c81] flex-shrink-0"
                    checked={evidence.includes(item)}
                    onChange={() => toggleEvidence(item)}
                  />
                  <span className="text-base text-slate-900">{t(item)}</span>
                </label>
              </li>
            ))}
          </ul>
          <div className="flex gap-3">
            <button onClick={() => setCurrent("step_call_1930")} className="flex-1 min-h-12 rounded-lg border border-slate-300 text-slate-700 text-sm font-medium hover:bg-slate-50">{t("back")}</button>
            <button onClick={() => setCurrent("step_portal")} className="flex-1 min-h-12 rounded-lg bg-[#0f4c81] text-white text-base font-semibold hover:bg-[#0c3c66] focus:outline-none focus:ring-2 focus:ring-[#0f4c81]">{t("next")}</button>
          </div>
        </section>
      )}

      {/* Step: Portal */}
      {current === "step_portal" && (
        <section className="bg-white border border-slate-200 rounded-xl p-6 space-y-4 shadow-xs">
          <h2 className="text-lg font-semibold text-slate-900">{t("scammed_step3_title")}</h2>
          <p className="text-base text-slate-700 leading-relaxed">{t("scammed_step3_body")}</p>
          <ol className="list-decimal pl-5 space-y-2 text-base text-slate-700">
            <li>{t("portal_step1")}</li>
            <li>{t("portal_step2")}</li>
            <li>{t("portal_step3")}</li>
            <li>{t("portal_step4")}</li>
          </ol>
          <a
            href={PORTAL_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center min-h-12 rounded-lg bg-[#0f4c81] text-white text-base font-semibold hover:bg-[#0c3c66] focus:outline-none focus:ring-2 focus:ring-[#0f4c81]"
          >
            cybercrime.gov.in
          </a>
          <div className="flex gap-3">
            <button onClick={() => setCurrent("step_evidence")} className="flex-1 min-h-12 rounded-lg border border-slate-300 text-slate-700 text-sm font-medium hover:bg-slate-50">{t("back")}</button>
            <button onClick={() => setCurrent("step_form")} className="flex-1 min-h-12 rounded-lg border border-[#0f4c81] text-[#0f4c81] text-base font-semibold hover:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-[#0f4c81]">{t("scammed_save_reference")}</button>
          </div>
        </section>
      )}

      {/* Step: Incident form + PDF */}
      {current === "step_form" && (
        <section className="bg-white border border-slate-200 rounded-xl p-6 space-y-4 shadow-xs">
          <h2 className="text-lg font-semibold text-slate-900">{t("scammed_step4_title")}</h2>
          <p className="text-base text-slate-700 leading-relaxed">{t("scammed_step4_body")}</p>
          <div className="space-y-3">
            {(["date", "amount", "account", "phone", "description"] as const).map((field) => (
              <div key={field}>
                <label className="block text-sm text-slate-600 mb-1">{t(`form_${field}`)}</label>
                {field === "description" ? (
                  <textarea
                    value={form[field]}
                    onChange={(e) => setForm((p) => ({ ...p, [field]: e.target.value }))}
                    rows={3}
                    className="w-full rounded-lg border border-slate-300 p-3 text-base text-slate-900 focus:outline-none focus:ring-2 focus:ring-[#0f4c81]"
                  />
                ) : (
                  <input
                    type={field === "date" ? "date" : "text"}
                    value={form[field]}
                    onChange={(e) => setForm((p) => ({ ...p, [field]: e.target.value }))}
                    className="w-full rounded-lg border border-slate-300 p-3 text-base text-slate-900 focus:outline-none focus:ring-2 focus:ring-[#0f4c81]"
                  />
                )}
              </div>
            ))}
          </div>
          <div className="flex gap-3">
            <button onClick={() => setCurrent("step_portal")} className="flex-1 min-h-12 rounded-lg border border-slate-300 text-slate-700 text-sm font-medium hover:bg-slate-50">{t("back")}</button>
            <button
              onClick={download}
              className="flex-1 min-h-12 rounded-lg bg-[#0f4c81] text-white text-base font-semibold hover:bg-[#0c3c66] focus:outline-none focus:ring-2 focus:ring-[#0f4c81]"
            >
              {t("scammed_download_pdf")}
            </button>
          </div>
          <p className="text-xs text-slate-500 leading-relaxed">{t("scammed_pdf_disclaimer")}</p>
        </section>
      )}
    </div>
  );
}

