import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import type { Lang } from "../lib/api";

interface ReadAloudProps {
  text: string;
  lang: Lang;
}

const BCP47_TAGS: Record<Lang, string> = {
  mr: "mr-IN",
  hi: "hi-IN",
  en: "en-IN",
};

export default function ReadAloud({ text, lang }: ReadAloudProps) {
  const { t } = useTranslation();
  const [supported, setSupported] = useState(false);
  const [speaking, setSpeaking] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) {
      setSupported(false);
      return;
    }

    const checkVoices = () => {
      const voices = window.speechSynthesis.getVoices();
      const targetTag = BCP47_TAGS[lang] || "en-US";
      const hasVoice = voices.some((v) =>
        v.lang.toLowerCase().replace("_", "-").startsWith(targetTag.slice(0, 2).toLowerCase())
      );
      // Support if voices are loaded and language or fallback exists
      setSupported(hasVoice || voices.length > 0);
    };

    checkVoices();
    window.speechSynthesis.onvoiceschanged = checkVoices;

    return () => {
      if (window.speechSynthesis.speaking) {
        window.speechSynthesis.cancel();
      }
    };
  }, [lang]);

  if (!supported) return null;

  const toggle = () => {
    if (speaking) {
      window.speechSynthesis.cancel();
      setSpeaking(false);
      return;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    const targetTag = BCP47_TAGS[lang] || "en-US";
    utterance.lang = targetTag;
    utterance.rate = 0.95; // Slightly slower for clarity

    const voices = window.speechSynthesis.getVoices();
    const voice = voices.find((v) =>
      v.lang.toLowerCase().replace("_", "-").startsWith(targetTag.toLowerCase())
    ) || voices.find((v) =>
      v.lang.toLowerCase().replace("_", "-").startsWith(targetTag.slice(0, 2).toLowerCase())
    );
    if (voice) {
      utterance.voice = voice;
    }

    utterance.onend = () => setSpeaking(false);
    utterance.onerror = () => setSpeaking(false);

    setSpeaking(true);
    window.speechSynthesis.speak(utterance);
  };

  return (
    <button
      type="button"
      onClick={toggle}
      className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-slate-300 text-sm font-medium text-slate-700 bg-white hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-[#0f4c81]"
      aria-label={speaking ? t("read_aloud_stop") : t("read_aloud")}
    >
      <svg
        className="w-4 h-4 text-slate-600"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        {speaking ? (
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z"
          />
        ) : (
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z"
          />
        )}
      </svg>
      <span>{speaking ? t("read_aloud_stop") : t("read_aloud")}</span>
    </button>
  );
}

