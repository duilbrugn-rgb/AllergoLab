import { useMemo, useState } from "react";
import { toast } from "sonner";
import { Layers, ArrowRight, Eye } from "lucide-react";
import { Card } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Dialog, DialogContent, DialogTitle, DialogDescription } from "./ui/dialog";
import { CATEGORIES } from "../lib/categories";

export default function ProfileSelector({ profiles, allergens, selectedCodes, setSelectedCodes }) {
  const [viewing, setViewing] = useState(null);
  const byCode = useMemo(() => new Map(allergens.map((a) => [a.code, a])), [allergens]);

  if (!profiles?.length) return null;
  const selectedSet = new Set(selectedCodes);

  const addProfile = (p) => {
    const toAdd = p.allergen_codes.filter((c) => byCode.has(c) && !selectedSet.has(c));
    if (!toAdd.length) {
      toast.info("Tutti gli allergeni del profilo sono già nella lista");
      return;
    }
    setSelectedCodes([...selectedCodes, ...toAdd]);
    toast.success(`Profilo "${p.name}" aggiunto (${toAdd.length} allergeni)`);
  };

  return (
    <Card className="p-5 border-slate-200" data-testid="profile-selector">
      <div className="flex items-center gap-2 mb-1">
        <Layers className="h-4 w-4 text-sky-600" />
        <h3 className="font-heading font-semibold text-slate-900">Profili di allergeni</h3>
        <Badge variant="secondary">{profiles.length}</Badge>
      </div>
      <p className="text-xs text-slate-500 mb-4">
        Aggiungi in un click tutti gli allergeni di un profilo predefinito. Potrai poi rimuovere quelli non necessari dalla lista di destra.
      </p>

      <div className="flex gap-3 overflow-x-auto pb-1">
        {profiles.map((p) => (
          <div
            key={p.profile_id}
            data-testid={`profile-card-${p.profile_id}`}
            className="min-w-[240px] max-w-[280px] shrink-0 rounded-xl border border-slate-200 bg-white p-4 flex flex-col"
          >
            <div className="flex items-start justify-between gap-2">
              <p className="font-medium text-slate-900 leading-tight">{p.name}</p>
              <Badge className="bg-sky-600 hover:bg-sky-600 shrink-0">{p.allergen_codes.length}</Badge>
            </div>
            {p.description && (
              <p className="text-xs text-slate-500 mt-1 line-clamp-2">{p.description}</p>
            )}
            <div className="flex gap-2 mt-3 pt-3 border-t border-slate-100">
              <Button size="sm" variant="outline" className="flex-1" onClick={() => setViewing(p)} data-testid={`profile-view-${p.profile_id}`}>
                <Eye className="h-4 w-4 mr-1.5" /> Vedi
              </Button>
              <Button size="sm" className="flex-1 bg-sky-600 hover:bg-sky-700" onClick={() => addProfile(p)} data-testid={`profile-add-${p.profile_id}`}>
                Aggiungi <ArrowRight className="h-4 w-4 ml-1" />
              </Button>
            </div>
          </div>
        ))}
      </div>

      <Dialog open={!!viewing} onOpenChange={(o) => !o && setViewing(null)}>
        <DialogContent className="max-w-lg max-h-[85vh] overflow-y-auto">
          <DialogTitle>{viewing?.name}</DialogTitle>
          <DialogDescription>
            {viewing?.allergen_codes?.length} allergeni contenuti in questo profilo.
          </DialogDescription>
          <div className="divide-y divide-slate-50 -mx-2">
            {viewing?.allergen_codes?.map((code) => {
              const a = byCode.get(code);
              const cat = a && CATEGORIES[a.type];
              return (
                <div key={code} className="flex items-center gap-2.5 px-2 py-2">
                  <span className="font-mono text-xs font-semibold text-slate-500 w-14 shrink-0">{code}</span>
                  {cat && (
                    <span className={`inline-flex items-center gap-1 rounded-full border px-1.5 py-0.5 text-[10px] font-semibold shrink-0 ${cat.pill}`}>
                      <span className={`h-1.5 w-1.5 rounded-full ${cat.dot}`} />{cat.label}
                    </span>
                  )}
                  <span className="text-sm text-slate-800 truncate">{a ? a.name : "(allergene non più disponibile)"}</span>
                </div>
              );
            })}
          </div>
          <Button className="w-full bg-sky-600 hover:bg-sky-700 mt-2" onClick={() => { addProfile(viewing); setViewing(null); }} data-testid="profile-dialog-add">
            Aggiungi tutti al report <ArrowRight className="h-4 w-4 ml-1" />
          </Button>
        </DialogContent>
      </Dialog>
    </Card>
  );
}
