import { useState, useEffect, useMemo, useLayoutEffect, useRef } from "react";
import { createPortal } from "react-dom";
import { Printer, Pencil, Check, FileText } from "lucide-react";
import { Dialog, DialogContent, DialogTitle, DialogDescription } from "./ui/dialog";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Textarea } from "./ui/textarea";
import { CATEGORY_ORDER } from "../lib/categories";

const FORM_CODE = "Mod-LABCENT13.08.01.01";
const REVISIONE = "00";
const DATA_MODULO = "04/09/2026";
const PAGE_CONTENT_PX = 880; // altezza utile per pagina (A4 meno header/margini)
const CHUNK = 24; // esami per blocco (evita overflow di una categoria lunga)

function fmtDate(iso) {
  if (!iso) return "—";
  const [y, m, d] = iso.split("-");
  if (!y || !m || !d) return iso;
  return `${d}/${m}/${y}`;
}

function chunk(arr, size) {
  const out = [];
  for (let i = 0; i < arr.length; i += size) out.push(arr.slice(i, i + size));
  return out;
}

function ReportHeader({ page, total }) {
  return (
    <div className="ph-header">
      <div className="ph-col ph-col-logo">
        <img src="/logo-regione.jpg" alt="Regione Lombardia" />
      </div>
      <div className="ph-col ph-col-title">
        <div className="ph-title-main">
          <div className="ph-title">ALLERGENI</div>
          <div className="ph-title">PER DETERMINAZIONE</div>
          <div className="ph-title-sub">IgE SPECIFICHE (RAST)</div>
        </div>
        <div className="ph-modulo">MODULO</div>
      </div>
      <div className="ph-col ph-col-meta">
        <div className="ph-mod-code">{FORM_CODE}</div>
        <div className="ph-meta-row">PAGINA: {page} DI {total}</div>
        <div className="ph-meta-row">REVISIONE: {REVISIONE}</div>
        <div className="ph-meta-row">DATA: {DATA_MODULO}</div>
      </div>
    </div>
  );
}

export default function ReportModal({ open, onOpenChange, allergens, selectedCodes, patient, doctorName, aggregation, onSave }) {
  const [editing, setEditing] = useState(false);
  const [header, setHeader] = useState("Laboratorio Analisi — Promemoria prelievo allergologico");
  const [notes, setNotes] = useState("");
  const [localPatient, setLocalPatient] = useState(patient);
  const [localDoctor, setLocalDoctor] = useState(doctorName);
  const [saved, setSaved] = useState(false);
  const [pages, setPages] = useState([]);
  const measureRefs = useRef([]);

  useEffect(() => {
    if (open) {
      setLocalPatient(patient);
      setLocalDoctor(doctorName);
      setEditing(false);
      setSaved(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  const byCode = useMemo(() => new Map(allergens.map((a) => [a.code, a])), [allergens]);
  const selectedItems = selectedCodes.map((c) => byCode.get(c)).filter(Boolean);

  const grouped = CATEGORY_ORDER.map((type) => ({
    type,
    items: selectedItems.filter((a) => a.type === type),
  })).filter((g) => g.items.length);

  // Costruisce i blocchi impaginabili del report da stampare
  const blocks = useMemo(() => {
    const list = [];
    list.push({
      key: "info",
      el: (
        <div className="pb-info">
          <div>
            <p className="pb-label">Paziente</p>
            <p className="pb-value">{localPatient.first_name} {localPatient.last_name}</p>
            <p className="pb-sub">Nato/a il {fmtDate(localPatient.dob)}</p>
          </div>
          <div>
            <p className="pb-label">Medico richiedente</p>
            <p className="pb-value">{localDoctor}</p>
          </div>
        </div>
      ),
    });

    if (aggregation?.codes?.length > 0) {
      list.push({
        key: "siss",
        el: (
          <div className="pb-siss">
            <p className="pb-siss-title">Codici SISS da riportare sulla ricetta</p>
            <table className="pb-siss-table">
              <thead>
                <tr>
                  <th>Codice SISS</th>
                  <th>Descrizione</th>
                  <th className="pb-right">Quantità</th>
                </tr>
              </thead>
              <tbody>
                {aggregation.codes.map((c) => (
                  <tr key={c.siss_code}>
                    <td className="pb-mono">{c.siss_code}</td>
                    <td>{c.description}</td>
                    <td className="pb-right pb-bold">× {c.quantity}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ),
      });
    }

    list.push({
      key: "exam-h",
      el: <p className="pb-section-title">Esami richiesti ({selectedItems.length})</p>,
    });

    grouped.forEach((g) => {
      chunk(g.items, CHUNK).forEach((items, ci) => {
        list.push({
          key: `g-${g.type}-${ci}`,
          el: (
            <div className="pb-group">
              <p className="pb-group-title">
                {g.type} · {g.items.length}{ci > 0 ? " (segue)" : ""}
              </p>
              <div className="pb-group-grid">
                {items.map((a) => (
                  <div key={a.code} className="pb-item">
                    <span className="pb-item-code">{a.code}</span>
                    <span>{a.name}</span>
                  </div>
                ))}
              </div>
            </div>
          ),
        });
      });
    });

    list.push({
      key: "notes",
      el: (
        <div className="pb-notes">
          <p className="pb-label">Note</p>
          <p className="pb-notes-text">{notes || "—"}</p>
        </div>
      ),
    });

    list.push({
      key: "sign",
      el: (
        <div className="pb-sign">
          <div className="pb-sign-generated">Documento generato da AllergoLab</div>
          <div className="pb-sign-line">Firma del medico</div>
        </div>
      ),
    });

    return list;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [localPatient, localDoctor, notes, selectedCodes.join(","), aggregation]);

  // Impagina i blocchi in pagine A4 in base all'altezza misurata
  useLayoutEffect(() => {
    if (!open) return;
    const packed = [[]];
    let cur = 0;
    let used = 0;
    blocks.forEach((_, i) => {
      const h = measureRefs.current[i]?.offsetHeight || 0;
      if (used + h > PAGE_CONTENT_PX && packed[cur].length) {
        cur += 1;
        packed[cur] = [];
        used = 0;
      }
      packed[cur].push(i);
      used += h;
    });
    setPages(packed);
  }, [blocks, open]);

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

        {/* Anteprima a schermo */}
        <div id="allergolab-report" className="px-8 py-6">
          <div className="mb-5">
            <ReportHeader page={1} total={pages.length || 1} />
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

          {aggregation?.codes?.length > 0 && (
            <div className="mb-6 rounded-lg border-2 border-sky-300 bg-sky-50 p-4">
              <p className="text-sm font-bold text-sky-900 mb-2">Codici SISS da riportare sulla ricetta</p>
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

          <div className="mb-6">
            <p className="text-sm font-bold text-slate-900 mb-2">Esami richiesti ({selectedItems.length})</p>
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

          <div className="mb-6">
            <p className="text-[11px] uppercase tracking-wider font-semibold text-slate-500 mb-1">Note</p>
            {editing ? (
              <Textarea value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Note aggiuntive…" className="no-print" />
            ) : (
              <p className="text-sm text-slate-700 whitespace-pre-wrap min-h-[1.5rem]">{notes || "—"}</p>
            )}
          </div>
        </div>
      </DialogContent>

      {/* Contenitore di misura (fuori schermo) + documento di stampa impaginato */}
      {open && createPortal(
        <>
          <div id="print-measure" aria-hidden="true">
            {blocks.map((b, i) => (
              <div key={b.key} ref={(el) => (measureRefs.current[i] = el)}>
                {b.el}
              </div>
            ))}
          </div>
          <div id="print-document">
            {pages.map((idxs, p) => (
              <div className="print-page" key={p}>
                <ReportHeader page={p + 1} total={pages.length} />
                <div className="print-body">
                  {idxs.map((i) => (
                    <div key={blocks[i].key}>{blocks[i].el}</div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </>,
        document.body
      )}
    </Dialog>
  );
}
