import { useEffect, useState, useRef, useCallback } from "react";
import { toast } from "sonner";
import { FileText, ClipboardList, History, Trash2, Eye, Settings } from "lucide-react";
import Header from "../components/Header";
import PatientForm from "../components/PatientForm";
import DualList from "../components/DualList";
import SissSummary from "../components/SissSummary";
import IggSissSummary from "../components/IggSissSummary";
import ReportModal from "../components/ReportModal";
import AdminAllergens from "../components/AdminAllergens";
import AdminUsers from "../components/AdminUsers";
import AuditLog from "../components/AuditLog";
import AdminProfiles from "../components/AdminProfiles";
import ProfileSelector from "../components/ProfileSelector";
import { Button } from "../components/ui/button";
import { Card } from "../components/ui/card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "../components/ui/tabs";
import api from "../lib/api";
import { useAuth } from "../context/AuthContext";
import { buildIggPrestazioni } from "../lib/iggPrestazioni";

export default function AppPage() {
  const { user } = useAuth();
  const [allergens, setAllergens] = useState([]);
  const [specificIgg, setSpecificIgg] = useState([]);
  const [profiles, setProfiles] = useState([]);
  const [workspaceType, setWorkspaceType] = useState("ige");
  const [selectedCodes, setSelectedCodes] = useState([]);
  const [patient, setPatient] = useState({ first_name: "", last_name: "", dob: "" });
  const [doctorName, setDoctorName] = useState(user?.name || "");
  const [aggregation, setAggregation] = useState({ codes: [], total: 0, molecular_count: 0, standard_count: 0 });
  const [reportOpen, setReportOpen] = useState(false);
  const [history, setHistory] = useState([]);
  const [historyFilter, setHistoryFilter] = useState("all");
  const debounceRef = useRef(null);

  const loadAllergens = useCallback(() => {
    api.get("/allergens").then((r) => setAllergens(r.data)).catch(() => toast.error("Errore caricamento allergeni"));
  }, []);

  const loadSpecificIgg = useCallback(() => {
    api.get("/specific-igg").then((r) => setSpecificIgg(r.data)).catch(() => toast.error("Errore caricamento IgG specifiche"));
  }, []);

  const loadHistory = useCallback(() => {
    api.get("/reports").then((r) => setHistory(r.data)).catch(() => {});
  }, []);

  const loadProfiles = useCallback(() => {
    api.get("/profiles").then((r) => setProfiles(r.data)).catch(() => {});
  }, []);

  useEffect(() => {
    loadAllergens();
    loadSpecificIgg();
    loadHistory();
    loadProfiles();
  }, [loadAllergens, loadSpecificIgg, loadHistory, loadProfiles]);

  useEffect(() => {
    if (workspaceType === "igg") {
      if (debounceRef.current) clearTimeout(debounceRef.current);
      setAggregation(buildIggPrestazioni(selectedCodes.length));
      return;
    }
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (!selectedCodes.length) {
      setAggregation({ codes: [], total: 0, molecular_count: 0, standard_count: 0 });
      return;
    }
    debounceRef.current = setTimeout(() => {
      api.post("/aggregate", { codes: selectedCodes })
        .then((r) => setAggregation(r.data))
        .catch(() => {});
    }, 250);
    return () => debounceRef.current && clearTimeout(debounceRef.current);
  }, [selectedCodes, workspaceType]);

  const switchWorkspace = (type) => {
    if (type === workspaceType) return;
    setWorkspaceType(type);
    setSelectedCodes([]);
    setAggregation(
      type === "igg"
        ? buildIggPrestazioni(0)
        : { codes: [], total: 0, molecular_count: 0, standard_count: 0 }
    );
  };

  const saveReport = async (overrides) => {
    try {
      await api.post("/reports", {
        patient: overrides?.patient || patient,
        doctor_name: overrides?.doctor_name || doctorName,
        allergen_codes: selectedCodes,
        notes: overrides?.notes || "",
        letterhead: overrides?.letterhead || "",
        report_type: workspaceType,
      });
      toast.success("Report salvato nello storico");
      loadHistory();
    } catch {
      toast.error("Errore nel salvataggio del report");
    }
  };

  const deleteReport = async (id) => {
    try {
      await api.delete(`/reports/${id}`);
      loadHistory();
      toast.success("Report eliminato");
    } catch {
      toast.error("Errore eliminazione");
    }
  };

  const loadFromHistory = (rep) => {
    const type = rep.report_type === "igg" ? "igg" : "ige";
    const codes = rep.allergen_codes || [];
    setWorkspaceType(type);
    setSelectedCodes(codes);
    setPatient(rep.patient || { first_name: "", last_name: "", dob: "" });
    setDoctorName(rep.doctor_name || doctorName);
    if (type === "igg") {
      setAggregation(buildIggPrestazioni(codes.length));
    }
    toast.success("Report caricato nell'editor");
  };

  const visibleHistory = history.filter((rep) => {
    if (historyFilter === "all") return true;
    return (rep.report_type || "ige") === historyFilter;
  });

  return (
    <div className="min-h-screen bg-slate-50">
      <Header />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <Tabs defaultValue="nuovo" className="w-full">
          <TabsList className="mb-6">
            <TabsTrigger value="nuovo" data-testid="tab-nuovo-report">
              <ClipboardList className="h-4 w-4 mr-1.5" /> Nuovo Report
            </TabsTrigger>
            <TabsTrigger value="storico" data-testid="tab-storico">
              <History className="h-4 w-4 mr-1.5" /> Storico ({history.length})
            </TabsTrigger>
            {user?.role === "admin" && (
              <TabsTrigger value="config" data-testid="tab-config">
                <Settings className="h-4 w-4 mr-1.5" /> Configurazione
              </TabsTrigger>
            )}
          </TabsList>

          <TabsContent value="nuovo" className="space-y-6">
            <PatientForm patient={patient} setPatient={setPatient} doctorName={doctorName} setDoctorName={setDoctorName} />

            <Card className="p-5 border-slate-200">
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-3">
                Tipo di esame
              </p>
              <div className="inline-flex flex-wrap rounded-lg bg-slate-100 p-1" data-testid="workspace-type-selector">
                <button
                  type="button"
                  data-testid="workspace-ige"
                  onClick={() => switchWorkspace("ige")}
                  className={`rounded-md px-3 py-1.5 text-sm font-medium transition-all ${
                    workspaceType === "ige"
                      ? "bg-white text-slate-900 shadow"
                      : "text-slate-500 hover:text-slate-800"
                  }`}
                >
                  IgE specifiche
                </button>
                <button
                  type="button"
                  data-testid="workspace-igg"
                  onClick={() => switchWorkspace("igg")}
                  className={`rounded-md px-3 py-1.5 text-sm font-medium transition-all ${
                    workspaceType === "igg"
                      ? "bg-white text-slate-900 shadow"
                      : "text-slate-500 hover:text-slate-800"
                  }`}
                >
                  IgG specifiche / precipitine
                </button>
              </div>
              <p className="text-xs text-slate-500 mt-3">
                {workspaceType === "ige"
                  ? "Stai componendo un pannello per IgE specifiche. Aggregazione SISS invariata."
                  : "Stai componendo un pannello per IgG specifiche / precipitine. Le prestazioni coincidono con gli esami selezionati."}
              </p>
            </Card>

            {workspaceType === "ige" && (
              <ProfileSelector profiles={profiles} allergens={allergens} selectedCodes={selectedCodes} setSelectedCodes={setSelectedCodes} />
            )}

            <DualList
              key={workspaceType}
              allergens={workspaceType === "ige" ? allergens : specificIgg}
              selectedCodes={selectedCodes}
              setSelectedCodes={setSelectedCodes}
              codeField={workspaceType === "ige" ? "code" : "dnlab_code"}
              showCategoryFilters={workspaceType === "ige"}
            />

            {workspaceType === "ige" ? (
              <SissSummary aggregation={aggregation} />
            ) : (
              <IggSissSummary selectedCount={selectedCodes.length} />
            )}

            <div className="flex justify-end">
              <Button
                size="lg"
                disabled={!selectedCodes.length}
                onClick={() => setReportOpen(true)}
                data-testid="btn-preview-report-button"
                className="bg-slate-900 hover:bg-slate-800"
              >
                <FileText className="h-4 w-4 mr-2" />
                Genera Report ({selectedCodes.length})
              </Button>
            </div>
          </TabsContent>

          <TabsContent value="storico">
            {history.length === 0 ? (
              <Card className="p-12 text-center text-slate-400 border-dashed">
                <History className="h-8 w-8 mx-auto mb-3 opacity-50" />
                Nessun report salvato finora.
              </Card>
            ) : (
              <div className="space-y-4">
                <div className="inline-flex flex-wrap rounded-lg bg-slate-100 p-1" data-testid="history-type-filter">
                  {[
                    { id: "all", label: "Tutti" },
                    { id: "ige", label: "IgE" },
                    { id: "igg", label: "IgG" },
                  ].map((opt) => (
                    <button
                      key={opt.id}
                      type="button"
                      data-testid={`history-filter-${opt.id}`}
                      onClick={() => setHistoryFilter(opt.id)}
                      className={`rounded-md px-3 py-1.5 text-sm font-medium transition-all ${
                        historyFilter === opt.id
                          ? "bg-white text-slate-900 shadow"
                          : "text-slate-500 hover:text-slate-800"
                      }`}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
                {visibleHistory.length === 0 ? (
                  <Card className="p-12 text-center text-slate-400 border-dashed">
                    Nessun report in questo filtro.
                  </Card>
                ) : (
              <div className="grid gap-3">
                {visibleHistory.map((rep) => {
                  const kind = rep.report_type === "igg" ? "igg" : "ige";
                  return (
                  <Card key={rep.report_id} className="p-4 flex items-center justify-between" data-testid={`history-item-${rep.report_id}`}>
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="font-medium text-slate-900">
                          {rep.patient?.first_name} {rep.patient?.last_name || "— Paziente"}
                        </p>
                        <span
                          data-testid={`history-badge-${kind}`}
                          className={`inline-flex items-center rounded-md border px-2 py-0.5 text-[11px] font-semibold ${
                            kind === "igg"
                              ? "bg-teal-50 text-teal-800 border-teal-200"
                              : "bg-sky-50 text-sky-800 border-sky-200"
                          }`}
                        >
                          {kind === "igg" ? "IgG" : "IgE"}
                        </span>
                      </div>
                      <p className="text-xs text-slate-500 mt-0.5">
                        {rep.allergen_codes?.length} esami · {rep.aggregation?.codes?.length || 0} codici SISS ·{" "}
                        {new Date(rep.created_at).toLocaleString("it-IT")}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <Button size="sm" variant="outline" onClick={() => loadFromHistory(rep)}>
                        <Eye className="h-4 w-4 mr-1.5" /> Carica
                      </Button>
                      <Button size="sm" variant="ghost" className="text-slate-400 hover:text-rose-600" onClick={() => deleteReport(rep.report_id)}>
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </Card>
                  );
                })}
              </div>
                )}
              </div>
            )}
          </TabsContent>

          {user?.role === "admin" && (
            <TabsContent value="config">
              <Tabs defaultValue="catalogo" className="w-full">
                <TabsList className="mb-4">
                  <TabsTrigger value="catalogo" data-testid="subtab-catalogo">Catalogo</TabsTrigger>
                  <TabsTrigger value="profili" data-testid="subtab-profili">Profili</TabsTrigger>
                  <TabsTrigger value="utenti" data-testid="subtab-utenti">Utenti</TabsTrigger>
                  <TabsTrigger value="registro" data-testid="subtab-registro">Registro modifiche</TabsTrigger>
                </TabsList>
                <TabsContent value="catalogo">
                  <AdminAllergens allergens={allergens} onChanged={loadAllergens} />
                </TabsContent>
                <TabsContent value="profili">
                  <AdminProfiles allergens={allergens} profiles={profiles} onChanged={loadProfiles} />
                </TabsContent>
                <TabsContent value="utenti">
                  <AdminUsers currentUser={user} />
                </TabsContent>
                <TabsContent value="registro">
                  <AuditLog />
                </TabsContent>
              </Tabs>
            </TabsContent>
          )}
        </Tabs>
      </main>

      <ReportModal
        open={reportOpen}
        onOpenChange={setReportOpen}
        reportType={workspaceType}
        allergens={workspaceType === "ige" ? allergens : specificIgg}
        selectedCodes={selectedCodes}
        patient={patient}
        doctorName={doctorName}
        aggregation={aggregation}
        onSave={saveReport}
      />
    </div>
  );
}
