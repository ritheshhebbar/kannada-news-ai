import { Entity } from "@/lib/api";
import { User, MapPin, Building, Tag } from "lucide-react";

interface EntityChipsProps {
  entities: Entity[];
}

export default function EntityChips({ entities }: EntityChipsProps) {
  if (!entities || entities.length === 0) return null;

  // Filter to English entities or unique ones for display
  const displayEntities = entities.filter((e) => e.lang === "en" || !entities.some((o) => o.norm_text === e.text));

  const getTypeStyle = (type: string) => {
    switch (type.toUpperCase()) {
      case "PER":
        return {
          icon: User,
          bg: "bg-blue-50 text-blue-700 dark:bg-blue-950/60 dark:text-blue-300 border-blue-200 dark:border-blue-800",
          label: "Person",
        };
      case "LOC":
        return {
          icon: MapPin,
          bg: "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800",
          label: "Location",
        };
      case "ORG":
        return {
          icon: Building,
          bg: "bg-purple-50 text-purple-700 dark:bg-purple-950/60 dark:text-purple-300 border-purple-200 dark:border-purple-800",
          label: "Organization",
        };
      default:
        return {
          icon: Tag,
          bg: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300 border-slate-200 dark:border-slate-700",
          label: type,
        };
    }
  };

  return (
    <div className="flex flex-wrap items-center gap-1.5 my-3">
      <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider mr-1">Entities:</span>
      {displayEntities.map((ent, idx) => {
        const style = getTypeStyle(ent.type);
        const Icon = style.icon;
        return (
          <span
            key={idx}
            className={`inline-flex items-center gap-1 text-xs px-2.5 py-0.5 rounded-full border ${style.bg}`}
          >
            <Icon className="w-3 h-3 opacity-70" />
            <span className="font-medium">{ent.norm_text || ent.text}</span>
          </span>
        );
      })}
    </div>
  );
}
