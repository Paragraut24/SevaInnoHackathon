import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import mr from "./mr.json";
import hi from "./hi.json";
import en from "./en.json";

const savedLang = localStorage.getItem("sajag_lang");
const defaultLang = savedLang === "mr" || savedLang === "hi" || savedLang === "en" ? savedLang : "mr";

i18n.use(initReactI18next).init({
  resources: {
    mr: { translation: mr },
    hi: { translation: hi },
    en: { translation: en },
  },
  lng: defaultLang,
  fallbackLng: "en",
  interpolation: { escapeValue: false },
});

export default i18n;

