import { Calculator, Layers, FileStack } from "lucide-react";
import { Card } from "./ui/card";
import { IGG_SISS_CODE, IGG_SISS_DESCRIPTION, iggRecipeCount } from "../lib/iggPrestazioni";

export default function IggSissSummary({ selectedCount }) {
  const n = selectedCount || 0;
  const recipes = iggRecipeCount(n);

  return (
    <Card className="p-5 border-slate-200 bg-gradient-to-br from-white to-slate-50">
      <div className="flex items-center gap-2 mb-4">
        <Calculator className="h-4 w-4 text-sky-600" />
        <h3 className="font-heading font-semibold text-slate-900">
          Prestazioni IgG specifiche
        </h3>
      </div>

      <div className="flex flex-wrap gap-3 mb-4 text-xs">
        <span className="inline-flex items-center gap-1.5 rounded-md bg-slate-100 px-2.5 py-1 font-medium text-slate-700">
          <Layers className="h-3.5 w-3.5" /> IgG selezionate: {n}
        </span>
        <span className="inline-flex items-center gap-1.5 rounded-md bg-sky-50 px-2.5 py-1 font-medium text-sky-700">
          <FileStack className="h-3.5 w-3.5" /> Ricette: {recipes}
        </span>
      </div>

      {n === 0 ? (
        <p className="text-sm text-slate-400 py-4 text-center">
          Seleziona almeno un esame IgG per calcolare le prestazioni.
        </p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          <div
            data-testid="siss-summary-card-0090685"
            className="rounded-lg border border-slate-200 bg-white p-3.5 shadow-sm"
          >
            <div className="flex items-center justify-between">
              <span className="font-mono text-sm font-bold text-sky-800 bg-sky-50 px-2 py-0.5 rounded border border-sky-200">
                {IGG_SISS_CODE}
              </span>
              <span className="text-sm font-bold text-slate-900 bg-amber-100 border border-amber-200 rounded-md px-2 py-0.5">
                × {n}
              </span>
            </div>
            <p className="text-xs text-slate-600 mt-2 leading-snug">{IGG_SISS_DESCRIPTION}</p>
            <p className="text-[11px] text-slate-400 mt-1">
              {n} prestazion{n === 1 ? "e" : "i"} · {recipes} ricett{recipes === 1 ? "a" : "e"} (max 8 per ricetta)
            </p>
          </div>
        </div>
      )}
    </Card>
  );
}
