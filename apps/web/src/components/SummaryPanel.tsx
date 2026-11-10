import { Summary } from "@/lib/api";
import { Sparkles, CheckCircle2, Bookmark, ExternalLink } from "lucide-react";

interface SummaryPanelProps {
  summary: Summary | null | undefined;
  onSelectEvidence?: (sentenceIdx: number) => void;
}

export default function SummaryPanel({ summary, onSelectEvidence }: SummaryPanelProps) {
  if (!summary) {
    return (
      <div className="bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700/60 rounded-xl p-5 text-center text-sm text-slate-500">
        Summary generation in progress...
      </div>
    );
  }

  const isExtractive = summary.method === "extractive_fallback";

  return (
    <div className="bg-white dark:bg-slate-800/90 border border-slate-200 dark:border-slate-700 rounded-xl p-5 shadow-xs">
      {/* Header Pill */}
      <div className="flex items-center justify-between gap-2 mb-3">
        <span className="inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800">
          <Sparkles className="w-3.5 h-3.5" />
          {isExtractive ? "Extractive Fallback Summary" : "AI-Generated Summary"}
        </span>
        <span className="text-[11px] text-slate-400 font-mono">
          {summary.model}
        </span>
      </div>

      {/* Generated Headline */}
      {summary.headline_en && (
        <h2 className="text-base font-bold text-slate-900 dark:text-slate-100 mb-2 leading-snug">
          {summary.headline_en}
        </h2>
      )}

      {/* 2-3 Sentence Summary */}
      {summary.summary_en && (
        <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed mb-4">
          {summary.summary_en}
        </p>
      )}

      {/* Key Points with Evidence Citations */}
      {summary.key_points && summary.key_points.length > 0 && (
        <div className="mb-4">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">
            Key Highlights & Evidence
          </h4>
          <ul className="space-y-2">
            {summary.key_points.map((kp, idx) => (
              <li key={idx} className="text-xs sm:text-sm text-slate-700 dark:text-slate-300 flex items-start gap-2">
                <span className="text-indigo-600 dark:text-indigo-400 font-bold mt-0.5">•</span>
                <div className="flex-1">
                  <span>{kp.text}</span>
                  {kp.evidence && kp.evidence.length > 0 && (
                    <span className="inline-flex items-center gap-1 ml-2">
                      {kp.evidence.map((sIdx) => (
                        <button
                          key={sIdx}
                          type="button"
                          onClick={() => onSelectEvidence && onSelectEvidence(sIdx)}
                          className="px-1.5 py-0.5 text-[10px] font-mono font-bold bg-indigo-50 hover:bg-indigo-100 dark:bg-indigo-950/80 dark:hover:bg-indigo-900 text-indigo-600 dark:text-indigo-400 rounded border border-indigo-200 dark:border-indigo-800 transition cursor-pointer"
                          title={`Click to view Sentence [S${sIdx + 1}]`}
                        >
                          S{sIdx + 1}
                        </button>
                      ))}
                    </span>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Key Facts Grid */}
      {summary.key_facts && (
        <div className="pt-3 border-t border-slate-100 dark:border-slate-700/60">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">
            Verified Key Facts
          </h4>
          <div className="grid grid-cols-2 gap-2 text-xs">
            {summary.key_facts.who && summary.key_facts.who.length > 0 && (
              <div className="bg-slate-50 dark:bg-slate-900/40 p-2 rounded-lg">
                <span className="text-slate-400 block text-[10px] uppercase">Who</span>
                <span className="font-medium text-slate-800 dark:text-slate-200">
                  {summary.key_facts.who.join(", ")}
                </span>
              </div>
            )}
            {summary.key_facts.where && summary.key_facts.where.length > 0 && (
              <div className="bg-slate-50 dark:bg-slate-900/40 p-2 rounded-lg">
                <span className="text-slate-400 block text-[10px] uppercase">Where</span>
                <span className="font-medium text-slate-800 dark:text-slate-200">
                  {summary.key_facts.where.join(", ")}
                </span>
              </div>
            )}
            {summary.key_facts.numbers && summary.key_facts.numbers.length > 0 && (
              <div className="col-span-2 bg-slate-50 dark:bg-slate-900/40 p-2 rounded-lg">
                <span className="text-slate-400 block text-[10px] uppercase">Numbers & Quantities</span>
                <span className="font-semibold text-indigo-700 dark:text-indigo-300">
                  {summary.key_facts.numbers.join(" • ")}
                </span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

