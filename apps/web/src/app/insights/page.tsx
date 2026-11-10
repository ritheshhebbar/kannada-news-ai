"use client";

import { useEffect, useState } from "react";
import { api, DashboardStats } from "@/lib/api";
import { BarChart2, ShieldCheck, Zap, Layers, PieChart } from "lucide-react";

export default function InsightsPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getStats()
      .then(setStats)
      .catch((e) => console.error(e))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="py-12 space-y-4 max-w-4xl mx-auto">
        <div className="h-8 bg-slate-200 rounded w-1/3 animate-pulse" />
        <div className="h-48 bg-slate-100 rounded-xl animate-pulse" />
      </div>
    );
  }

  const categoryEntries = stats ? Object.entries(stats.categories_distribution) : [];

  return (
    <div className="max-w-5xl mx-auto py-4">
      <div className="mb-6 pb-3 border-b border-slate-200">
        <h1 className="text-xl sm:text-2xl font-bold text-slate-900 flex items-center gap-2">
          <BarChart2 className="w-6 h-6 text-indigo-600" />
          Pipeline Metrics & Evaluation Insights
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 mt-1">
          Operational metrics, factual verification rate, and category distributions across processed Kannada news articles.
        </p>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase">Factual Pass Rate</span>
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="text-2xl font-bold text-emerald-600">{stats?.verification_pass_rate}%</div>
          <p className="text-[11px] text-slate-400 mt-1">7-layer hallucination guards passed</p>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase">Average Latency</span>
            <Zap className="w-4 h-4 text-indigo-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900">{stats?.average_latency_sec}s</div>
          <p className="text-[11px] text-slate-400 mt-1">Translate + summarize end-to-end</p>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase">Articles Processed</span>
            <Layers className="w-4 h-4 text-blue-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900">{stats?.translated_count}</div>
          <p className="text-[11px] text-slate-400 mt-1">Total verified Kannada articles</p>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase">Review Queue</span>
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
          </div>
          <div className="text-2xl font-bold text-amber-600">{stats?.flagged_for_review}</div>
          <p className="text-[11px] text-slate-400 mt-1">Discrepancy flags detected</p>
        </div>
      </div>

      {/* Category Distribution Breakdown */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs mb-8">
        <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2 mb-4">
          <PieChart className="w-4 h-4 text-indigo-600" />
          Articles Distributed by Topic Category
        </h3>

        <div className="space-y-3">
          {categoryEntries.map(([slug, count]) => {
            const maxVal = Math.max(...categoryEntries.map(([_, c]) => c), 1);
            const percentage = Math.round((count / maxVal) * 100);
            return (
              <div key={slug} className="text-xs">
                <div className="flex items-center justify-between font-medium text-slate-700 mb-1">
                  <span className="capitalize">{slug}</span>
                  <span className="text-slate-400">{count} articles</span>
                </div>
                <div className="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-indigo-600 rounded-full transition-all duration-500"
                    style={{ width: `${Math.max(percentage, 5)}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

