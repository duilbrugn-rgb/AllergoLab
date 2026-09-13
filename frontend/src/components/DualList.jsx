import { useMemo, useState } from "react";
import { Search, X, ChevronRight, ChevronLeft, Trash2, ArrowRight } from "lucide-react";
import { Input } from "./ui/input";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { CATEGORIES, CATEGORY_ORDER } from "../lib/categories";

function CategoryPill({ type }) {
  const c = CATEGORIES[type];
  if (!c) return null;
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-1.5 py-0.5 text-[10px] font-semibold ${c.pill}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${c.dot}`} />
      {c.label}
    </span>
  );
}

export default function DualList({
  allergens,
  selectedCodes,
  setSelectedCodes,
  codeField = "code",
  showCategoryFilters = true,
}) {
  const [sourceSearch, setSourceSearch] = useState("");
  const [selectedSearch, setSelectedSearch] = useState("");
  const [activeFilters, setActiveFilters] = useState([]);

  const selectedSet = useMemo(() => new Set(selectedCodes), [selectedCodes]);

  const toggleFilter = (type) =>
    setActiveFilters((f) =>
      f.includes(type) ? f.filter((x) => x !== type) : [...f, type]
    );

  const filteredSource = useMemo(() => {
    const q = sourceSearch.trim().toLowerCase();
    return [...allergens].sort((a, b) =>
      a.name.localeCompare(b.name, "it", { sensitivity: "base" }) ||
      a[codeField].localeCompare(b[codeField], "it", { numeric: true })
    ).filter((a) => {
      if (selectedSet.has(a[codeField])) return false;
      if (showCategoryFilters && activeFilters.length && !activeFilters.includes(a.type)) return false;
      if (!q) return true;
      return (
        a[codeField].toLowerCase().includes(q) ||
        a.name.toLowerCase().includes(q) ||
        (a.siss_code || "").toLowerCase().includes(q)
      );
    });
  }, [allergens, sourceSearch, activeFilters, selectedSet, codeField, showCategoryFilters]);

  const selectedItems = useMemo(() => {
    const q = selectedSearch.trim().toLowerCase();
    const byCode = new Map(allergens.map((a) => [a[codeField], a]));
    return selectedCodes
      .map((c) => byCode.get(c))
      .filter(Boolean)
      .filter((a) =>
        !q
          ? true
          : a[codeField].toLowerCase().includes(q) ||
            a.name.toLowerCase().includes(q) ||
            (!showCategoryFilters && (a.siss_code || "").toLowerCase().includes(q))
      );
  }, [selectedCodes, selectedSearch, allergens, codeField, showCategoryFilters]);

  const addAllVisible = () => {
    const codes = filteredSource.map((a) => a[codeField]);
    if (!codes.length) return;
    setSelectedCodes([...selectedCodes, ...codes]);
  };

  const removeOne = (code) => setSelectedCodes(selectedCodes.filter((c) => c !== code));
  const clearAll = () => setSelectedCodes([]);

  const addSingle = (code) => {
    if (!selectedSet.has(code)) setSelectedCodes([...selectedCodes, code]);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-stretch">
      {/* Source list */}
      <div className="lg:col-span-5 flex flex-col rounded-xl border border-slate-200 bg-white overflow-hidden">
        <div className="p-3 border-b border-slate-100 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="font-heading font-semibold text-slate-900 text-sm">
              Catalogo esami
            </h3>
            <span className="text-xs text-slate-500" data-testid="source-count">
              {filteredSource.length} disponibili
            </span>
          </div>
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-400" />
            <Input
              value={sourceSearch}
              onChange={(e) => setSourceSearch(e.target.value)}
              placeholder="Cerca codice o allergene…"
              className="pl-8"
              data-testid="search-source-allergens"
            />
            {sourceSearch && (
              <button
                onClick={() => setSourceSearch("")}
                className="absolute right-2 top-2.5 text-slate-400 hover:text-slate-700"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>
          {showCategoryFilters && (
          <div className="flex flex-wrap gap-1.5">
            {CATEGORY_ORDER.map((type) => {
              const c = CATEGORIES[type];
              const on = activeFilters.includes(type);
              return (
                <button
                  key={type}
                  onClick={() => toggleFilter(type)}
                  data-testid={`filter-category-badge-${type}`}
                  className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-semibold transition-colors ${
                    on ? c.active : c.pill
                  }`}
                >
                  <span
                    className={`h-1.5 w-1.5 rounded-full ${on ? "bg-white" : c.dot}`}
                  />
                  {c.label}
                </button>
              );
            })}
          </div>
          )}
        </div>

        <div className="flex-1 overflow-y-auto max-h-[52vh] divide-y divide-slate-50">
          {filteredSource.map((a) => {
            const code = a[codeField];
            return (
            <button
              key={code}
              type="button"
              onClick={() => addSingle(code)}
              data-testid={`add-allergen-${code}`}
              className="w-full flex items-center gap-2.5 px-3 py-2 text-left hover:bg-sky-50 group transition-colors"
            >
              <div className="flex-1 min-w-0" data-testid={`source-allergen-item-${code}`}>
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-semibold text-slate-500">
                    {code}
                  </span>
                  {showCategoryFilters && <CategoryPill type={a.type} />}
                </div>
                <p className="text-sm text-slate-800 truncate">{a.name}</p>
              </div>
              <span
                className="shrink-0 h-7 w-7 rounded-full border border-slate-200 bg-white flex items-center justify-center text-slate-400 group-hover:bg-sky-600 group-hover:text-white group-hover:border-sky-600 transition-colors"
                title="Sposta a destra"
              >
                <ArrowRight className="h-4 w-4" />
              </span>
            </button>
            );
          })}
          {!filteredSource.length && (
            <p className="p-6 text-center text-sm text-slate-400">
              Nessun allergene trovato
            </p>
          )}
        </div>

        <div className="p-2.5 border-t border-slate-100 flex justify-between items-center gap-2">
          <span className="text-[11px] text-slate-400 pl-1">Clicca una riga per spostarla a destra →</span>
          <Button size="sm" variant="outline" onClick={addAllVisible} disabled={!filteredSource.length} data-testid="btn-add-all-allergens">
            <ChevronRight className="h-4 w-4 mr-1" /> Aggiungi tutti
          </Button>
        </div>
      </div>

      {/* Middle arrows (desktop) */}
      <div className="hidden lg:flex lg:col-span-2 flex-col items-center justify-center gap-3 text-slate-300">
        <ChevronRight className="h-8 w-8" />
        <ChevronLeft className="h-8 w-8" />
      </div>

      {/* Selected list */}
      <div className="lg:col-span-5 flex flex-col rounded-xl border border-slate-200 bg-white overflow-hidden">
        <div className="p-3 border-b border-slate-100 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="font-heading font-semibold text-slate-900 text-sm">
              Esami selezionati
            </h3>
            <Badge className="bg-sky-600 hover:bg-sky-600" data-testid="selected-count">
              {selectedCodes.length}
            </Badge>
          </div>
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-400" />
            <Input
              value={selectedSearch}
              onChange={(e) => setSelectedSearch(e.target.value)}
              placeholder="Filtra selezionati…"
              className="pl-8"
              data-testid="search-selected-allergens"
            />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto max-h-[52vh] divide-y divide-slate-50">
          {selectedItems.map((a) => {
            const code = a[codeField];
            return (
            <div
              key={code}
              data-testid={`selected-allergen-item-${code}`}
              className="flex items-start gap-2.5 px-3 py-2 hover:bg-rose-50/40 group"
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-semibold text-slate-500">
                    {code}
                  </span>
                  {showCategoryFilters && <CategoryPill type={a.type} />}
                </div>
                <p className="text-sm text-slate-800 truncate">{a.name}</p>
              </div>
              <button
                onClick={() => removeOne(code)}
                data-testid={`remove-allergen-${code}`}
                className="text-slate-300 group-hover:text-rose-600 transition-colors"
                title="Rimuovi"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            );
          })}
          {!selectedItems.length && (
            <p className="p-6 text-center text-sm text-slate-400">
              Nessun esame selezionato. Aggiungi allergeni dal catalogo.
            </p>
          )}
        </div>

        <div className="p-2.5 border-t border-slate-100 flex justify-end">
          <Button
            size="sm"
            variant="ghost"
            onClick={clearAll}
            disabled={!selectedCodes.length}
            data-testid="btn-clear-all-selected"
            className="text-slate-500 hover:text-rose-600"
          >
            <Trash2 className="h-4 w-4 mr-1.5" />
            Svuota lista
          </Button>
        </div>
      </div>
    </div>
  );
}
