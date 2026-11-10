"use client";

import { useState } from "react";
import { Sentence } from "@/lib/api";
import { AlertTriangle, Info, Columns, AlignLeft } from "lucide-react";

interface SideBySideProps {
  sentences: Sentence[];
  highlightedIdx?: number | null;
  onSentenceClick?: (idx: number) => void;
}

export default function SideBySide({ sentences, highlightedIdx: externalHighlighted, onSentenceClick }: SideBySideProps) {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);
  const [viewMode, setViewMode] = useState<"side-by-side" | "english" | "kannada">("side-by-side");
  const [selectedFlag, setSelectedFlag] = useState<{ sentenceIdx: number; flags: any[] } | null>(null);

  const activeIdx = externalHighlighted !== undefined && externalHighlighted !== null ? externalHighlighted : hoveredIdx;

  if (!sentences || sentences.length === 0) {
    return (
      <div className="p-8 text-center text-slate-500 bg-slate-50 dark:bg-slate-800/40 rounded-xl">
        No parsed sentences available.
      </div>
    );
  }

  return (
    <div className="my-6">
      {/* Reader Controls: 3-Way Mode Toggle */}
      <div className="flex items-center justify-between gap-4 mb-4 pb-3 border-b border-slate-200 dark:border-slate-800">
        <div className="flex items-center gap-1 bg-slate-100 dark:bg-slate-800 p-1 rounded-lg text-xs font-medium">
          <button
            type="button"
            onClick={() => setViewMode("side-by-side")}
            className={`px-3 py-1.5 rounded-md transition cursor-pointer flex items-center gap-1.5 ${
              viewMode === "side-by-side"
                ? "bg-white dark:bg-slate-700 text-indigo-600 dark:text-white shadow-xs font-bold"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900"
            }`}
          >
            <Columns className="w-3.5 h-3.5" />
            Side by Side
          </button>
          <button
            type="button"
            onClick={() => setViewMode("english")}
            className={`px-3 py-1.5 rounded-md transition cursor-pointer ${
              viewMode === "english"
                ? "bg-white dark:bg-slate-700 text-indigo-600 dark:text-white shadow-xs font-bold"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900"
            }`}
          >
            English Only
          </button>
          <button
            type="button"
            onClick={() => setViewMode("kannada")}
            className={`px-3 py-1.5 rounded-md transition cursor-pointer font-kannada ${
              viewMode === "kannada"
                ? "bg-white dark:bg-slate-700 text-indigo-600 dark:text-white shadow-xs font-bold"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900"
            }`}
          >
            ಕನ್ನಡ ಮಾತ್ರ
          </button>
        </div>

        <span className="text-xs text-slate-400 hidden sm:inline">
          {viewMode === "side-by-side" ? "Hover any sentence to highlight its counterpart" : `${sentences.length} sentences`}
        </span>
      </div>

      {/* Flag Discrepancy Detail Modal / Alert */}
      {selectedFlag && (
        <div className="mb-4 p-3.5 bg-amber-50 dark:bg-amber-950/70 border border-amber-200 dark:border-amber-800 rounded-lg text-xs text-amber-900 dark:text-amber-200 flex items-start justify-between gap-3">
          <div className="flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-bold">Sentence [S{selectedFlag.sentenceIdx + 1}] Quality Guard Flag:</p>
              <ul className="list-disc list-inside mt-1 space-y-0.5">
                {selectedFlag.flags.map((f, i) => (
                  <li key={i}>{f.detail || f.type}</li>
                ))}
              </ul>
            </div>
          </div>
          <button
            type="button"
            onClick={() => setSelectedFlag(null)}
            className="text-amber-700 hover:text-amber-950 font-bold px-2 py-0.5"
          >
            &times;
          </button>
        </div>
      )}

      {/* Side by Side View */}
      {viewMode === "side-by-side" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Left Column: Kannada Original */}
          <div className="space-y-3">
            <div className="text-xs font-bold uppercase tracking-wider text-slate-400 pb-1 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
              <span>ಮೂಲ ಕನ್ನಡ (Kannada Original)</span>
              <span className="text-[10px] font-normal">Noto Sans Kannada</span>
            </div>
            {sentences.map((sent) => {
              const isHovered = activeIdx === sent.idx;
              const hasFlags = sent.translation?.flags && sent.translation.flags.length > 0;
              return (
                <div
                  key={sent.id}
                  id={`kn-sent-${sent.idx}`}
                  onMouseEnter={() => setHoveredIdx(sent.idx)}
                  onMouseLeave={() => setHoveredIdx(null)}
                  onClick={() => onSentenceClick && onSentenceClick(sent.idx)}
                  className={`p-3 rounded-lg transition font-kannada text-base leading-kannada cursor-pointer border ${
                    isHovered
                      ? "bg-indigo-50/90 dark:bg-indigo-950/60 border-indigo-400 shadow-xs"
                      : "bg-white dark:bg-slate-800 border-slate-100 dark:border-slate-700/60"
                  } ${hasFlags ? "border-b-2 border-b-amber-400" : ""}`}
                >
                  <span className="text-[10px] font-mono font-bold text-slate-400 mr-2 select-none">
                    [S{sent.idx + 1}]
                  </span>
                  <span className="text-slate-900 dark:text-slate-100">{sent.text_kn}</span>
                </div>
              );
            })}
          </div>

          {/* Right Column: English Translation */}
          <div className="space-y-3">
            <div className="text-xs font-bold uppercase tracking-wider text-slate-400 pb-1 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
              <span>English Translation (IndicTrans2)</span>
              <span className="text-[10px] font-normal">Inter</span>
            </div>
            {sentences.map((sent) => {
              const isHovered = activeIdx === sent.idx;
              const flags = sent.translation?.flags || [];
              const hasFlags = flags.length > 0;
              return (
                <div
                  key={sent.id}
                  id={`en-sent-${sent.idx}`}
                  onMouseEnter={() => setHoveredIdx(sent.idx)}
                  onMouseLeave={() => setHoveredIdx(null)}
                  onClick={() => onSentenceClick && onSentenceClick(sent.idx)}
                  className={`p-3 rounded-lg transition text-sm leading-relaxed cursor-pointer border ${
                    isHovered
                      ? "bg-indigo-50/90 dark:bg-indigo-950/60 border-indigo-400 shadow-xs"
                      : "bg-white dark:bg-slate-800 border-slate-100 dark:border-slate-700/60"
                  } ${hasFlags ? "border-b-2 border-b-amber-400 bg-amber-50/30 dark:bg-amber-950/20" : ""}`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <span className="text-[10px] font-mono font-bold text-slate-400 mr-2 select-none">
                        [S{sent.idx + 1}]
                      </span>
                      <span className="text-slate-800 dark:text-slate-200">
                        {sent.translation?.text_en || "(Translating...)"}
                      </span>
                    </div>

                    {hasFlags && (
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedFlag({ sentenceIdx: sent.idx, flags });
                        }}
                        className="flex-shrink-0 text-amber-500 hover:text-amber-600 p-0.5"
                        title="Click to inspect discrepancy flag"
                      >
                        <AlertTriangle className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* English Only View */}
      {viewMode === "english" && (
        <div className="bg-white dark:bg-slate-800 p-6 rounded-xl border border-slate-200 dark:border-slate-700 space-y-4">
          {sentences.map((sent) => (
            <p key={sent.id} className="text-base text-slate-800 dark:text-slate-200 leading-relaxed">
              {sent.translation?.text_en}
            </p>
          ))}
        </div>
      )}

      {/* Kannada Only View */}
      {viewMode === "kannada" && (
        <div className="bg-white dark:bg-slate-800 p-6 rounded-xl border border-slate-200 dark:border-slate-700 space-y-4">
          {sentences.map((sent) => (
            <p key={sent.id} className="font-kannada text-lg text-slate-900 dark:text-slate-100 leading-kannada">
              {sent.text_kn}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}

