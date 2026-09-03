import { Copy, Calculator, Layers } from "lucide-react";
import { toast } from "sonner";
import { Button } from "./ui/button";
import { Card } from "./ui/card";

export default function SissSummary({ aggregation }) {
  if (!aggregation || !aggregation.codes) return null;
  const { codes, total, molecular_count, standard_count } = aggregation;

  const copyRecipe = () => {
    const text = codes
      .map((c) => `${c.siss_code} x${c.quantity}`)
      .join("   •   ");
    navigator.clipboard.writeText(text);
    toast.success("Ricetta copiata negli appunti");
  };

  return (
    <Card className="p-5 border-slate-200 bg-gradient-to-br from-white to-slate-50">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Calculator className="h-4 w-4 text-sky-600" />
          <h3 className="font-heading font-semibold text-slate-900">
            Codici SISS suggeriti
          </h3>
        </div>
        {codes.length > 0 && (
          <Button
            size="sm"
            variant="outline"
            onClick={copyRecipe}
            data-testid="siss-copy-recipe-button"
          >
            <Copy className="h-4 w-4 mr-1.5" /> Copia ricetta
          </Button>
        )}
      </div>

      <div className="flex flex-wrap gap-3 mb-4 text-xs">
        <span className="inline-flex items-center gap-1.5 rounded-md bg-slate-100 px-2.5 py-1 font-medium text-slate-700">
          <Layers className="h-3.5 w-3.5" /> Totale: {total}
        </span>
        <span className="inline-flex items-center gap-1.5 rounded-md bg-indigo-50 px-2.5 py-1 font-medium text-indigo-700">
          Molecolari: {molecular_count}
        </span>
        <span className="inline-flex items-center gap-1.5 rounded-md bg-sky-50 px-2.5 py-1 font-medium text-sky-700">
          Standard: {standard_count}
        </span>
      </div>

      {codes.length === 0 ? (
        <p className="text-sm text-slate-400 py-4 text-center">
          Seleziona almeno un allergene per calcolare i codici SISS.
        </p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {codes.map((c) => (
            <div
              key={c.siss_code}
              data-testid={`siss-summary-card-${c.siss_code}`}
              className="rounded-lg border border-slate-200 bg-white p-3.5 shadow-sm hover:shadow-md transition-shadow"
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-sm font-bold text-sky-800 bg-sky-50 px-2 py-0.5 rounded border border-sky-200">
                  {c.siss_code}
                </span>
                <span
                  data-testid={`siss-quantity-badge-${c.siss_code}`}
                  className="text-sm font-bold text-slate-900 bg-amber-100 border border-amber-200 rounded-md px-2 py-0.5"
                >
                  × {c.quantity}
                </span>
              </div>
              <p className="text-xs text-slate-600 mt-2 leading-snug">{c.description}</p>
              <p className="text-[11px] text-slate-400 mt-1">
                {c.allergen_count} allergen{c.allergen_count === 1 ? "e" : "i"} mappati
              </p>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}
