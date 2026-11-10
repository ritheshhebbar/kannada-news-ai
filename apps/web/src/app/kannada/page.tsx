"use client";

import { useEffect, useState } from "react";
import { api, ArticleListItem, Category, Source } from "@/lib/api";
import ArticleCard from "@/components/ArticleCard";
import { Globe, Filter } from "lucide-react";

export default function KannadaFeedPage() {
  const [articles, setArticles] = useState<ArticleListItem[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>("");
  const [selectedSource, setSelectedSource] = useState<string>("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.getCategories().catch(() => []),
      api.getSources().catch(() => []),
    ]).then(([cats, srcs]) => {
      setCategories(cats);
      setSources(srcs);
    });
  }, []);

  useEffect(() => {
    setLoading(true);
    api.getArticles({
      category: selectedCategory || undefined,
      source_id: selectedSource ? parseInt(selectedSource) : undefined,
      page_size: 20,
    })
      .then((res) => setArticles(res.items || []))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, [selectedCategory, selectedSource]);

  return (
    <div>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 flex items-center gap-2 font-kannada">
            <Globe className="w-6 h-6 text-indigo-600" />
            ಕನ್ನಡ ಸುದ್ದಿ ಫೀಡ್ (Original Kannada News)
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Browse authentic Kannada news articles from registered state publications.
          </p>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-2">
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="text-xs bg-white border border-slate-200 rounded-lg px-2.5 py-1.5 text-slate-700 font-medium"
          >
            <option value="">All Categories</option>
            {categories.map((c) => (
              <option key={c.id} value={c.slug}>
                {c.name_kn} ({c.name_en})
              </option>
            ))}
          </select>

          <select
            value={selectedSource}
            onChange={(e) => setSelectedSource(e.target.value)}
            className="text-xs bg-white border border-slate-200 rounded-lg px-2.5 py-1.5 text-slate-700 font-medium"
          >
            <option value="">All Publications</option>
            {sources.map((s) => (
              <option key={s.id} value={s.id.toString()}>
                {s.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-44 bg-slate-100 rounded-xl animate-pulse" />
          ))}
        </div>
      ) : articles.length === 0 ? (
        <div className="p-12 text-center bg-white rounded-xl border border-slate-200">
          <p className="text-slate-600 font-medium font-kannada text-lg">ಯಾವುದೇ ಲೇಖನಗಳು ಕಂಡುಬಂದಿಲ್ಲ.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {articles.map((art) => (
            <ArticleCard key={art.id} article={art} showKannadaFirst={true} />
          ))}
        </div>
      )}
    </div>
  );
}

