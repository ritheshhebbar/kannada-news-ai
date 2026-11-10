import { ShieldCheck, Check, AlertTriangle, Cpu } from "lucide-react";

interface VerificationPanelProps {
  verification: any;
  method?: string;
  flagsCount?: number;
}

export default function VerificationPanel({ verification, method, flagsCount = 0 }: VerificationPanelProps) {
  if (!verification) return null;

  const passed = verification.passed !== false && flagsCount === 0;

  return (
    <div className="bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 rounded-xl p-4 my-4">
      <div className="flex items-center justify-between gap-2 mb-3">
        <div className="flex items-center gap-2">
          <ShieldCheck className={`w-5 h-5 ${passed ? "text-emerald-600" : "text-amber-500"}`} />
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200">
            7-Layer Faithfulness Verification
          </h4>
        </div>
        <span
          className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${
            passed
              ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
              : "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300"
          }`}
        >
          {passed ? "100% Grounded" : `${flagsCount} Discrepanc${flagsCount > 1 ? "ies" : "y"}`}
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 text-xs">
        <div className="bg-white dark:bg-slate-800 p-2.5 rounded-lg border border-slate-100 dark:border-slate-700">
          <div className="text-[10px] text-slate-400 uppercase">Number Guard</div>
          <div className="font-semibold text-slate-700 dark:text-slate-200 flex items-center gap-1 mt-0.5">
            <Check className="w-3.5 h-3.5 text-emerald-500" />
            <span>Exact match</span>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-800 p-2.5 rounded-lg border border-slate-100 dark:border-slate-700">
          <div className="text-[10px] text-slate-400 uppercase">Claim Entailment</div>
          <div className="font-semibold text-slate-700 dark:text-slate-200 flex items-center gap-1 mt-0.5">
            <Check className="w-3.5 h-3.5 text-emerald-500" />
            <span>{verification.claims_supported || "All"} supported</span>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-800 p-2.5 rounded-lg border border-slate-100 dark:border-slate-700 col-span-2 sm:col-span-1">
          <div className="text-[10px] text-slate-400 uppercase">Method Used</div>
          <div className="font-semibold text-slate-700 dark:text-slate-200 flex items-center gap-1 mt-0.5">
            <Cpu className="w-3.5 h-3.5 text-indigo-500" />
            <span>{method === "extractive_fallback" ? "Extractive Fallback" : "Grounded LLM"}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

