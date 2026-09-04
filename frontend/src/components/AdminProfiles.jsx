import { useMemo, useState } from "react";
import { toast } from "sonner";
import { Layers, Plus, Pencil, Trash2, Search, X } from "lucide-react";
import { Card } from "./ui/card";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Textarea } from "./ui/textarea";
import { Dialog, DialogContent, DialogTitle, DialogDescription, DialogFooter } from "./ui/dialog";
import { CATEGORIES } from "../lib/categories";
import api, { formatApiErrorDetail } from "../lib/api";

const EMPTY = { name: "", description: "", allergen_codes: [] };

export default function AdminProfiles({ allergens, profiles, onChanged }) {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(EMPTY);
  const [pickerSearch, setPickerSearch] = useState("");
  const [saving, setSaving] = useState(false);

  const byCode = useMemo(() => new Map(allergens.map((a) => [a.code, a])), [allergens]);
  const selectedSet = useMemo(() => new Set(form.allergen_codes), [form.allergen_codes]);

  const pickerResults = useMemo(() => {
    const q = pickerSearch.trim().toLowerCase();
    return allergens
      .filter((a) => !selectedSet.has(a.code))
      .filter((a) => !q || a.code.toLowerCase().includes(q) || a.name.toLowerCase().includes(q))
      .slice(0, 50);
  }, [allergens, pickerSearch, selectedSet]);

  const openCreate = () => { setForm(EMPTY); setEditing(null); setPickerSearch(""); setDialogOpen(true); };
  const openEdit = (p) => {
    setForm({ name: p.name, description: p.description || "", allergen_codes: [...p.allergen_codes] });
    setEditing(p.profile_id); setPickerSearch(""); setDialogOpen(true);
  };

  const addCode = (code) => setForm((f) => ({ ...f, allergen_codes: [...f.allergen_codes, code] }));
  const removeCode = (code) => setForm((f) => ({ ...f, allergen_codes: f.allergen_codes.filter((c) => c !== code) }));

  const save = async () => {
    if (!form.name.trim()) { toast.error("Il nome del profilo è obbligatorio"); return; }
    if (!form.allergen_codes.length) { toast.error("Aggiungi almeno un allergene al profilo"); return; }
    setSaving(true);
    try {
      if (editing) { await api.put(`/admin/profiles/${editing}`, form); toast.success("Profilo aggiornato"); }
      else { await api.post("/admin/profiles", form); toast.success("Profilo creato"); }
      setDialogOpen(false); onChanged();
    } catch (err) {
      toast.error(formatApiErrorDetail(err.response?.data?.detail) || err.message);
    } finally { setSaving(false); }
  };

  const remove = async (p) => {
    if (!window.confirm(`Eliminare il profilo "${p.name}"?`)) return;
    try { await api.delete(`/admin/profiles/${p.profile_id}`); toast.success("Profilo eliminato"); onChanged(); }
    catch (err) { toast.error(formatApiErrorDetail(err.response?.data?.detail) || err.message); }
  };

  return (
    <Card className="p-5 border-slate-200">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Layers className="h-4 w-4 text-sky-600" />
          <h3 className="font-heading font-semibold text-slate-900">Profili di allergeni</h3>
          <Badge variant="secondary" data-testid="admin-profiles-count">{profiles.length}</Badge>
        </div>
        <Button onClick={openCreate} className="bg-sky-600 hover:bg-sky-700" data-testid="admin-add-profile-button">
          <Plus className="h-4 w-4 mr-1.5" /> Nuovo profilo
        </Button>
      </div>

      <div className="rounded-lg border border-slate-200 overflow-hidden">
        <div className="max-h-[58vh] overflow-y-auto divide-y divide-slate-50">
          {profiles.map((p) => (
            <div key={p.profile_id} data-testid={`admin-profile-row-${p.profile_id}`} className="flex items-start gap-3 px-3 py-3 hover:bg-slate-50">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-medium text-slate-800">{p.name}</p>
                  <Badge className="bg-sky-600 hover:bg-sky-600">{p.allergen_codes.length}</Badge>
                </div>
                {p.description && <p className="text-xs text-slate-500 mt-0.5">{p.description}</p>}
                <p className="text-[11px] text-slate-400 mt-1 font-mono truncate">
                  {p.allergen_codes.slice(0, 14).join(", ")}{p.allergen_codes.length > 14 ? " …" : ""}
                </p>
              </div>
              <div className="flex items-center gap-1 shrink-0">
                <Button size="icon" variant="ghost" className="h-8 w-8 text-slate-500 hover:text-sky-700" onClick={() => openEdit(p)} data-testid={`admin-profile-edit-${p.profile_id}`}>
                  <Pencil className="h-4 w-4" />
                </Button>
                <Button size="icon" variant="ghost" className="h-8 w-8 text-slate-400 hover:text-rose-600" onClick={() => remove(p)} data-testid={`admin-profile-delete-${p.profile_id}`}>
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
          ))}
          {!profiles.length && <p className="p-8 text-center text-sm text-slate-400">Nessun profilo. Crea il primo con "Nuovo profilo".</p>}
        </div>
      </div>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[92vh] overflow-y-auto">
          <DialogTitle>{editing ? "Modifica profilo" : "Nuovo profilo"}</DialogTitle>
          <DialogDescription>Definisci nome, descrizione e gli allergeni contenuti nel profilo.</DialogDescription>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 py-2">
            <div className="space-y-1.5">
              <Label>Nome profilo</Label>
              <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="es. Pannello inalanti base" data-testid="admin-profile-name" />
            </div>
            <div className="space-y-1.5">
              <Label>Descrizione (opzionale)</Label>
              <Input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="Breve descrizione" data-testid="admin-profile-description" />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Picker */}
            <div className="space-y-2">
              <Label>Aggiungi allergeni</Label>
              <div className="relative">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-400" />
                <Input value={pickerSearch} onChange={(e) => setPickerSearch(e.target.value)} placeholder="Cerca…" className="pl-8" data-testid="admin-profile-picker-search" />
              </div>
              <div className="rounded-lg border border-slate-200 max-h-56 overflow-y-auto divide-y divide-slate-50">
                {pickerResults.map((a) => (
                  <button key={a.code} type="button" onClick={() => addCode(a.code)} data-testid={`admin-profile-pick-${a.code}`} className="w-full flex items-center gap-2 px-2.5 py-1.5 text-left hover:bg-sky-50">
                    <span className="font-mono text-xs text-slate-500 w-12 shrink-0">{a.code}</span>
                    <span className="text-sm text-slate-800 truncate flex-1">{a.name}</span>
                    <Plus className="h-3.5 w-3.5 text-sky-600 shrink-0" />
                  </button>
                ))}
                {!pickerResults.length && <p className="p-4 text-center text-xs text-slate-400">Nessun risultato</p>}
              </div>
            </div>

            {/* Selected chips */}
            <div className="space-y-2">
              <Label>Nel profilo ({form.allergen_codes.length})</Label>
              <div className="rounded-lg border border-slate-200 max-h-56 overflow-y-auto p-2 flex flex-wrap gap-1.5 content-start" data-testid="admin-profile-selected">
                {form.allergen_codes.map((code) => {
                  const a = byCode.get(code);
                  const cat = a && CATEGORIES[a.type];
                  return (
                    <span key={code} className={`inline-flex items-center gap-1 rounded-full border pl-2 pr-1 py-0.5 text-[11px] font-medium ${cat ? cat.pill : "bg-slate-100 text-slate-700 border-slate-200"}`}>
                      <span className="font-mono">{code}</span>
                      <button type="button" onClick={() => removeCode(code)} className="hover:text-rose-600" data-testid={`admin-profile-remove-${code}`}>
                        <X className="h-3 w-3" />
                      </button>
                    </span>
                  );
                })}
                {!form.allergen_codes.length && <p className="text-xs text-slate-400 p-2">Nessun allergene selezionato</p>}
              </div>
            </div>
          </div>

          <DialogFooter className="mt-2">
            <Button variant="outline" onClick={() => setDialogOpen(false)}>Annulla</Button>
            <Button onClick={save} disabled={saving} className="bg-sky-600 hover:bg-sky-700" data-testid="admin-profile-save">
              {saving ? "Salvataggio…" : "Salva profilo"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  );
}
