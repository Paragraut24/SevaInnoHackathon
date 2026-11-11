import { useState } from "react";
import { useTranslation } from "react-i18next";

export default function PrivacyNotice() {
  const { t } = useTranslation();
  const [dismissed, setDismissed] = useState(() => localStorage.getItem("sajag_privacy_ok") === "1");

  if (dismissed) return null;

  const dismiss = () => {
    localStorage.setItem("sajag_privacy_ok", "1");
    setDismissed(true);
  };

  return (
    <section
      aria-label={t("privacy_title")}
      className="bg-sky-50 border border-sky-200 rounded-xl p-4 space-y-3"
    >
      <h2 className="text-base font-semibold text-slate-900">{t("privacy_title")}</h2>
      <p className="text-sm text-slate-700 leading-relaxed">{t("privacy_body")}</p>
      <button
        type="button"
        onClick={dismiss}
        className="px-4 py-2 rounded-lg bg-[#0f4c81] text-white text-sm font-medium hover:bg-[#0c3c66] focus:outline-none focus:ring-2 focus:ring-[#0f4c81]"
      >
        {t("privacy_ok")}
      </button>
    </section>
  );
}
