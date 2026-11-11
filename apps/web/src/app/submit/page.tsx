"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, getSessionId } from "@/lib/api";
import { Send, Globe, AlertTriangle, CheckCircle, ArrowRight, Loader2 } from "lucide-react";

export default function SubmitArticlePage() {
  const router = useRouter();

  const [mode, setMode] = useState<"text" | "url">("text");
  const [title, setTitle] = useState("");
  const [text, setText] = useState("");
  const [url, setUrl] = useState("");
  const [section, setSection] = useState("karnataka");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Live Kannada script detection
  const calculateKannadaRatio = (str: string) => {
    let kannada = 0;
    let nonKannadaLetters = 0;
    for (const char of str) {
      const code = char.charCodeAt(0);
      if (code >= 0x0c80 && code <= 0x0cff) {
        kannada++;
      } else if (/[a-zA-Z]/.test(char)) {
        nonKannadaLetters++;
      }
    }
    const total = kannada + nonKannadaLetters;
    return total === 0 ? 0 : Math.round((kannada / total) * 100);
  };

  const kannadaRatio = mode === "text" ? calculateKannadaRatio(text) : 100;
  const isSuspiciousScript = mode === "text" && text.length > 20 && kannadaRatio < 35;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      const sid = getSessionId();
      const res = await api.submitArticle({
        title: title.trim() || undefined,
        text: mode === "text" ? text.trim() : undefined,
        url: mode === "url" ? url.trim() : undefined,
        section_label: section,
        session_id: sid,
      });

      // Immediate redirect to article page where live progress tracking handles completion
      router.push(`/article/${res.article_id}`);
    } catch (err: any) {
      setError(err.message || "Failed to submit article.");
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto py-6">
      <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-xs">
        <h1 className="text-xl sm:text-2xl font-bold text-slate-900 mb-1">
          Submit Kannada News Article
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 mb-6">
          Paste authentic Kannada news text or enter an article URL from permitted publications. The AI pipeline will normalize, translate, and verify the story.
        </p>

        {/* Input Mode Toggle */}
        <div className="flex items-center gap-2 mb-6 p-1 bg-slate-100 rounded-lg max-w-xs text-xs font-medium">
          <button
            type="button"
            onClick={() => setMode("text")}
            className={`flex-1 py-1.5 rounded-md transition cursor-pointer text-center ${
              mode === "text" ? "bg-white text-indigo-600 shadow-xs font-bold" : "text-slate-500"
            }`}
          >
            Paste Kannada Text
          </button>
          <button
            type="button"
            onClick={() => setMode("url")}
            className={`flex-1 py-1.5 rounded-md transition cursor-pointer text-center ${
              mode === "url" ? "bg-white text-indigo-600 shadow-xs font-bold" : "text-slate-500"
            }`}
          >
            News Article URL
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Headline / Title (Optional)
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. ಬೆಂಗಳೂರು ಮೆಟ್ರೋ ಹೊಸ ಮಾರ್ಗ ಉದ್ಘಾಟನೆ"
              className="w-full text-sm p-2.5 bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Category
            </label>
            <select
              value={section}
              onChange={(e) => setSection(e.target.value)}
              className="w-full text-sm p-2.5 bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none"
            >
              <option value="karnataka">Karnataka & Bengaluru</option>
              <option value="politics">Politics (ರಾಜಕೀಯ)</option>
              <option value="technology">Technology & Science (ತಂತ್ರಜ್ಞಾನ)</option>
              <option value="sports">Sports (ಕ್ರೀಡೆ)</option>
              <option value="business">Business & Economy (ವಾಣಿಜ್ಯ)</option>
            </select>
          </div>

          {mode === "text" ? (
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-xs font-semibold text-slate-700">
                  Kannada Body Text *
                </label>
                {text.length > 0 && (
                  <span
                    className={`text-[11px] font-mono font-medium ${
                      kannadaRatio >= 35 ? "text-emerald-600" : "text-amber-600"
                    }`}
                  >
                    Kannada Script: {kannadaRatio}%
                  </span>
                )}
              </div>
              <textarea
                rows={6}
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="ಕನ್ನಡ ಸುದ್ದಿಯನ್ನು ಇಲ್ಲಿ ನಮೂದಿಸಿ..."
                className="w-full font-kannada text-base p-3 bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none leading-kannada"
                required
              />
              {isSuspiciousScript && (
                <div className="mt-1.5 flex items-center gap-1.5 text-xs text-amber-600">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  <span>
                    Warning: The input contains very little Kannada script. The pipeline will validate and may reject non-Kannada articles.
                  </span>
                </div>
              )}
            </div>
          ) : (
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Article URL * (Permitted Outlets)
              </label>
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://www.prajavani.net/karnataka-news/..."
                className="w-full text-sm p-2.5 bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                required
              />
              <p className="text-[11px] text-slate-400 mt-1">
                Allowed outlets: Prajavani, Kannada Prabha, Vijay Karnataka, Udayavani, Vijayavani.
              </p>
            </div>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="w-full mt-4 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-2.5 rounded-xl shadow-xs transition flex items-center justify-center gap-2 text-sm disabled:opacity-50 cursor-pointer"
          >
            {submitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Submitting to AI Pipeline...</span>
              </>
            ) : (
              <>
                <Send className="w-4 h-4" />
                <span>Process Article with AI Pipeline</span>
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
