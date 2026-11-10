"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, ArticleListItem, Category } from "@/lib/api";
import ArticleCard from "@/components/ArticleCard";
import { LayoutGrid, List, Sparkles } from "lucide-react";

export default function EnglishFeedPage() {
  const [articles, setArticles] = useState<ArticleListItem[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>("");
  const [compactView, setCompactView] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getCategories().then(setCategories).catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    api.getArticles({
      category: selectedCategory || undefined,
      status: "ready",
      page_size: 20,
    })
      .then((res) => setArticles(res.items || []))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, [selectedCategory]);

  return (
    <div>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-indigo-600" />
            English Translated News Feed
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Grounded English translations powered by IndicTrans2 with automated verification.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="text-xs bg-white border border-slate-200 rounded-lg px-2.5 py-1.5 text-slate-700 font-medium"
          >
            <option value="">All Categories</option>
            {categories.map((c) => (
              <option key={c.id} value={c.slug}>
                {c.name_en}
              </option>
            ))}
          </select>

          <div className="flex items-center bg-slate-100 p-1 rounded-lg">
            <button
              type="button"
              onClick={() => setCompactView(false)}
              className={`p-1.5 rounded ${!compactView ? "bg-white text-indigo-600 shadow-xs" : "text-slate-400"}`}
              title="Grid Cards"
            >
              <LayoutGrid className="w-4 h-4" />
            </button>
            <button
              type="button"
              onClick={() => setCompactView(true)}
              className={`p-1.5 rounded ${compactView ? "bg-white text-indigo-600 shadow-xs" : "text-slate-400"}`}
              title="Compact List"
            >
              <List className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 bg-slate-100 rounded-xl animate-pulse" />
          ))}
        </div>
      ) : articles.length === 0 ? (
        <div className="p-12 text-center bg-white rounded-xl border border-slate-200">
          <p className="text-slate-600 font-medium">No translated articles available yet.</p>
        </div>
      ) : compactView ? (
        <div className="bg-white rounded-xl border border-slate-200 divide-y divide-slate-100">
          {articles.map((art) => (
            <Link
              key={art.id}
              href={`/article/${art.id}`}
              className="p-4 flex items-center justify-between gap-4 hover:bg-slate-50 transition group"
            >
              <div className="flex-1">
                <div className="flex items-center gap-2 text-xs text-slate-400 mb-1">
                  <span className="font-semibold text-slate-700">{art.source_name || "Direct"}</span>
                  <span>•</span>
                  <span>{art.section_label}</span>
                </div>
                <h3 className="text-sm sm:text-base font-semibold text-slate-900 group-hover:text-indigo-600 transition">
                  {art.title_en || art.title_kn}
                </h3>
              </div>
              <span className="text-xs text-indigo-600 font-medium whitespace-nowrap">
                Read &rarr;
              </span>
            </Link>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {articles.map((art) => (
            <ArticleCard key={art.id} article={art} />
          ))}
        </div>
      )}
    </div>
  );
}
