"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { api, ArticleListItem, getSessionId } from "@/lib/api";
import ArticleCard from "@/components/ArticleCard";
import { Search, Clock, ArrowRight } from "lucide-react";

function SearchContent() {
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get("q") || "";

  const [query, setQuery] = useState(initialQuery);
  const [results, setResults] = useState<ArticleListItem[]>([]);
  const [recentSearches, setRecentSearches] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const performSearch = async (searchStr: string) => {
    if (!searchStr.trim()) return;
    setLoading(true);
    setHasSearched(true);
    try {
      const sid = getSessionId();
      const res = await api.search(searchStr.trim(), sid);
      setResults(res.items || []);
      // Refresh recent searches
      api.getSearchHistory(sid).then(setRecentSearches).catch(() => {});
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const sid = getSessionId();
    api.getSearchHistory(sid).then(setRecentSearches).catch(() => {});
    if (initialQuery) {
      performSearch(initialQuery);
    }
  }, [initialQuery]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    performSearch(query);
  };

  return (
    <div className="max-w-4xl mx-auto py-4">
      {/* Search Input Box */}
      <form onSubmit={handleSubmit} className="mb-6">
        <div className="relative flex items-center">
          <Search className="w-5 h-5 text-slate-400 absolute left-4" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search keywords in English or ಕನ್ನಡ (e.g. ಬೆಂಗಳೂರು, ಇಸ್ರೋ, rail)..."
            className="w-full pl-12 pr-28 py-3 bg-white border border-slate-200 rounded-2xl shadow-xs focus:ring-2 focus:ring-indigo-500 focus:outline-none text-sm text-slate-800"
          />
          <button
            type="submit"
            className="absolute right-2 px-4 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-xs rounded-xl transition cursor-pointer"
          >
            Search
          </button>
        </div>
      </form>

      {/* Recent Searches Pills */}
      {recentSearches.length > 0 && (
        <div className="flex items-center gap-2 mb-6 overflow-x-auto pb-1 text-xs text-slate-500">
          <span className="flex items-center gap-1 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
            <Clock className="w-3 h-3" /> Recent:
          </span>
          {recentSearches.slice(0, 5).map((s) => (
            <button
              key={s.id}
              type="button"
              onClick={() => {
                setQuery(s.query);
                performSearch(s.query);
              }}
              className="px-2.5 py-1 bg-white hover:bg-slate-100 border border-slate-200 rounded-full text-slate-700 transition cursor-pointer"
            >
              {s.query}
            </button>
          ))}
        </div>
      )}

      {/* Search Results */}
      <div>
        {loading ? (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-32 bg-slate-100 rounded-xl animate-pulse" />
            ))}
          </div>
        ) : hasSearched && results.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-xl border border-slate-200">
            <p className="text-slate-600 font-medium">No matching articles found for "{query}".</p>
            <p className="text-xs text-slate-400 mt-1">Try another term or search in Kannada script.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {results.map((art) => (
              <ArticleCard key={art.id} article={art} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<div className="py-12 text-center text-slate-400">Loading search...</div>}>
      <SearchContent />
    </Suspense>
  );
}
