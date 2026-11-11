import { useTranslation } from "react-i18next";
import type { Lang } from "../lib/api";

const LANGS: { code: Lang; label: string }[] = [
  { code: "mr", label: "मराठी" },
  { code: "hi", label: "हिन्दी" },
  { code: "en", label: "English" },
];

export default function LangToggle() {
  const { t, i18n } = useTranslation();

  const changeLang = (code: Lang) => {
    i18n.changeLanguage(code);
    localStorage.setItem("sajag_lang", code);
    document.documentElement.lang = code;
  };

  return (
    <nav aria-label={t("lang_label")} className="flex gap-1">
      {LANGS.map((l) => (
        <button
          key={l.code}
          type="button"
          onClick={() => changeLang(l.code)}
          className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-[#0f4c81] ${
            i18n.language === l.code
              ? "bg-[#0f4c81] text-white"
              : "bg-slate-100 text-slate-700 hover:bg-slate-200"
          }`}
        >
          {l.label}
        </button>
      ))}
    </nav>
  );
}
