import { AlertTriangle, AlertCircle, Info } from "lucide-react";

interface FlagBadgeProps {
  flags: Array<{ type: string; detail: string; severity?: string }>;
  onClick?: () => void;
}

export default function FlagBadge({ flags, onClick }: FlagBadgeProps) {
  if (!flags || flags.length === 0) return null;

  const hasCritical = flags.some((f) => f.severity === "critical" || f.type.includes("hallucination"));

  return (
    <button
      type="button"
      onClick={onClick}
      className={`inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-md transition cursor-pointer ${
        hasCritical
          ? "bg-red-100 text-red-700 dark:bg-red-950/70 dark:text-red-300 border border-red-300 dark:border-red-800"
          : "bg-amber-100 text-amber-700 dark:bg-amber-950/70 dark:text-amber-300 border border-amber-300 dark:border-amber-800"
      }`}
      title={flags.map((f) => f.detail).join("\n")}
    >
      {hasCritical ? <AlertCircle className="w-3 h-3 text-red-500" /> : <AlertTriangle className="w-3 h-3 text-amber-500" />}
      <span>{flags.length} Flag{flags.length > 1 ? "s" : ""}</span>
    </button>
  );
}

