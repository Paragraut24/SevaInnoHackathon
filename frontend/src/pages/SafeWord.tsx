import { useState } from "react";
import { useTranslation } from "react-i18next";
import { QRCodeSVG } from "qrcode.react";
import { generateSafeWord, type SafeWordResult } from "../lib/safeWord";
import type { Lang } from "../lib/api";

export default function SafeWord() {
  const { t, i18n } = useTranslation();
  const [result, setResult] = useState<SafeWordResult | null>(null);
  const [copied, setCopied] = useState(false);

  const generate = () => {
    setResult(generateSafeWord(i18n.language as Lang));
    setCopied(false);
  };

  const copy = async () => {
    if (!result) return;
    await navigator.clipboard.writeText(result.shareText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      <section className="bg-white border border-slate-200 rounded-xl p-6 space-y-4 shadow-xs">
        <h2 className="text-lg font-semibold text-slate-900">{t("safe_word_title")}</h2>
        <p className="text-base text-slate-700 leading-relaxed">{t("safe_word_desc")}</p>

        <button
          onClick={generate}
          className="min-h-12 px-6 py-2 rounded-lg bg-[#0f4c81] text-white text-base font-semibold hover:bg-[#0c3c66] focus:outline-none focus:ring-2 focus:ring-[#0f4c81]"
        >
          {t("safe_word_generate")}
        </button>

        {result && (
          <div className="space-y-4 pt-2">
            <div className="rounded-lg bg-slate-50 border border-slate-200 p-4 space-y-3">
              <div>
                <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">{t("safe_word_phrase_label")}</p>
                <p className="text-2xl font-bold text-[#0f4c81] mt-1">{result.phrase}</p>
              </div>
              <div>
                <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">{t("safe_word_challenge_label")}</p>
                <p className="text-base text-slate-900 mt-1">{result.challenge}</p>
              </div>
            </div>

            <div className="flex justify-center">
            <QRCodeSVG value={result.shareText} size={160} level="M" />
            </div>

            <button
              onClick={copy}
              className="w-full min-h-12 px-4 py-2 rounded-lg border border-slate-300 text-base text-slate-700 font-medium hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-[#0f4c81]"
            >
              {copied ? t("safe_word_copied") : t("safe_word_copy")}
            </button>

            <p className="text-sm text-slate-600 leading-relaxed">{t("safe_word_instructions")}</p>
          </div>
        )}
      </section>
    </div>
  );
}
