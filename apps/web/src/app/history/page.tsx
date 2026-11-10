"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, ArticleListItem, getSessionId } from "@/lib/api";
import ArticleCard from "@/components/ArticleCard";
import { Bookmark, Clock, Trash2 } from "lucide-react";

export default function HistoryPage() {
  const [tab, setTab] = useState<"bookmarks" | "reading">("bookmarks");
  const [bookmarks, setBookmarks] = useState<ArticleListItem[]>([]);
  const [readingHistory, setReadingHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = () => {
    const sid = getSessionId();
    setLoading(true);
    Promise.all([
      api.getBookmarks(sid).catch(() => []),
      api.getReadingHistory(sid).catch(() => []),
    ])
      .then(([bm, rh]) => {
        setBookmarks(bm);
        setReadingHistory(rh);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleClear = async () => {
    const sid = getSessionId();
    if (confirm("Clear all reading and search history?")) {
      await api.clearHistory(sid);
      loadData();
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-4">
      <div className="flex items-center justify-between gap-4 mb-6 pb-3 border-b border-slate-200">
        <div className="flex items-center gap-2 bg-slate-100 p-1 rounded-xl text-xs font-semibold">
          <button
            type="button"
            onClick={() => setTab("bookmarks")}
            className={`px-4 py-2 rounded-lg transition cursor-pointer flex items-center gap-1.5 ${
              tab === "bookmarks" ? "bg-white text-indigo-600 shadow-xs font-bold" : "text-slate-500"
            }`}
          >
            <Bookmark className="w-3.5 h-3.5" /> Bookmarks ({bookmarks.length})
          </button>
          <button
            type="button"
            onClick={() => setTab("reading")}
            className={`px-4 py-2 rounded-lg transition cursor-pointer flex items-center gap-1.5 ${
              tab === "reading" ? "bg-white text-indigo-600 shadow-xs font-bold" : "text-slate-500"
            }`}
          >
            <Clock className="w-3.5 h-3.5" /> Reading History ({readingHistory.length})
          </button>
        </div>

        {readingHistory.length > 0 && tab === "reading" && (
          <button
            type="button"
            onClick={handleClear}
            className="text-xs text-red-600 hover:text-red-700 font-medium flex items-center gap-1 cursor-pointer"
          >
            <Trash2 className="w-3.5 h-3.5" /> Clear History
          </button>
        )}
      </div>

      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-24 bg-slate-100 rounded-xl animate-pulse" />
          ))}
        </div>
      ) : tab === "bookmarks" ? (
        bookmarks.length === 0 ? (
          <div className="text-center py-16 bg-white rounded-xl border border-slate-200">
            <Bookmark className="w-8 h-8 text-slate-300 mx-auto mb-2" />
            <p className="text-slate-600 font-medium">No bookmarked articles yet.</p>
            <p className="text-xs text-slate-400 mt-1">Bookmark articles to read them later.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {bookmarks.map((art) => (
              <ArticleCard key={art.id} article={art} />
            ))}
          </div>
        )
      ) : readingHistory.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-xl border border-slate-200">
          <Clock className="w-8 h-8 text-slate-300 mx-auto mb-2" />
          <p className="text-slate-600 font-medium">No reading history yet.</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 divide-y divide-slate-100">
          {readingHistory.map((r) => (
            <Link
              key={r.id}
              href={`/article/${r.article_id}`}
              className="p-4 flex items-center justify-between gap-4 hover:bg-slate-50 transition"
            >
              <div>
                <h4 className="text-sm font-semibold text-slate-900 mb-0.5">
                  {r.article_title_en || r.article_title_kn}
                </h4>
                {r.article_title_kn && (
                  <p className="font-kannada text-xs text-slate-400 leading-kannada">
                    {r.article_title_kn}
                  </p>
                )}
              </div>
              <span className="text-xs text-slate-400 whitespace-nowrap">
                {new Date(r.opened_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
