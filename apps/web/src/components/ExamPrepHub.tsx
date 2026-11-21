"use client";

import { useEffect, useState } from "react";
import {
  GraduationCap,
  CheckCircle2,
  XCircle,
  HelpCircle,
  BookOpen,
  RefreshCw,
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
  FileText,
  Award,
  Sparkles,
  ExternalLink,
} from "lucide-react";
import { api, ExamPrepResponse, ExamMCQ, ExamDescriptive } from "@/lib/api";

interface ExamPrepHubProps {
  articleId: number;
  onSelectEvidence?: (sentenceIdx: number) => void;
}

export default function ExamPrepHub({ articleId, onSelectEvidence }: ExamPrepHubProps) {
  const [data, setData] = useState<ExamPrepResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [activeTab, setActiveTab] = useState<"prelims" | "mains">("prelims");

  // Track user selections for each MCQ: { [mcqIndex]: selectedOptionIndex }
  const [selectedAnswers, setSelectedAnswers] = useState<{ [key: number]: number }>({});
  
  // Track expanded state for descriptive questions: { [descIndex]: boolean }
  const [expandedMains, setExpandedMains] = useState<{ [key: number]: boolean }>({ 0: true });

  // Track copy feedback for descriptive questions
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const fetchExamPrep = async (force: boolean = false) => {
    if (force) setRefreshing(true);
    else setLoading(true);
    setError(null);

    try {
      const res = await api.getExamPrep(articleId, force);
      setData(res);
      // Reset selections on fresh generation
      if (force) {
        setSelectedAnswers({});
        setExpandedMains({ 0: true });
      }
    } catch (err: any) {
      console.error("Failed to load exam prep:", err);
      setError(err.message || "Failed to generate exam questions. Please retry.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    if (articleId) {
      fetchExamPrep(false);
    }
  }, [articleId]);

  const handleSelectOption = (mcqIdx: number, optIdx: number) => {
    setSelectedAnswers((prev) => ({ ...prev, [mcqIdx]: optIdx }));
  };

  const toggleMainsExpanded = (idx: number) => {
    setExpandedMains((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  const handleCopyMains = (desc: ExamDescriptive, idx: number) => {
    const textToCopy = `[UPSC / KPSC Mains Question - ${desc.syllabus_paper} (${desc.marks} Marks | ${desc.word_limit} Words)]\n\nQ: ${desc.question}\n\n--- MODEL ANSWER OUTLINE ---\n\n• Introduction: ${desc.model_answer.introduction}\n\n• Core Analytical Dimensions:\n${desc.model_answer.key_dimensions.map((d) => `  - ${d}`).join("\n")}\n\n• Policy & Constitutional Framework: ${desc.model_answer.policy_implications}\n\n• Way Forward: ${desc.model_answer.way_forward}`;

    navigator.clipboard.writeText(textToCopy);
    setCopiedIndex(idx);
    setTimeout(() => setCopiedIndex(null), 2500);
  };

  if (loading) {
    return (
      <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700/80 rounded-2xl p-6 shadow-xs animate-pulse">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-9 h-9 rounded-xl bg-indigo-100 dark:bg-indigo-950/60" />
          <div className="space-y-1.5 flex-1">
            <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-1/3" />
            <div className="h-3 bg-slate-100 dark:bg-slate-800 rounded w-1/2" />
          </div>
        </div>
        <div className="h-20 bg-slate-50 dark:bg-slate-800/40 rounded-xl mb-4" />
        <div className="h-32 bg-slate-100 dark:bg-slate-700/40 rounded-xl" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700/80 rounded-2xl p-6 shadow-xs text-center">
        <GraduationCap className="w-10 h-10 text-indigo-500 mx-auto mb-2 opacity-80" />
        <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100">UPSC & KPSC Study Hub</h3>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 mb-4">
          {error || "Exam questions could not be prepared for this article."}
        </p>
        <button
          type="button"
          onClick={() => fetchExamPrep(true)}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-xs transition"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Try Generating Again
        </button>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-slate-800/90 border border-slate-200 dark:border-slate-700/80 rounded-2xl p-5 sm:p-6 shadow-xs space-y-5">
      {/* Header */}
      <div className="flex items-start justify-between gap-3 pb-3 border-b border-slate-100 dark:border-slate-700/60">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-indigo-700 text-white flex items-center justify-center shadow-xs">
            <GraduationCap className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm sm:text-base font-extrabold text-slate-900 dark:text-slate-100 tracking-tight">
                UPSC & KPSC Civil Services Study Hub
              </h3>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-indigo-50 dark:bg-indigo-950/80 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800 flex items-center gap-1">
                <Sparkles className="w-2.5 h-2.5" />
                Exam-Ready
              </span>
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
              Grounded current affairs questions curated from this verified Kannada report
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={() => fetchExamPrep(true)}
          disabled={refreshing}
          title="Regenerate questions using Gemini"
          className="p-1.5 text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700/50 transition cursor-pointer disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin text-indigo-600" : ""}`} />
        </button>
      </div>

      {/* Exam Relevance Callout */}
      {data.exam_relevance_summary && (
        <div className="bg-gradient-to-r from-indigo-50/70 to-blue-50/70 dark:from-indigo-950/40 dark:to-blue-950/30 border border-indigo-100 dark:border-indigo-900/60 rounded-xl p-3.5 text-xs text-indigo-950 dark:text-indigo-200 space-y-1.5">
          <div className="flex items-center gap-1.5 font-bold uppercase tracking-wider text-[10px] text-indigo-700 dark:text-indigo-400">
            <Award className="w-3.5 h-3.5" />
            <span>Syllabus Relevance & Exam Utility</span>
          </div>
          <p className="leading-relaxed text-[11px] font-medium text-slate-700 dark:text-slate-300">
            {data.exam_relevance_summary}
          </p>
          {data.syllabus_focus && data.syllabus_focus.length > 0 && (
            <div className="flex flex-wrap gap-1.5 pt-1">
              {data.syllabus_focus.map((tag, idx) => (
                <span
                  key={idx}
                  className="px-2 py-0.5 bg-white dark:bg-slate-800 text-indigo-800 dark:text-indigo-300 text-[10px] font-semibold rounded-md border border-indigo-100 dark:border-indigo-800 shadow-2xs"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Mode Switcher Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200 dark:border-slate-700/60 pb-2">
        <button
          type="button"
          onClick={() => setActiveTab("prelims")}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-bold transition cursor-pointer ${
            activeTab === "prelims"
              ? "bg-indigo-600 text-white shadow-xs"
              : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700/50"
          }`}
        >
          <CheckCircle2 className="w-3.5 h-3.5" />
          <span>Prelims Practice (MCQs)</span>
          <span className="text-[10px] px-1.5 py-0.2 bg-white/20 rounded-full font-mono">
            {data.mcqs?.length || 0}
          </span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab("mains")}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-bold transition cursor-pointer ${
            activeTab === "mains"
              ? "bg-indigo-600 text-white shadow-xs"
              : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700/50"
          }`}
        >
          <FileText className="w-3.5 h-3.5" />
          <span>Mains Answer Writing</span>
          <span className="text-[10px] px-1.5 py-0.2 bg-white/20 rounded-full font-mono">
            {data.descriptive?.length || 0}
          </span>
        </button>
      </div>

      {/* Tab 1: Prelims MCQs */}
      {activeTab === "prelims" && (
        <div className="space-y-5">
          {data.mcqs && data.mcqs.length > 0 ? (
            data.mcqs.map((mcq, qIdx) => {
              const selectedOpt = selectedAnswers[qIdx];
              const isAnswered = selectedOpt !== undefined;
              const isCorrect = isAnswered && selectedOpt === mcq.correct_index;

              return (
                <div
                  key={qIdx}
                  className="bg-slate-50/80 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700/70 rounded-xl p-4 transition-all"
                >
                  {/* Meta Bar */}
                  <div className="flex items-center justify-between gap-2 mb-2.5">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-700 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-950/60 px-2 py-0.5 rounded border border-indigo-100 dark:border-indigo-900/50">
                      Question {qIdx + 1} • {mcq.subject_tag || "General Studies"}
                    </span>
                    <span className="text-[10px] font-medium text-slate-400 dark:text-slate-500">
                      Difficulty: <strong className="font-semibold text-slate-600 dark:text-slate-300">{mcq.difficulty || "Medium"}</strong>
                    </span>
                  </div>

                  {/* Question Text */}
                  <div className="text-xs sm:text-sm font-semibold text-slate-900 dark:text-slate-100 whitespace-pre-line leading-relaxed mb-3">
                    {mcq.question}
                  </div>

                  {/* Options List */}
                  <div className="space-y-2 mb-3">
                    {mcq.options.map((opt, optIdx) => {
                      const isThisSelected = selectedOpt === optIdx;
                      const isThisCorrect = optIdx === mcq.correct_index;

                      let style = "bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 hover:border-indigo-300 hover:bg-indigo-50/30";

                      if (isAnswered) {
                        if (isThisCorrect) {
                          style = "bg-emerald-50 dark:bg-emerald-950/60 border-emerald-500 text-emerald-900 dark:text-emerald-200 font-semibold";
                        } else if (isThisSelected && !isCorrect) {
                          style = "bg-rose-50 dark:bg-rose-950/60 border-rose-400 text-rose-900 dark:text-rose-200";
                        } else {
                          style = "bg-white/60 dark:bg-slate-800/60 border-slate-200/60 dark:border-slate-700/60 text-slate-400 dark:text-slate-500";
                        }
                      }

                      return (
                        <button
                          key={optIdx}
                          type="button"
                          onClick={() => handleSelectOption(qIdx, optIdx)}
                          className={`w-full text-left p-2.5 rounded-lg border text-xs flex items-center justify-between gap-3 transition cursor-pointer ${style}`}
                        >
                          <span className="leading-snug">{opt}</span>
                          {isAnswered && isThisCorrect && (
                            <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
                          )}
                          {isAnswered && isThisSelected && !isCorrect && (
                            <XCircle className="w-4 h-4 text-rose-500 dark:text-rose-400 shrink-0" />
                          )}
                        </button>
                      );
                    })}
                  </div>

                  {/* Answer & Explanation Box (Revealed upon selection) */}
                  {isAnswered && (
                    <div className={`p-3 rounded-lg border text-xs space-y-2 animate-fadeIn ${
                      isCorrect
                        ? "bg-emerald-50/80 dark:bg-emerald-950/40 border-emerald-200 dark:border-emerald-800 text-emerald-950 dark:text-emerald-200"
                        : "bg-amber-50/80 dark:bg-amber-950/40 border-amber-200 dark:border-amber-800 text-amber-950 dark:text-amber-200"
                    }`}>
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-bold flex items-center gap-1.5">
                          {isCorrect ? (
                            <>
                              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                              <span>Correct Answer! Option {String.fromCharCode(65 + mcq.correct_index)}</span>
                            </>
                          ) : (
                            <>
                              <XCircle className="w-4 h-4 text-rose-600" />
                              <span>Incorrect! Correct Option is {String.fromCharCode(65 + mcq.correct_index)}</span>
                            </>
                          )}
                        </span>

                        {/* Evidence Sentence Pills */}
                        {mcq.evidence_indices && mcq.evidence_indices.length > 0 && (
                          <div className="flex items-center gap-1">
                            <span className="text-[10px] text-slate-500 dark:text-slate-400">Evidence:</span>
                            {mcq.evidence_indices.map((sIdx) => (
                              <button
                                key={sIdx}
                                type="button"
                                onClick={() => onSelectEvidence && onSelectEvidence(sIdx)}
                                className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-indigo-100 hover:bg-indigo-200 dark:bg-indigo-900/80 text-indigo-700 dark:text-indigo-300 transition cursor-pointer"
                                title={`Click to jump to sentence [S${sIdx}] in reader`}
                              >
                                [S{sIdx}]
                              </button>
                            ))}
                          </div>
                        )}
                      </div>

                      <p className="text-[11px] leading-relaxed text-slate-700 dark:text-slate-300 pt-1 border-t border-slate-200/60 dark:border-slate-700/60">
                        {mcq.explanation}
                      </p>
                    </div>
                  )}
                </div>
              );
            })
          ) : (
            <p className="text-xs text-slate-500 text-center py-4">No MCQs available for this story.</p>
          )}
        </div>
      )}

      {/* Tab 2: Mains Descriptive Questions */}
      {activeTab === "mains" && (
        <div className="space-y-5">
          {data.descriptive && data.descriptive.length > 0 ? (
            data.descriptive.map((desc, dIdx) => {
              const isExpanded = expandedMains[dIdx] !== false;

              return (
                <div
                  key={dIdx}
                  className="bg-slate-50/80 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700/70 rounded-xl p-4 transition-all"
                >
                  {/* Meta Bar */}
                  <div className="flex flex-wrap items-center justify-between gap-2 mb-2.5">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-700 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-950/60 px-2 py-0.5 rounded border border-indigo-100 dark:border-indigo-900/50">
                        Mains Question {dIdx + 1}
                      </span>
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-slate-200/70 dark:bg-slate-700 text-slate-700 dark:text-slate-300">
                        {desc.syllabus_paper || "GS Paper II"}
                      </span>
                    </div>

                    <span className="text-[10px] font-semibold text-slate-500 dark:text-slate-400">
                      {desc.marks || 10} Marks • {desc.word_limit || 150} Words
                    </span>
                  </div>

                  {/* Question Statement */}
                  <div className="text-xs sm:text-sm font-bold text-slate-900 dark:text-slate-100 leading-relaxed mb-3">
                    "{desc.question}"
                  </div>

                  {/* Actions & Expand Toggle */}
                  <div className="flex items-center justify-between gap-2 pt-2 border-t border-slate-200/60 dark:border-slate-700/60">
                    <button
                      type="button"
                      onClick={() => toggleMainsExpanded(dIdx)}
                      className="inline-flex items-center gap-1.5 text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:underline cursor-pointer"
                    >
                      <BookOpen className="w-3.5 h-3.5" />
                      <span>{isExpanded ? "Hide Model Answer Framework" : "View Structured Model Answer"}</span>
                      {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                    </button>

                    <button
                      type="button"
                      onClick={() => handleCopyMains(desc, dIdx)}
                      className="inline-flex items-center gap-1 text-[11px] font-medium text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200 px-2 py-1 rounded hover:bg-slate-200/50 dark:hover:bg-slate-800 transition cursor-pointer"
                    >
                      {copiedIndex === dIdx ? (
                        <>
                          <Check className="w-3.5 h-3.5 text-emerald-600" />
                          <span className="text-emerald-600">Copied</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3.5 h-3.5" />
                          <span>Copy Answer Framework</span>
                        </>
                      )}
                    </button>
                  </div>

                  {/* Expandable Model Answer */}
                  {isExpanded && desc.model_answer && (
                    <div className="mt-3.5 p-3.5 bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 text-xs space-y-3 animate-fadeIn">
                      {/* Introduction */}
                      <div>
                        <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500 mb-1">
                          1. Context & Introduction (20-30 Words)
                        </div>
                        <p className="text-slate-700 dark:text-slate-200 leading-relaxed">
                          {desc.model_answer.introduction}
                        </p>
                      </div>

                      {/* Key Dimensions */}
                      {desc.model_answer.key_dimensions && desc.model_answer.key_dimensions.length > 0 && (
                        <div>
                          <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500 mb-1">
                            2. Core Analytical Dimensions & Evidence
                          </div>
                          <ul className="space-y-1.5 list-disc list-inside text-slate-700 dark:text-slate-200">
                            {desc.model_answer.key_dimensions.map((dim, kIdx) => (
                              <li key={kIdx} className="leading-relaxed">
                                {dim}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Policy & Constitutional Framework */}
                      {desc.model_answer.policy_implications && (
                        <div>
                          <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500 mb-1">
                            3. Governance & Policy Linkages
                          </div>
                          <p className="text-slate-700 dark:text-slate-200 leading-relaxed bg-slate-50 dark:bg-slate-900/60 p-2 rounded border border-slate-100 dark:border-slate-700/60">
                            {desc.model_answer.policy_implications}
                          </p>
                        </div>
                      )}

                      {/* Way Forward */}
                      {desc.model_answer.way_forward && (
                        <div>
                          <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500 mb-1">
                            4. Administrative Way Forward & Recommendations
                          </div>
                          <p className="text-slate-700 dark:text-slate-200 leading-relaxed">
                            {desc.model_answer.way_forward}
                          </p>
                        </div>
                      )}

                      {/* Evidence Citations */}
                      {desc.evidence_indices && desc.evidence_indices.length > 0 && (
                        <div className="pt-2 border-t border-slate-100 dark:border-slate-700 flex items-center gap-1.5">
                          <span className="text-[10px] text-slate-400">Cited Sentences:</span>
                          {desc.evidence_indices.map((sIdx) => (
                            <button
                              key={sIdx}
                              type="button"
                              onClick={() => onSelectEvidence && onSelectEvidence(sIdx)}
                              className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-indigo-50 hover:bg-indigo-100 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 transition cursor-pointer"
                              title={`Jump to sentence [S${sIdx}] in reader`}
                            >
                              [S{sIdx}]
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })
          ) : (
            <p className="text-xs text-slate-500 text-center py-4">No descriptive questions available.</p>
          )}
        </div>
      )}
    </div>
  );
}
