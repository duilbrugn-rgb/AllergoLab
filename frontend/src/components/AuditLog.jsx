import { useEffect, useState, useCallback } from "react";
import { toast } from "sonner";
import { History, RefreshCw, Plus, Pencil, Trash2 } from "lucide-react";
import { Card } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import api from "../lib/api";

const ACTION = {
  create: { label: "Creato", cls: "bg-emerald-50 text-emerald-700 border-emerald-200", icon: Plus },
  update: { label: "Modificato", cls: "bg-amber-50 text-amber-800 border-amber-200", icon: Pencil },
  delete: { label: "Eliminato", cls: "bg-rose-50 text-rose-700 border-rose-200", icon: Trash2 },
};

export default function AuditLog() {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    api.get("/admin/audit")
      .then((r) => setEntries(r.data))
      .catch(() => toast.error("Errore caricamento registro"))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <Card className="p-5 border-slate-200">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <History className="h-4 w-4 text-sky-600" />
          <h3 className="font-heading font-semibold text-slate-900">Registro modifiche allergeni</h3>
          <Badge variant="secondary" data-testid="audit-count">{entries.length}</Badge>
        </div>
        <Button size="sm" variant="outline" onClick={load} data-testid="audit-refresh">
          <RefreshCw className="h-4 w-4 mr-1.5" /> Aggiorna
        </Button>
      </div>

      <div className="rounded-lg border border-slate-200 overflow-hidden">
        <div className="max-h-[58vh] overflow-y-auto divide-y divide-slate-50">
          {entries.map((e, i) => {
            const a = ACTION[e.action] || ACTION.update;
            const Icon = a.icon;
            return (
              <div key={i} data-testid="audit-entry" className="flex items-start gap-3 px-3 py-2.5">
                <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-semibold shrink-0 mt-0.5 ${a.cls}`}>
                  <Icon className="h-3 w-3" /> {a.label}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-slate-800">
                    <span className="font-mono text-xs text-slate-500">{e.allergen_code}</span>
                    {" — "}
                    {e.allergen_name}
                  </p>
                  {e.details && <p className="text-[11px] text-slate-500 mt-0.5 break-words">{e.details}</p>}
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    {e.changed_by_name} ({e.changed_by_email}) ·{" "}
                    {e.timestamp ? new Date(e.timestamp).toLocaleString("it-IT") : ""}
                  </p>
                </div>
              </div>
            );
          })}
          {!entries.length && (
            <p className="p-8 text-center text-sm text-slate-400">
              {loading ? "Caricamento…" : "Nessuna modifica registrata finora."}
            </p>
          )}
        </div>
      </div>
    </Card>
  );
}
