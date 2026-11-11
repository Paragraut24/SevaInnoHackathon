import { useState } from "react";
import { useTranslation } from "react-i18next";

const LANGS = [
  { code: "mr", label: "मराठी" },
  { code: "hi", label: "हिन्दी" },
  { code: "en", label: "English" },
] as const;

export default function App() {
  const { t, i18n } = useTranslation();
  const [noticeDismissed, setNoticeDismissed] = useState(
    () => localStorage.getItem("sajag_privacy_ok") === "1"
  );

  const changeLang = (code: string) => {
    i18n.changeLanguage(code);
    localStorage.setItem("sajag_lang", code);
    document.documentElement.lang = code;
  };

  const dismissNotice = () => {
    localStorage.setItem("sajag_privacy_ok", "1");
    setNoticeDismissed(true);
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900">
      <header className="bg-white border-b border-slate-200 px-4 py-4">
        <div className="max-w-xl mx-auto flex items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold text-[#0f4c81]">{t("app_name")}</h1>
            <p className="text-sm text-slate-600">{t("tagline")}</p>
          </div>
          <nav aria-label={t("lang_label")} className="flex gap-1">
            {LANGS.map((l) => {
              const active = i18n.language === l.code;
              return (
                <button
                  key={l.code}
                  type="button"
                  onClick={() => changeLang(l.code)}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-[#0f4c81] ${
                    active
                      ? "bg-[#0f4c81] text-white"
                      : "bg-slate-100 text-slate-700 hover:bg-slate-200"
                  }`}
                >
                  {l.label}
                </button>
              );
            })}
          </nav>
        </div>
      </header>

      <main className="flex-1 w-full max-w-xl mx-auto px-4 py-6 space-y-6">
        {!noticeDismissed && (
          <section
            aria-label={t("privacy_title")}
            className="bg-sky-50 border border-sky-200 rounded-xl p-4 space-y-3"
          >
            <h2 className="text-base font-semibold text-slate-900">{t("privacy_title")}</h2>
            <p className="text-sm text-slate-700 leading-relaxed">{t("privacy_body")}</p>
            <button
              type="button"
              onClick={dismissNotice}
              className="px-4 py-2 rounded-lg bg-[#0f4c81] text-white text-sm font-medium hover:bg-[#0c3c66] focus:outline-none focus:ring-2 focus:ring-[#0f4c81]"
            >
              {t("privacy_ok")}
            </button>
          </section>
        )}

        <section className="bg-white border border-slate-200 rounded-xl p-6 space-y-3 shadow-xs">
          <h2 className="text-lg font-semibold text-slate-900">{t("placeholder_title")}</h2>
          <p className="text-base text-slate-700 leading-relaxed">{t("placeholder_desc")}</p>
        </section>

        <section className="bg-red-50 border border-red-200 rounded-xl p-4 flex flex-wrap items-center justify-between gap-4">
          <p className="text-sm font-medium text-red-900">{t("helpline_label")} 1930</p>
          <a
            href="tel:1930"
            className="px-4 py-2 rounded-lg bg-red-700 text-white text-sm font-semibold hover:bg-red-800 focus:outline-none focus:ring-2 focus:ring-red-600"
          >
            {t("call_1930")}
          </a>
        </section>
      </main>

      <footer className="border-t border-slate-200 bg-white px-4 py-4">
        <p className="max-w-xl mx-auto text-xs text-slate-500 text-center">
          {t("footer_disclaimer")}
        </p>
      </footer>
    </div>
  );
}

