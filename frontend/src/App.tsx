import { useTranslation } from "react-i18next";
import LangToggle from "./components/LangToggle";
import PrivacyNotice from "./components/PrivacyNotice";
import Check from "./pages/Check";

export default function App() {
  const { t } = useTranslation();

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900">
      <header className="bg-white border-b border-slate-200 px-4 py-4">
        <div className="max-w-xl mx-auto flex items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold text-[#0f4c81]">{t("app_name")}</h1>
            <p className="text-sm text-slate-600">{t("tagline")}</p>
          </div>
          <LangToggle />
        </div>
      </header>

      <main className="flex-1 w-full max-w-xl mx-auto px-4 py-6 space-y-6">
        <PrivacyNotice />
        <Check />

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
