"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, ArticleListItem, Category, DashboardStats, getSessionId } from "@/lib/api";
import StatStrip from "@/components/StatStrip";
import ArticleCard from "@/components/ArticleCard";
import { Sparkles, ArrowRight, Newspaper, Filter, RefreshCw } from "lucide-react";

export default function HomePage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [articles, setArticles] = useState<ArticleListItem[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [statsData, catsData, articlesData] = await Promise.all([
        api.getStats().catch(() => null),
        api.getCategories().catch(() => []),
        api.getArticles({ category: selectedCategory || undefined, page_size: 12 }),
      ]);
      setStats(statsData);
      setCategories(catsData);
      setArticles(articlesData.items || []);
    } catch (e) {
      console.error("Failed to load dashboard data:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [selectedCategory]);

  return (
    <div>
      {/* Hero Banner */}
      <div className="bg-linear-to-r from-indigo-700 via-indigo-600 to-indigo-800 rounded-2xl p-6 sm:p-8 text-white mb-8 shadow-sm">
        <div className="max-w-3xl">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-white/20 backdrop-blur mb-3">
            <Sparkles className="w-3.5 h-3.5" />
            Verified Translate-Then-Summarize Pipeline
          </span>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight mb-2">
            AI-Powered News Translation from Kannada to English
          </h1>
          <p className="text-indigo-100 text-sm sm:text-base leading-relaxed mb-5">
            Read contemporary Kannada news with sentence-aligned English translations and grounded summaries verified against source evidence.
          </p>
          <div className="flex flex-wrap gap-3">
            <Link
              href="/submit"
              className="bg-white text-indigo-700 hover:bg-indigo-50 font-semibold px-4 py-2 rounded-lg text-sm shadow-xs transition inline-flex items-center gap-1.5"
            >
              Submit an Article &rarr;
            </Link>
            <Link
              href="/kannada"
              className="bg-indigo-500/40 hover:bg-indigo-500/60 text-white font-medium px-4 py-2 rounded-lg text-sm transition"
            >
              Browse Kannada Feed
            </Link>
          </div>
        </div>
      </div>

      {/* Operational Stats Strip */}
      <StatStrip stats={stats} />

      {/* Categories Filter Strip */}
      <div className="flex items-center justify-between gap-4 mb-6 overflow-x-auto pb-2">
        <div className="flex items-center gap-1.5">
          <button
            type="button"
            onClick={() => setSelectedCategory(null)}
            className={`px-3 py-1.5 rounded-full text-xs font-medium transition cursor-pointer ${
              selectedCategory === null
                ? "bg-indigo-600 text-white shadow-xs"
                : "bg-white text-slate-600 hover:bg-slate-100 border border-slate-200"
            }`}
          >
            All Stories
          </button>
          {categories.map((cat) => (
            <button
              key={cat.id}
              type="button"
              onClick={() => setSelectedCategory(cat.slug)}
              className={`px-3 py-1.5 rounded-full text-xs font-medium transition cursor-pointer whitespace-nowrap ${
                selectedCategory === cat.slug
                  ? "bg-indigo-600 text-white shadow-xs"
                  : "bg-white text-slate-600 hover:bg-slate-100 border border-slate-200"
              }`}
            >
              {cat.name_en}
            </button>
          ))}
        </div>

        <button
          type="button"
          onClick={fetchData}
          className="text-xs text-slate-500 hover:text-indigo-600 flex items-center gap-1 flex-shrink-0"
          title="Refresh Feed"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {/* Top Stories Grid */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <Newspaper className="w-5 h-5 text-indigo-600" />
            Top Stories
          </h2>
          <span className="text-xs text-slate-500">{articles.length} articles</span>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-44 bg-slate-100 rounded-xl animate-pulse" />
            ))}
          </div>
        ) : articles.length === 0 ? (
          <div className="p-12 text-center bg-white rounded-xl border border-slate-200">
            <p className="text-slate-600 font-medium">No articles found in this category.</p>
            <p className="text-xs text-slate-400 mt-1">Submit a new Kannada article to populate the feed.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {articles.map((article) => (
              <ArticleCard key={article.id} article={article} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
