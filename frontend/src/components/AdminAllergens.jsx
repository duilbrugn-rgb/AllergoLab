import { useMemo, useState } from "react";
import { toast } from "sonner";
import { Search, Plus, Pencil, Trash2, Settings, X } from "lucide-react";
import { Card } from "./ui/card";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Textarea } from "./ui/textarea";
import { Dialog, DialogContent, DialogTitle, DialogDescription, DialogFooter } from "./ui/dialog";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "./ui/select";
import { CATEGORIES, CATEGORY_ORDER } from "../lib/categories";
import api, { formatApiErrorDetail } from "../lib/api";

const EMPTY = { code: "", name: "", type: "Alimenti", siss_code: "", siss_description: "" };

export default function AdminAllergens({ allergens, onChanged }) {
  const [search, setSearch] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingCode, setEditingCode] = useState(null); // null => create
  const [form, setForm] = useState(EMPTY);
  const [saving, setSaving] = useState(false);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return allergens;
    return allergens.filter(
      (a) =>
        a.code.toLowerCase().includes(q) ||
        a.name.toLowerCase().includes(q) ||
        (a.siss_code || "").toLowerCase().includes(q)
    );
  }, [allergens, search]);

  const openCreate = () => {
    setForm(EMPTY);
    setEditingCode(null);
    setDialogOpen(true);
  };

  const openEdit = (a) => {
    setForm({ ...a });
    setEditingCode(a.code);
    setDialogOpen(true);
  };

  const save = async () => {
    if (!form.code.trim() || !form.name.trim() || !form.siss_code.trim()) {
      toast.error("Codice, allergene e codice SISS sono obbligatori");
      return;
    }
    setSaving(true);
    try {
      if (editingCode) {
        await api.put(`/admin/allergens/${encodeURIComponent(editingCode)}`, form);
        toast.success("Allergene aggiornato");
      } else {
        await api.post("/admin/allergens", form);
        toast.success("Allergene aggiunto");
      }
      setDialogOpen(false);
      onChanged();
    } catch (err) {
      toast.error(formatApiErrorDetail(err.response?.data?.detail) || err.message);
    } finally {
      setSaving(false);
    }
  };

  const remove = async (a) => {
    if (!window.confirm(`Eliminare l'allergene ${a.code} — ${a.name}?`)) return;
    try {
      await api.delete(`/admin/allergens/${encodeURIComponent(a.code)}`);
      toast.success("Allergene eliminato");
      onChanged();
    } catch (err) {
      toast.error(formatApiErrorDetail(err.response?.data?.detail) || err.message);
    }
  };

  return (
    <Card className="p-5 border-slate-200">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div className="flex items-center gap-2">
          <Settings className="h-4 w-4 text-sky-600" />
          <h3 className="font-heading font-semibold text-slate-900">
            Configurazione catalogo allergeni
          </h3>
          <Badge variant="secondary" data-testid="admin-allergen-count">
            {allergens.length}
          </Badge>
        </div>
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-400" />
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Cerca…"
              className="pl-8 w-52"
              data-testid="admin-search-input"
            />
          </div>
          <Button onClick={openCreate} className="bg-sky-600 hover:bg-sky-700" data-testid="admin-add-allergen-button">
            <Plus className="h-4 w-4 mr-1.5" /> Aggiungi
          </Button>
        </div>
      </div>

      <div className="rounded-lg border border-slate-200 overflow-hidden">
        <div className="max-h-[58vh] overflow-y-auto divide-y divide-slate-50">
          {filtered.map((a) => {
            const cat = CATEGORIES[a.type];
            return (
              <div
                key={a.code}
                data-testid={`admin-allergen-row-${a.code}`}
                className="flex items-center gap-3 px-3 py-2 hover:bg-slate-50"
              >
                <span className="font-mono text-xs font-semibold text-slate-500 w-16 shrink-0">
                  {a.code}
                </span>
                {cat && (
                  <span className={`hidden sm:inline-flex items-center gap-1 rounded-full border px-1.5 py-0.5 text-[10px] font-semibold shrink-0 ${cat.pill}`}>
                    <span className={`h-1.5 w-1.5 rounded-full ${cat.dot}`} />
                    {cat.label}
                  </span>
                )}
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-slate-800 truncate">{a.name}</p>
                  <p className="text-[11px] text-slate-400 truncate">
                    SISS: <span className="font-mono">{a.siss_code}</span>
                    {a.siss_description ? ` · ${a.siss_description}` : ""}
                  </p>
                </div>
                <div className="flex items-center gap-1 shrink-0">
                  <Button size="icon" variant="ghost" className="h-8 w-8 text-slate-500 hover:text-sky-700" onClick={() => openEdit(a)} data-testid={`admin-edit-${a.code}`}>
                    <Pencil className="h-4 w-4" />
                  </Button>
                  <Button size="icon" variant="ghost" className="h-8 w-8 text-slate-400 hover:text-rose-600" onClick={() => remove(a)} data-testid={`admin-delete-${a.code}`}>
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            );
          })}
          {!filtered.length && (
            <p className="p-8 text-center text-sm text-slate-400">Nessun allergene trovato</p>
          )}
        </div>
      </div>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogTitle>{editingCode ? "Modifica allergene" : "Nuovo allergene"}</DialogTitle>
          <DialogDescription>
            Compila i campi del record del catalogo allergeni.
          </DialogDescription>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 py-2">
            <div className="space-y-1.5">
              <Label>Codice DnLab</Label>
              <Input value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} placeholder="es. f1" data-testid="admin-form-code" />
            </div>
            <div className="space-y-1.5">
              <Label>Tipologia</Label>
              <Select value={form.type} onValueChange={(v) => setForm({ ...form, type: v })}>
                <SelectTrigger data-testid="admin-form-type"><SelectValue placeholder="Tipologia" /></SelectTrigger>
                <SelectContent>
                  {CATEGORY_ORDER.map((t) => (
                    <SelectItem key={t} value={t}>{t}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5 sm:col-span-2">
              <Label>Allergene / Descrizione</Label>
              <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="es. Albume" data-testid="admin-form-name" />
            </div>
            <div className="space-y-1.5">
              <Label>Codice SISS</Label>
              <Input value={form.siss_code} onChange={(e) => setForm({ ...form, siss_code: e.target.value })} placeholder="es. 0090681.01" data-testid="admin-form-siss-code" />
            </div>
            <div className="space-y-1.5 sm:col-span-2">
              <Label>Descrizione SISS</Label>
              <Textarea value={form.siss_description} onChange={(e) => setForm({ ...form, siss_description: e.target.value })} placeholder="Descrizione SISS…" data-testid="admin-form-siss-description" />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              <X className="h-4 w-4 mr-1.5" /> Annulla
            </Button>
            <Button onClick={save} disabled={saving} className="bg-sky-600 hover:bg-sky-700" data-testid="admin-form-save">
              {saving ? "Salvataggio…" : "Salva"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  );
}
