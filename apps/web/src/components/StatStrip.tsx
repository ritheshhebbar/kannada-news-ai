import { DashboardStats } from "@/lib/api";
import { CheckCircle2, AlertTriangle, Clock, Layers, FileText } from "lucide-react";

interface StatStripProps {
  stats: DashboardStats | null;
}

export default function StatStrip({ stats }: StatStripProps) {
  if (!stats) return null;

  const items = [
    {
      label: "Articles Today",
      value: stats.articles_today,
      icon: FileText,
      color: "text-blue-600 bg-blue-50 dark:bg-blue-950/40",
    },
    {
      label: "Translated & Ready",
      value: stats.translated_count,
      icon: CheckCircle2,
      color: "text-emerald-600 bg-emerald-50 dark:bg-emerald-950/40",
    },
    {
      label: "Needs Review",
      value: stats.flagged_for_review,
      icon: AlertTriangle,
      color: "text-amber-600 bg-amber-50 dark:bg-amber-950/40",
    },
    {
      label: "Avg Pipeline Latency",
      value: `${stats.average_latency_sec}s`,
      icon: Clock,
      color: "text-indigo-600 bg-indigo-50 dark:bg-indigo-950/40",
    },
    {
      label: "Queue / In Flight",
      value: stats.items_in_queue,
      icon: Layers,
      color: "text-purple-600 bg-purple-50 dark:bg-purple-950/40",
    },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 mb-8">
      {items.map((it, idx) => {
        const Icon = it.icon;
        return (
          <div
            key={idx}
            className="bg-white dark:bg-slate-800/80 p-3.5 rounded-xl border border-slate-200 dark:border-slate-700/60 shadow-xs flex items-center gap-3"
          >
            <div className={`p-2.5 rounded-lg ${it.color}`}>
              <Icon className="w-5 h-5" />
            </div>
            <div>
              <p className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">{it.label}</p>
              <p className="text-xl font-bold text-slate-800 dark:text-slate-100">{it.value}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}

