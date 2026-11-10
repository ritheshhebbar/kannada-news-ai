import Link from "next/link";
import { ArticleListItem } from "@/lib/api";
import { Clock, AlertCircle, CheckCircle, ExternalLink } from "lucide-react";

interface ArticleCardProps {
  article: ArticleListItem;
  showKannadaFirst?: boolean;
}

export default function ArticleCard({ article, showKannadaFirst = false }: ArticleCardProps) {
  const isReady = article.status === "ready";
  const needsReview = article.status === "needs_review";

  return (
    <Link
      href={`/article/${article.id}`}
      className="group block bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700/70 p-5 hover:border-indigo-400 dark:hover:border-indigo-500 hover:shadow-md transition-all duration-200"
    >
      {/* Top Meta: Source, Date, Category, Status */}
      <div className="flex items-center justify-between text-xs text-slate-500 mb-2.5">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-slate-700 dark:text-slate-300">
            {article.source_name || "Direct Input"}
          </span>
          <span>•</span>
          <span className="inline-block px-2 py-0.5 rounded-full text-[11px] font-medium bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 uppercase">
            {article.section_label || "General"}
          </span>
        </div>

        <div className="flex items-center gap-2">
          {needsReview && (
            <span className="inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-full bg-amber-50 dark:bg-amber-950/50 text-amber-600 border border-amber-200 dark:border-amber-800">
              <AlertCircle className="w-3 h-3" />
              Needs Review
            </span>
          )}
          {isReady && !needsReview && (
            <span className="inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 border border-emerald-200 dark:border-emerald-800">
              <CheckCircle className="w-3 h-3" />
              Verified
            </span>
          )}
        </div>
      </div>

      {/* Main Headline */}
      {showKannadaFirst ? (
        <>
          <h3 className="font-kannada text-lg font-bold text-slate-900 dark:text-slate-100 leading-kannada group-hover:text-indigo-600 transition mb-1.5">
            {article.title_kn || "ಶೀರ್ಷಿಕೆ ಇಲ್ಲ"}
          </h3>
          {article.title_en && (
            <p className="text-sm font-medium text-slate-600 dark:text-slate-300 mb-2">
              {article.title_en}
            </p>
          )}
        </>
      ) : (
        <>
          <h3 className="text-base sm:text-lg font-bold text-slate-900 dark:text-slate-100 group-hover:text-indigo-600 transition mb-1.5">
            {article.title_en || article.title_kn || "Untitled News Story"}
          </h3>
          {article.title_kn && (
            <p className="font-kannada text-xs text-slate-500 leading-kannada line-clamp-1 mb-2">
              {article.title_kn}
            </p>
          )}
        </>
      )}

      {/* Two-line Summary */}
      {article.two_line_summary && (
        <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 line-clamp-2 mb-3">
          {article.two_line_summary}
        </p>
      )}

      {/* Footer Info */}
      <div className="flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-slate-100 dark:border-slate-700/50">
        <span className="flex items-center gap-1">
          <Clock className="w-3.5 h-3.5" />
          {article.published_at ? new Date(article.published_at).toLocaleDateString() : "Today"}
        </span>
        <span className="text-indigo-600 dark:text-indigo-400 font-medium group-hover:translate-x-0.5 transition inline-flex items-center gap-0.5">
          Read side-by-side &rarr;
        </span>
      </div>
    </Link>
  );
}
