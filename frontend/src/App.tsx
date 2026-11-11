import { lazy, Suspense } from "react";
import { NavLink, Route, Routes } from "react-router-dom";
import { useTranslation } from "react-i18next";
import LangToggle from "./components/LangToggle";
import PrivacyNotice from "./components/PrivacyNotice";
import Check from "./pages/Check";

const SafeWord = lazy(() => import("./pages/SafeWord"));
const Scammed = lazy(() => import("./pages/Scammed"));
const Media = lazy(() => import("./pages/Media"));
const Dashboard = lazy(() => import("./pages/Dashboard"));

const NAV_LINK_CLASS = ({ isActive }: { isActive: boolean }) =>
  `text-sm font-medium px-3 py-2 rounded-lg transition-colors ${
    isActive
      ? "bg-[#0f4c81] text-white"
      : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
  }`;

export default function App() {
  const { t } = useTranslation();

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900">
      <header className="bg-white border-b border-slate-200 px-4 py-3 sticky top-0 z-10">
        <div className="max-w-2xl mx-auto space-y-2">
          <div className="flex items-center justify-between gap-4">
            <div>
              <h1 className="text-xl font-bold text-[#0f4c81]">{t("app_name")}</h1>
              <p className="text-xs text-slate-500">{t("tagline")}</p>
            </div>
            <LangToggle />
          </div>
          <nav aria-label="Main navigation" className="flex flex-wrap gap-1">
            <NavLink to="/" end className={NAV_LINK_CLASS}>{t("nav_check")}</NavLink>
            <NavLink to="/safe-word" className={NAV_LINK_CLASS}>{t("nav_safe_word")}</NavLink>
            <NavLink to="/scammed" className={NAV_LINK_CLASS}>{t("nav_scammed")}</NavLink>
            <NavLink to="/media" className={NAV_LINK_CLASS}>{t("nav_media")}</NavLink>
            <NavLink to="/dashboard" className={NAV_LINK_CLASS}>{t("nav_dashboard")}</NavLink>
          </nav>
        </div>
      </header>

      <main className="flex-1 w-full max-w-2xl mx-auto px-4 py-6">
        <PrivacyNotice />
        <Suspense fallback={<p className="text-center py-12 text-slate-500">{t("loading")}</p>}>
          <Routes>
            <Route path="/" element={
              <div className="space-y-6">
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
              </div>
            } />
            <Route path="/safe-word" element={<SafeWord />} />
            <Route path="/scammed" element={<Scammed />} />
            <Route path="/media" element={<Media />} />
            <Route path="/dashboard" element={<Dashboard />} />
          </Routes>
        </Suspense>
      </main>

      <footer className="border-t border-slate-200 bg-white px-4 py-4">
        <p className="max-w-2xl mx-auto text-xs text-slate-500 text-center">
          {t("footer_disclaimer")}
        </p>
      </footer>
    </div>
  );
}
