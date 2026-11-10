"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api, ArticleDetail, getSessionId } from "@/lib/api";
import SideBySide from "@/components/SideBySide";
import SummaryPanel from "@/components/SummaryPanel";
import VerificationPanel from "@/components/VerificationPanel";
import EntityChips from "@/components/EntityChips";
import { Bookmark, BookmarkCheck, ExternalLink, MessageSquare, ArrowLeft, RefreshCw } from "lucide-react";

export default function ArticleDetailPage() {
  const params = useParams();
  const articleId = parseInt(params.id as string);

  const [article, setArticle] = useState<ArticleDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [highlightedSentIdx, setHighlightedSentIdx] = useState<number | null>(null);
  const [isBookmarked, setIsBookmarked] = useState(false);
  const [feedbackOpen, setFeedbackOpen] = useState(false);
  const [feedbackKind, setFeedbackKind] = useState("translation_error");
  const [feedbackComment, setFeedbackComment] = useState("");
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);

  useEffect(() => {
    if (!articleId) return;

    const sid = getSessionId();
    api.getArticle(articleId)
      .then((data) => {
        setArticle(data);
        // Record in reading history
        api.recordReading(sid, articleId).catch(() => {});
      })
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));

    // Check if bookmarked
    api.getBookmarks(sid)
      .then((bm) => {
        setIsBookmarked(bm.some((b) => b.id === articleId));
      })
      .catch(() => {});
  }, [articleId]);

  const toggleBookmark = async () => {
    const sid = getSessionId();
    try {
      if (isBookmarked) {
        await api.removeBookmark(sid, articleId);
        setIsBookmarked(false);
      } else {
        await api.addBookmark(sid, articleId);
        setIsBookmarked(true);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleSendFeedback = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.submitFeedback({
        article_id: articleId,
        kind: feedbackKind,
        comment: feedbackComment,
      });
      setFeedbackSubmitted(true);
      setTimeout(() => {
        setFeedbackOpen(false);
        setFeedbackSubmitted(false);
        setFeedbackComment("");
      }, 1500);
    } catch (e) {
      console.error(e);
    }
  };

  if (loading) {
    return (
      <div className="py-12 space-y-4 max-w-4xl mx-auto">
        <div className="h-8 bg-slate-200 rounded w-3/4 animate-pulse" />
        <div className="h-6 bg-slate-100 rounded w-1/2 animate-pulse" />
        <div className="h-64 bg-slate-100 rounded-xl animate-pulse" />
      </div>
    );
  }

  if (!article) {
    return (
      <div className="py-16 text-center">
        <h2 className="text-xl font-bold text-slate-800">Article not found</h2>
        <Link href="/" className="text-sm text-indigo-600 mt-2 inline-block">
          &larr; Return to Dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="pb-16">
      {/* Back button & Action Bar */}
      <div className="flex items-center justify-between gap-4 mb-5">
        <Link
          href="/"
          className="text-xs font-semibold text-slate-500 hover:text-indigo-600 inline-flex items-center gap-1"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to News
        </Link>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={toggleBookmark}
            className={`p-2 rounded-lg border text-xs font-medium flex items-center gap-1.5 transition cursor-pointer ${
              isBookmarked
                ? "bg-indigo-50 border-indigo-200 text-indigo-600"
                : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
            }`}
          >
            {isBookmarked ? <BookmarkCheck className="w-4 h-4" /> : <Bookmark className="w-4 h-4" />}
            <span>{isBookmarked ? "Bookmarked" : "Bookmark"}</span>
          </button>

          <button
            type="button"
            onClick={() => setFeedbackOpen(true)}
            className="p-2 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-600 text-xs font-medium flex items-center gap-1.5 transition cursor-pointer"
          >
            <MessageSquare className="w-4 h-4 text-slate-400" />
            <span>Report Error</span>
          </button>
        </div>
      </div>

      {/* Article Header */}
      <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700/80 rounded-2xl p-6 sm:p-8 mb-6 shadow-xs">
        {/* Meta Bar */}
        <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500 mb-3">
          <span className="font-bold text-slate-800 dark:text-slate-200">
            {article.source_name || "Direct News Source"}
          </span>
          <span>•</span>
          <span className="px-2.5 py-0.5 rounded-full bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 font-medium uppercase text-[10px]">
            {article.section_label || "Karnataka"}
          </span>
          <span>•</span>
          <span>{article.published_at ? new Date(article.published_at).toLocaleString() : "Recent"}</span>

          {article.url && (
            <>
              <span>•</span>
              <a
                href={article.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-indigo-600 dark:text-indigo-400 hover:underline inline-flex items-center gap-1 font-medium"
              >
                Read Original <ExternalLink className="w-3 h-3" />
              </a>
            </>
          )}
        </div>

        {/* English Translated Headline */}
        <h1 className="text-xl sm:text-3xl font-extrabold text-slate-900 dark:text-slate-100 tracking-tight leading-snug mb-2">
          {article.active_translation?.title_en || article.title_en || article.title_kn}
        </h1>

        {/* Original Kannada Headline */}
        <h2 className="font-kannada text-base sm:text-xl font-semibold text-slate-600 dark:text-slate-400 leading-kannada mb-4">
          {article.title_kn}
        </h2>

        {/* Named Entity Chips */}
        <EntityChips entities={article.entities} />
      </div>

      {/* Two Column Layout: Summary & Verification on Left, Side-by-Side Reader on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Summary & Verification (4 cols) */}
        <div className="lg:col-span-4 space-y-4">
          <SummaryPanel
            summary={article.active_summary}
            onSelectEvidence={(sIdx) => setHighlightedSentIdx(sIdx)}
          />

          <VerificationPanel
            verification={article.active_summary?.verification}
            method={article.active_summary?.method}
            flagsCount={article.flags?.length || 0}
          />
        </div>

        {/* Right Column: Sentence-Aligned Reader (8 cols) */}
        <div className="lg:col-span-8">
          <SideBySide
            sentences={article.sentences}
            highlightedIdx={highlightedSentIdx}
            onSentenceClick={(idx) => setHighlightedSentIdx(idx)}
          />
        </div>
      </div>

      {/* Report Problem / Human Feedback Modal */}
      {feedbackOpen && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200">
            <h3 className="text-base font-bold text-slate-900 mb-1">Report Translation or Fact Issue</h3>
            <p className="text-xs text-slate-500 mb-4">
              Your feedback is recorded to evaluate translation adequacy and train verification filters.
            </p>

            {feedbackSubmitted ? (
              <div className="p-4 bg-emerald-50 text-emerald-800 rounded-lg text-xs font-semibold text-center">
                Thank you! Your feedback has been recorded for the research evaluation report.
              </div>
            ) : (
              <form onSubmit={handleSendFeedback} className="space-y-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Issue Category</label>
                  <select
                    value={feedbackKind}
                    onChange={(e) => setFeedbackKind(e.target.value)}
                    className="w-full text-xs p-2 border border-slate-200 rounded-lg"
                  >
                    <option value="translation_error">Translation Error / Mistranslation</option>
                    <option value="hallucination">Factual Hallucination in Summary</option>
                    <option value="bad_entity">Entity / Name Mismatch</option>
                    <option value="number_mismatch">Number / Date Inaccuracy</option>
                    <option value="other">Other Feedback</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Comment / Details</label>
                  <textarea
                    rows={3}
                    value={feedbackComment}
                    onChange={(e) => setFeedbackComment(e.target.value)}
                    placeholder="Describe what was mistranslated or unsupported..."
                    className="w-full text-xs p-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                    required
                  />
                </div>

                <div className="flex items-center justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setFeedbackOpen(false)}
                    className="px-3 py-1.5 text-xs text-slate-600 hover:text-slate-800"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-1.5 text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg shadow-xs"
                  >
                    Submit Feedback
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
