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
  Bookmark,
  BookmarkCheck,
  Download,
  Trash2,
  ListFilter,
  CheckCheck,
  Printer,
} from "lucide-react";
import { api, ExamPrepResponse, ExamMCQ, ExamDescriptive } from "@/lib/api";

interface ExamPrepHubProps {
  articleId: number;
  onSelectEvidence?: (sentenceIdx: number) => void;
}

interface SavedMCQItem extends ExamMCQ {
  articleId: number;
  savedAt: string;
}

const LOCAL_STORAGE_KEY = "kannada_news_saved_mcqs";

export default function ExamPrepHub({ articleId, onSelectEvidence }: ExamPrepHubProps) {
  const [data, setData] = useState<ExamPrepResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [activeTab, setActiveTab] = useState<"prelims" | "mains" | "saved">("prelims");

  // Track user selections for each MCQ: { [mcqIndex]: selectedOptionIndex }
  const [selectedAnswers, setSelectedAnswers] = useState<{ [key: number]: number }>({});
  
  // Track expanded state for descriptive questions: { [descIndex]: boolean }
  const [expandedMains, setExpandedMains] = useState<{ [key: number]: boolean }>({ 0: true });

  // Track copy feedback for individual descriptive questions
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  // Track copy all questions feedback
  const [copiedAll, setCopiedAll] = useState(false);

  // Saved MCQs in localStorage
  const [savedMcqs, setSavedMcqs] = useState<SavedMCQItem[]>([]);

  // Load saved MCQs from localStorage
  useEffect(() => {
    try {
      const stored = localStorage.getItem(LOCAL_STORAGE_KEY);
      if (stored) {
        setSavedMcqs(JSON.parse(stored));
      }
    } catch (e) {
      console.error("Failed to load saved MCQs:", e);
    }
  }, []);

  const persistSavedMcqs = (items: SavedMCQItem[]) => {
    setSavedMcqs(items);
    try {
      localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(items));
    } catch (e) {
      console.error("Failed to save MCQs to storage:", e);
    }
  };

  const isMcqSaved = (mcq: ExamMCQ): boolean => {
    return savedMcqs.some(
      (s) => s.question.trim().toLowerCase() === mcq.question.trim().toLowerCase()
    );
  };

  const toggleSaveMcq = (mcq: ExamMCQ) => {
    const alreadySaved = isMcqSaved(mcq);
    if (alreadySaved) {
      const filtered = savedMcqs.filter(
        (s) => s.question.trim().toLowerCase() !== mcq.question.trim().toLowerCase()
      );
      persistSavedMcqs(filtered);
    } else {
      const newItem: SavedMCQItem = {
        ...mcq,
        articleId,
        savedAt: new Date().toISOString(),
      };
      persistSavedMcqs([newItem, ...savedMcqs]);
    }
  };

  const clearAllSaved = () => {
    if (confirm("Are you sure you want to clear all bookmarked questions?")) {
      persistSavedMcqs([]);
    }
  };

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

  // Build full study text for download/copy
  const generateFullStudySheet = (): string => {
    if (!data) return "";

    let text = `========================================================================\n`;
    text += `   UPSC & KPSC CIVIL SERVICES COMPREHENSIVE PRACTICE SHEET\n`;
    text += `   Grounded in Regional Kannada Journalism (KannadaNewsAI)\n`;
    text += `========================================================================\n\n`;
    text += `EXAM RELEVANCE:\n${data.exam_relevance_summary}\n\n`;
    text += `SYLLABUS TOPICS:\n${data.syllabus_focus?.join(" | ") || "General Studies"}\n\n`;
    text += `------------------------------------------------------------------------\n`;
    text += `PART I: PRELIMS MULTIPLE CHOICE QUESTIONS (MCQs)\n`;
    text += `------------------------------------------------------------------------\n\n`;

    data.mcqs?.forEach((m, idx) => {
      text += `Q${idx + 1}. [${m.subject_tag || "General Studies"}] (${m.difficulty || "Medium"})\n`;
      text += `${m.question}\n\n`;
      m.options.forEach((opt) => {
        text += `   ${opt}\n`;
      });
      text += `\n>> Correct Answer: Option ${String.fromCharCode(65 + m.correct_index)}\n`;
      text += `>> Evidence Sentences: ${m.evidence_indices?.map((i) => `[S${i}]`).join(", ") || "[None]"}\n`;
      text += `>> Explanation: ${m.explanation}\n\n`;
      text += `------------------------------------------------------------------------\n\n`;
    });

    text += `------------------------------------------------------------------------\n`;
    text += `PART II: MAINS DESCRIPTIVE QUESTIONS & MODEL ANSWERS\n`;
    text += `------------------------------------------------------------------------\n\n`;

    data.descriptive?.forEach((d, idx) => {
      text += `Question ${idx + 1} (${d.marks || 10} Marks | ${d.word_limit || 150} Words) [${d.syllabus_paper || "GS Paper"}]:\n`;
      text += `"${d.question}"\n\n`;
      text += `STRUCTURED MODEL ANSWER:\n`;
      text += `1. Introduction:\n   ${d.model_answer.introduction}\n\n`;
      text += `2. Key Dimensions:\n`;
      d.model_answer.key_dimensions?.forEach((k) => {
        text += `   • ${k}\n`;
      });
      text += `\n3. Policy & Governance Links:\n   ${d.model_answer.policy_implications}\n\n`;
      text += `4. Administrative Way Forward:\n   ${d.model_answer.way_forward}\n\n`;
      text += `>> Evidence Sentences: ${d.evidence_indices?.map((i) => `[S${i}]`).join(", ") || "[None]"}\n\n`;
      text += `------------------------------------------------------------------------\n\n`;
    });

    return text;
  };

  const handleDownloadSheet = () => {
    const fullText = generateFullStudySheet();
    const blob = new Blob([fullText], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `UPSC_KPSC_Exam_Prep_Article_${articleId}.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleCopyAll = () => {
    const fullText = generateFullStudySheet();
    navigator.clipboard.writeText(fullText);
    setCopiedAll(true);
    setTimeout(() => setCopiedAll(false), 2500);
  };

  const handlePrintPdf = () => {
    if (!data) return;
    const printWindow = window.open("", "_blank");
    if (!printWindow) {
      alert("Please allow popups to open the printable exam sheet.");
      return;
    }
    const content = `
      <!DOCTYPE html>
      <html>
      <head>
        <title>UPSC & KPSC Exam Sheet - Article ${articleId}</title>
        <style>
          body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; line-height: 1.5; color: #1e293b; padding: 40px; max-width: 850px; margin: 0 auto; }
          h1 { font-size: 20px; font-weight: 800; color: #0f172a; margin-bottom: 4px; border-bottom: 2px solid #4f46e5; padding-bottom: 8px; }
          .meta { font-size: 12px; color: #64748b; margin-bottom: 20px; }
          .badge { display: inline-block; background: #e0e7ff; color: #3730a3; font-size: 11px; font-weight: bold; padding: 2px 8px; border-radius: 4px; margin-right: 6px; }
          .section-title { font-size: 14px; font-weight: bold; text-transform: uppercase; background: #f1f5f9; padding: 6px 10px; margin: 25px 0 15px 0; border-left: 4px solid #4f46e5; }
          .q-card { margin-bottom: 20px; padding: 12px; border: 1px solid #e2e8f0; border-radius: 8px; page-break-inside: avoid; }
          .q-text { font-size: 13px; font-weight: 600; margin-bottom: 8px; white-space: pre-line; }
          .options { font-size: 12px; margin-left: 10px; }
          .opt-item { margin-bottom: 4px; }
          .ans-box { margin-top: 10px; padding: 8px; background: #f8fafc; border-left: 3px solid #10b981; font-size: 12px; }
          .mains-q { font-size: 13px; font-weight: bold; margin-bottom: 8px; }
          .mains-ans { font-size: 12px; margin-top: 6px; line-height: 1.6; }
          @media print { body { padding: 20px; } .no-print { display: none; } }
        </style>
      </head>
      <body>
        <div class="no-print" style="margin-bottom: 20px; display: flex; justify-content: space-between;">
          <button onclick="window.print()" style="background:#4f46e5;color:white;border:none;padding:8px 16px;border-radius:6px;cursor:pointer;font-weight:bold;">🖨️ Print / Save as PDF</button>
          <button onclick="window.close()" style="background:#e2e8f0;color:#334155;border:none;padding:8px 16px;border-radius:6px;cursor:pointer;">Close Window</button>
        </div>
        <h1>UPSC & KPSC Civil Services Exam Practice Sheet</h1>
        <div class="meta">
          <div><strong>Source:</strong> Verified Regional Journalism (KannadaNewsAI) • <strong>Date:</strong> ${new Date().toLocaleDateString()}</div>
          <div style="margin-top:6px;"><strong>Syllabus Mapping:</strong> ${data.syllabus_focus?.map((t: string) => `<span class="badge">${t}</span>`).join(" ")}</div>
          <div style="margin-top:8px;font-style:italic;">${data.exam_relevance_summary}</div>
        </div>

        <div class="section-title">Part I: Prelims Multiple Choice Questions (MCQs)</div>
        ${data.mcqs?.map((m: any, idx: number) => `
          <div class="q-card">
            <div style="font-size:11px;color:#6366f1;font-weight:bold;margin-bottom:4px;">QUESTION ${idx + 1} • ${m.subject_tag || 'General Studies'} (${m.difficulty || 'Medium'})</div>
            <div class="q-text">${m.question}</div>
            <div class="options">
              ${m.options?.map((opt: string) => `<div class="opt-item">[ &nbsp; ] ${opt}</div>`).join("")}
            </div>
            <div class="ans-box">
              <strong>Correct Answer: Option ${String.fromCharCode(65 + m.correct_index)}</strong> • <em>Evidence Sentences: ${m.evidence_indices?.map((i: number) => `[S${i}]`).join(", ") || "[None]"}</em>
              <div style="margin-top:4px;">${m.explanation}</div>
            </div>
          </div>
        `).join("")}

        <div class="section-title">Part II: Mains Analytical Questions & Model Answers</div>
        ${data.descriptive?.map((d: any, idx: number) => `
          <div class="q-card">
            <div style="font-size:11px;color:#6366f1;font-weight:bold;margin-bottom:4px;">QUESTION ${idx + 1} (${d.marks || 10} Marks | ${d.word_limit || 150} Words) • ${d.syllabus_paper}</div>
            <div class="mains-q">"${d.question}"</div>
            <div class="mains-ans">
              <div><strong>1. Context & Introduction:</strong> ${d.model_answer.introduction}</div>
              <div style="margin-top:4px;"><strong>2. Core Dimensions:</strong>
                <ul>${d.model_answer.key_dimensions?.map((k: string) => `<li>${k}</li>`).join("")}</ul>
              </div>
              <div style="margin-top:4px;"><strong>3. Policy Framework:</strong> ${d.model_answer.policy_implications}</div>
              <div style="margin-top:4px;"><strong>4. Way Forward:</strong> ${d.model_answer.way_forward}</div>
            </div>
          </div>
        `).join("")}
      </body>
      </html>
    `;
    printWindow.document.write(content);
    printWindow.document.close();
    setTimeout(() => {
      printWindow.print();
    }, 400);
  };

  // Score calculations
  const totalMcqs = data?.mcqs?.length || 0;
  const answeredCount = Object.keys(selectedAnswers).length;
  const correctCount = Object.entries(selectedAnswers).filter(
    ([qIdx, optIdx]) => data?.mcqs[parseInt(qIdx)]?.correct_index === optIdx
  ).length;

  if (loading) {
    return (
      <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700/80 rounded-2xl p-6 shadow-xs animate-pulse">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-indigo-100 dark:bg-indigo-950/60" />
          <div className="space-y-1.5 flex-1">
            <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-1/3" />
            <div className="h-3 bg-slate-100 dark:bg-slate-800 rounded w-1/2" />
          </div>
        </div>
        <div className="h-24 bg-slate-50 dark:bg-slate-800/40 rounded-xl mb-4" />
        <div className="space-y-3">
          <div className="h-20 bg-slate-100 dark:bg-slate-700/40 rounded-xl" />
          <div className="h-20 bg-slate-100 dark:bg-slate-700/40 rounded-xl" />
        </div>
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
          className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-xs transition cursor-pointer"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Generate Questions
        </button>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-slate-800/90 border border-slate-200 dark:border-slate-700/80 rounded-2xl p-5 sm:p-6 shadow-xs space-y-5">
      {/* Top Header Bar */}
      <div className="flex flex-wrap items-start justify-between gap-3 pb-3 border-b border-slate-100 dark:border-slate-700/60">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-indigo-500 to-indigo-700 text-white flex items-center justify-center shadow-xs">
            <GraduationCap className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm sm:text-base font-extrabold text-slate-900 dark:text-slate-100 tracking-tight">
                UPSC & KPSC Civil Services Study Hub
              </h3>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-indigo-50 dark:bg-indigo-950/80 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800 flex items-center gap-1">
                <Sparkles className="w-2.5 h-2.5" />
                Comprehensive Bank
              </span>
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
              Grounded, syllabus-mapped questions extracted from verified regional Kannada reporting
            </p>
          </div>
        </div>

        {/* Global Action Toolbar */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <button
            type="button"
            onClick={handleCopyAll}
            title="Copy full exam question paper & model answers"
            className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 text-xs font-semibold transition cursor-pointer"
          >
            {copiedAll ? (
              <>
                <CheckCheck className="w-3.5 h-3.5 text-emerald-600" />
                <span className="text-emerald-600">Copied All</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5 text-slate-500" />
                <span>Copy Bank</span>
              </>
            )}
          </button>

          <button
            type="button"
            onClick={handleDownloadSheet}
            title="Download full practice test paper as text document"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-xs transition cursor-pointer"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download (.txt)</span>
          </button>

          <button
            type="button"
            onClick={handlePrintPdf}
            title="Open printable exam sheet (Save as PDF)"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-xs transition cursor-pointer"
          >
            <Printer className="w-3.5 h-3.5" />
            <span>Print / PDF</span>
          </button>

          <button
            type="button"
            onClick={() => fetchExamPrep(true)}
            disabled={refreshing}
            title="Re-run AI to extract more diverse questions"
            className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 text-xs font-semibold transition cursor-pointer disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin text-indigo-600" : ""}`} />
            <span>{refreshing ? "Generating..." : "Regenerate"}</span>
          </button>
        </div>
      </div>

      {/* Exam Relevance Callout */}
      {data.exam_relevance_summary && (
        <div className="bg-gradient-to-r from-indigo-50/70 to-blue-50/70 dark:from-indigo-950/40 dark:to-blue-950/30 border border-indigo-100 dark:border-indigo-900/60 rounded-xl p-3.5 text-xs text-indigo-950 dark:text-indigo-200 space-y-1.5">
          <div className="flex items-center gap-1.5 font-bold uppercase tracking-wider text-[10px] text-indigo-700 dark:text-indigo-400">
            <Award className="w-3.5 h-3.5" />
            <span>Civil Services Exam Utility & Syllabus Alignment</span>
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

      {/* High-Visibility Download Banner */}
      <div id="download-exam-banner" className="bg-gradient-to-r from-emerald-50 to-teal-50 dark:from-emerald-950/40 dark:to-teal-950/40 border-2 border-emerald-400 dark:border-emerald-600 rounded-xl p-4 flex flex-col sm:flex-row items-center justify-between gap-3 shadow-xs">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-600 text-white flex items-center justify-center shrink-0 shadow-sm">
            <Download className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-xs sm:text-sm font-extrabold text-emerald-950 dark:text-emerald-100 flex items-center gap-2">
              <span>Download & Print Practice Test Paper</span>
              <span className="text-[10px] bg-emerald-200 dark:bg-emerald-800 text-emerald-900 dark:text-emerald-100 px-1.5 py-0.2 rounded font-bold">PDF / TXT</span>
            </h4>
            <p className="text-[11px] text-emerald-800 dark:text-emerald-300 mt-0.5">
              Includes all {data.mcqs?.length || 5} Prelims MCQs, Mains questions with model answers & sentence citations.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0 w-full sm:w-auto">
          <button
            type="button"
            onClick={handleDownloadSheet}
            className="flex-1 sm:flex-initial inline-flex items-center justify-center gap-1.5 px-3.5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-sm transition cursor-pointer"
          >
            <Download className="w-4 h-4" />
            <span>Download (.txt)</span>
          </button>

          <button
            type="button"
            onClick={handlePrintPdf}
            className="flex-1 sm:flex-initial inline-flex items-center justify-center gap-1.5 px-3.5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs shadow-sm transition cursor-pointer"
          >
            <Printer className="w-4 h-4" />
            <span>Print / Save PDF</span>
          </button>
        </div>
      </div>

      {/* Mode Switcher Tabs */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 dark:border-slate-700/60 pb-2">
        <div className="flex items-center gap-1.5 sm:gap-2">
          <button
            type="button"
            onClick={() => setActiveTab("prelims")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition cursor-pointer ${
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
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition cursor-pointer ${
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

          <button
            type="button"
            onClick={() => setActiveTab("saved")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition cursor-pointer ${
              activeTab === "saved"
                ? "bg-amber-600 text-white shadow-xs"
                : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700/50"
            }`}
          >
            <BookmarkCheck className="w-3.5 h-3.5" />
            <span>Saved MCQs</span>
            <span className="text-[10px] px-1.5 py-0.2 bg-white/20 rounded-full font-mono">
              {savedMcqs.length}
            </span>
          </button>
        </div>

        {/* Live Quiz Score Tracker */}
        {activeTab === "prelims" && answeredCount > 0 && (
          <div className="text-[11px] font-semibold text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-700/60 px-2.5 py-1 rounded-full flex items-center gap-1.5">
            <span>Score:</span>
            <span className="text-emerald-600 dark:text-emerald-400 font-bold">{correctCount}</span>
            <span>/</span>
            <span>{answeredCount}</span>
            <span className="text-slate-400">({Math.round((correctCount / answeredCount) * 100)}%)</span>
          </div>
        )}
      </div>

      {/* Tab 1: Prelims MCQs */}
      {activeTab === "prelims" && (
        <div className="space-y-5">
          {data.mcqs && data.mcqs.length > 0 ? (
            data.mcqs.map((mcq, qIdx) => {
              const selectedOpt = selectedAnswers[qIdx];
              const isAnswered = selectedOpt !== undefined;
              const isCorrect = isAnswered && selectedOpt === mcq.correct_index;
              const saved = isMcqSaved(mcq);

              return (
                <div
                  key={qIdx}
                  className="bg-slate-50/80 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700/70 rounded-xl p-4 transition-all"
                >
                  {/* Meta Bar */}
                  <div className="flex flex-wrap items-center justify-between gap-2 mb-2.5">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-700 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-950/60 px-2 py-0.5 rounded border border-indigo-100 dark:border-indigo-900/50">
                        MCQ {qIdx + 1} • {mcq.subject_tag || "General Studies"}
                      </span>
                      <span className="text-[10px] font-medium text-slate-500 dark:text-slate-400">
                        Difficulty: <strong className="font-semibold text-slate-700 dark:text-slate-200">{mcq.difficulty || "Medium"}</strong>
                      </span>
                    </div>

                    {/* Save / Bookmark Button */}
                    <button
                      type="button"
                      onClick={() => toggleSaveMcq(mcq)}
                      title={saved ? "Remove from saved questions" : "Save question to revision bank"}
                      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold transition cursor-pointer border ${
                        saved
                          ? "bg-amber-50 text-amber-800 border-amber-300 dark:bg-amber-950/60 dark:text-amber-300"
                          : "bg-white text-slate-600 border-slate-200 hover:border-amber-300 hover:text-amber-700 dark:bg-slate-800 dark:text-slate-300"
                      }`}
                    >
                      {saved ? (
                        <>
                          <BookmarkCheck className="w-3.5 h-3.5 text-amber-600 fill-amber-500" />
                          <span>Saved ⭐</span>
                        </>
                      ) : (
                        <>
                          <Bookmark className="w-3.5 h-3.5 text-slate-400" />
                          <span>Save MCQ</span>
                        </>
                      )}
                    </button>
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

      {/* Tab 3: Saved MCQs Bank */}
      {activeTab === "saved" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100 dark:border-slate-700/60">
            <div>
              <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200">
                Personal Saved Question Bank ({savedMcqs.length})
              </h4>
              <p className="text-[10px] text-slate-400">
                Bookmarked MCQs stored locally for revision and mock practice
              </p>
            </div>

            {savedMcqs.length > 0 && (
              <button
                type="button"
                onClick={clearAllSaved}
                className="inline-flex items-center gap-1 text-[11px] text-rose-600 hover:text-rose-700 font-semibold cursor-pointer"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>Clear All</span>
              </button>
            )}
          </div>

          {savedMcqs.length > 0 ? (
            savedMcqs.map((mcq, sIdx) => (
              <div
                key={sIdx}
                className="bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-700 rounded-xl p-4 text-xs space-y-2.5"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="text-[10px] font-bold uppercase text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/60 px-2 py-0.5 rounded border border-amber-200 dark:border-amber-900/50">
                    Saved #{sIdx + 1} • {mcq.subject_tag || "General Studies"}
                  </span>

                  <button
                    type="button"
                    onClick={() => toggleSaveMcq(mcq)}
                    className="text-rose-500 hover:text-rose-700 text-[11px] font-semibold cursor-pointer inline-flex items-center gap-1"
                  >
                    <Trash2 className="w-3 h-3" />
                    <span>Remove</span>
                  </button>
                </div>

                <div className="font-semibold text-slate-900 dark:text-slate-100 whitespace-pre-line leading-relaxed">
                  {mcq.question}
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5 pt-1">
                  {mcq.options.map((opt, optIdx) => (
                    <div
                      key={optIdx}
                      className={`p-2 rounded border text-[11px] ${
                        optIdx === mcq.correct_index
                          ? "bg-emerald-50 dark:bg-emerald-950/60 border-emerald-400 text-emerald-900 dark:text-emerald-200 font-bold"
                          : "bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400"
                      }`}
                    >
                      {opt} {optIdx === mcq.correct_index && "✓ (Correct)"}
                    </div>
                  ))}
                </div>

                <div className="p-2.5 rounded bg-white dark:bg-slate-800 border border-slate-200/80 dark:border-slate-700/80 text-[11px] space-y-1 text-slate-600 dark:text-slate-300">
                  <div className="font-bold text-slate-800 dark:text-slate-200">
                    Explanation:
                  </div>
                  <p className="leading-relaxed">{mcq.explanation}</p>
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-8 text-slate-400 space-y-2">
              <Bookmark className="w-8 h-8 mx-auto opacity-50" />
              <p className="text-xs">No questions saved yet.</p>
              <p className="text-[11px] text-slate-500">
                Click <strong>"Save MCQ"</strong> on any question in the Prelims tab to add it to your personal revision bank.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
