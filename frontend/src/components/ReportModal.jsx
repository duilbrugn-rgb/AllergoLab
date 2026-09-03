import { useState, useEffect, useMemo } from "react";
import { Printer, Pencil, Check, FileText } from "lucide-react";
import { Dialog, DialogContent, DialogTitle, DialogDescription } from "./ui/dialog";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Textarea } from "./ui/textarea";
import { CATEGORY_ORDER } from "../lib/categories";

function fmtDate(iso) {
  if (!iso) return "—";
  const [y, m, d] = iso.split("-");
  if (!y || !m || !d) return iso;
  return `${d}/${m}/${y}`;
}

export default function ReportModal({ open, onOpenChange, allergens, selectedCodes, patient, doctorName, aggregation, onSave }) {
  const [editing, setEditing] = useState(false);
  const [header, setHeader] = useState("");
  const [notes, setNotes] = useState("");
  const [localPatient, setLocalPatient] = useState(patient);
  const [localDoctor, setLocalDoctor] = useState(doctorName);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (open) {
      setLocalPatient(patient);
      setLocalDoctor(doctorName);
      setEditing(false);
      setSaved(false);
      if (!header) setHeader("Laboratorio Analisi — Promemoria prelievo allergologico");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  const byCode = useMemo(() => new Map(allergens.map((a) => [a.code, a])), [allergens]);
  const selectedItems = selectedCodes.map((c) => byCode.get(c)).filter(Boolean);

  const grouped = CATEGORY_ORDER.map((type) => ({
    type,
    items: selectedItems.filter((a) => a.type === type),
  })).filter((g) => g.items.length);

  const today = new Date().toLocaleDateString("it-IT");

  const handleSave = async () => {
    await onSave({
      patient: localPatient,
      doctor_name: localDoctor,
      notes,
      letterhead: header,
    });
    setSaved(true);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[92vh] overflow-y-auto p-0">
        <DialogTitle className="sr-only">Anteprima Report AllergoLab</DialogTitle>
        <DialogDescription className="sr-only">
          Anteprima e modifica del report da consegnare al paziente prima della stampa.
        </DialogDescription>
        {/* Toolbar */}
        <div className="sticky top-0 z-10 flex items-center justify-between border-b border-slate-200 bg-white px-5 py-3 no-print">
          <div className="flex items-center gap-2">
            <FileText className="h-4 w-4 text-sky-600" />
            <span className="font-heading font-semibold text-slate-900">Anteprima Report</span>
          </div>
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant={editing ? "default" : "outline"}
              onClick={() => setEditing((e) => !e)}
              data-testid="btn-edit-report-button"
              className={editing ? "bg-emerald-600 hover:bg-emerald-700" : ""}
            >
              {editing ? <Check className="h-4 w-4 mr-1.5" /> : <Pencil className="h-4 w-4 mr-1.5" />}
              {editing ? "Fine modifica" : "Modifica"}
            </Button>
            <Button size="sm" variant="outline" onClick={handleSave} data-testid="btn-save-report-button">
              {saved ? <Check className="h-4 w-4 mr-1.5 text-emerald-600" /> : null}
              {saved ? "Salvato" : "Salva"}
            </Button>
            <Button size="sm" onClick={() => window.print()} data-testid="btn-print-report-button" className="bg-sky-600 hover:bg-sky-700">
              <Printer className="h-4 w-4 mr-1.5" /> Stampa
            </Button>
          </div>
        </div>

        {/* Printable area */}
        <div id="allergolab-report" className="px-8 py-6 print-area">
          <div className="border-b-2 border-slate-800 pb-3 mb-5">
            {editing ? (
              <Input value={header} onChange={(e) => setHeader(e.target.value)} className="font-semibold no-print" />
            ) : (
              <h2 className="font-heading text-xl font-bold text-slate-900">{header}</h2>
            )}
            <p className="text-xs text-slate-500 mt-1">Data emissione: {today}</p>
          </div>

          <div className="grid grid-cols-2 gap-6 mb-6">
            <div>
              <p className="text-[11px] uppercase tracking-wider font-semibold text-slate-500 mb-1">Paziente</p>
              {editing ? (
                <div className="space-y-2 no-print">
                  <Input value={localPatient.first_name} onChange={(e) => setLocalPatient({ ...localPatient, first_name: e.target.value })} placeholder="Nome" />
                  <Input value={localPatient.last_name} onChange={(e) => setLocalPatient({ ...localPatient, last_name: e.target.value })} placeholder="Cognome" />
                  <Input type="date" value={localPatient.dob} onChange={(e) => setLocalPatient({ ...localPatient, dob: e.target.value })} />
                </div>
              ) : (
                <>
                  <p className="text-base font-medium text-slate-900">
                    {localPatient.first_name} {localPatient.last_name}
                  </p>
                  <p className="text-sm text-slate-600">Nato/a il {fmtDate(localPatient.dob)}</p>
                </>
              )}
            </div>
            <div>
              <p className="text-[11px] uppercase tracking-wider font-semibold text-slate-500 mb-1">Medico richiedente</p>
              {editing ? (
                <Input value={localDoctor} onChange={(e) => setLocalDoctor(e.target.value)} className="no-print" />
              ) : (
                <p className="text-base font-medium text-slate-900">{localDoctor}</p>
              )}
            </div>
          </div>

          {/* SISS prescription box */}
          {aggregation?.codes?.length > 0 && (
            <div className="mb-6 rounded-lg border-2 border-sky-300 bg-sky-50 p-4">
              <p className="text-sm font-bold text-sky-900 mb-2">
                Codici SISS da riportare sulla ricetta
              </p>
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-[11px] uppercase tracking-wider text-sky-700 border-b border-sky-200">
                    <th className="py-1.5 pr-3">Codice SISS</th>
                    <th className="py-1.5 pr-3">Descrizione</th>
                    <th className="py-1.5 text-right">Quantità</th>
                  </tr>
                </thead>
                <tbody>
                  {aggregation.codes.map((c) => (
                    <tr key={c.siss_code} className="border-b border-sky-100 last:border-0">
                      <td className="py-1.5 pr-3 font-mono font-bold text-sky-900">{c.siss_code}</td>
                      <td className="py-1.5 pr-3 text-slate-700">{c.description}</td>
                      <td className="py-1.5 text-right font-bold text-slate-900">× {c.quantity}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Selected allergens */}
          <div className="mb-6">
            <p className="text-sm font-bold text-slate-900 mb-2">
              Esami richiesti ({selectedItems.length})
            </p>
            {grouped.map((g) => (
              <div key={g.type} className="mb-3">
                <p className="text-[11px] uppercase tracking-wider font-semibold text-slate-500 mb-1">
                  {g.type} · {g.items.length}
                </p>
                <div className="grid grid-cols-2 gap-x-6 gap-y-0.5">
                  {g.items.map((a) => (
                    <div key={a.code} className="flex items-baseline gap-2 text-sm">
                      <span className="font-mono text-xs text-slate-500 w-12 shrink-0">{a.code}</span>
                      <span className="text-slate-800">{a.name}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* Notes */}
          <div className="mb-6">
            <p className="text-[11px] uppercase tracking-wider font-semibold text-slate-500 mb-1">Note</p>
            {editing ? (
              <Textarea value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Note aggiuntive…" className="no-print" />
            ) : (
              <p className="text-sm text-slate-700 whitespace-pre-wrap min-h-[1.5rem]">{notes || "—"}</p>
            )}
          </div>

          <div className="mt-10 flex justify-between items-end">
            <div className="text-xs text-slate-400">Documento generato da AllergoLab</div>
            <div className="text-center">
              <div className="w-52 border-t border-slate-400 pt-1 text-xs text-slate-600">
                Firma del medico
              </div>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
