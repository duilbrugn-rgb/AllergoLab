import { useEffect, useState, useRef, useCallback } from "react";
import { toast } from "sonner";
import { FileText, ClipboardList, Settings, Plus } from "lucide-react";
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
import { applyPrescriptionReset, emptyAggregation } from "../lib/prescription";

export default function AppPage() {
  const { user, logout } = useAuth();
  const [allergens, setAllergens] = useState([]);
  const [specificIgg, setSpecificIgg] = useState([]);
  const [profiles, setProfiles] = useState([]);
  const [workspaceType, setWorkspaceType] = useState("ige");
  const [selectedCodes, setSelectedCodes] = useState([]);
  const [patient, setPatient] = useState({ first_name: "", last_name: "", dob: "" });
  const [notes, setNotes] = useState("");
  const [aggregation, setAggregation] = useState(emptyAggregation("ige"));
  const [reportOpen, setReportOpen] = useState(false);
  const [prescriptionKey, setPrescriptionKey] = useState(0);
  const debounceRef = useRef(null);
  const aggregationVersionRef = useRef(0);

  const loadAllergens = useCallback(() => {
    api.get("/allergens").then((r) => setAllergens(r.data)).catch(() => toast.error("Errore caricamento allergeni"));
  }, []);

  const loadSpecificIgg = useCallback(() => {
    api.get("/specific-igg").then((r) => setSpecificIgg(r.data)).catch(() => toast.error("Errore caricamento IgG specifiche"));
  }, []);

  const loadProfiles = useCallback(() => {
    api.get("/profiles").then((r) => setProfiles(r.data)).catch(() => {});
  }, []);

  useEffect(() => {
    loadAllergens();
    loadSpecificIgg();
    loadProfiles();
  }, [loadAllergens, loadSpecificIgg, loadProfiles]);

  useEffect(() => {
    const version = ++aggregationVersionRef.current;
    let active = true;

    if (debounceRef.current) clearTimeout(debounceRef.current);

    if (workspaceType === "igg") {
      setAggregation(buildIggPrestazioni(selectedCodes.length));
    } else {
      setAggregation(emptyAggregation("ige"));
      if (selectedCodes.length) {
        debounceRef.current = setTimeout(() => {
          api.post("/aggregate", { codes: selectedCodes })
            .then((r) => {
              if (active && version === aggregationVersionRef.current) {
                setAggregation(r.data);
              }
            })
            .catch(() => {});
        }, 250);
      }
    }

    return () => {
      active = false;
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [selectedCodes, workspaceType]);

  const resetPrescription = useCallback(() => {
    aggregationVersionRef.current += 1;
    if (debounceRef.current) clearTimeout(debounceRef.current);
    applyPrescriptionReset(
      { setPatient, setNotes, setSelectedCodes, setAggregation, setReportOpen },
      workspaceType
    );
    setPrescriptionKey((k) => k + 1);
  }, [workspaceType]);

  const handleLogout = async () => {
    resetPrescription();
    await logout();
  };

  const switchWorkspace = (type) => {
    if (type === workspaceType) return;
    aggregationVersionRef.current += 1;
    if (debounceRef.current) clearTimeout(debounceRef.current);
    setWorkspaceType(type);
    setSelectedCodes([]);
    setAggregation(emptyAggregation(type));
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <Header onLogout={handleLogout} />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <Tabs defaultValue="nuovo" className="w-full">
          <TabsList className="mb-6">
            <TabsTrigger value="nuovo" data-testid="tab-nuovo-report">
              <ClipboardList className="h-4 w-4 mr-1.5" /> Nuovo Report
            </TabsTrigger>
            {user?.role === "admin" && (
              <TabsTrigger value="config" data-testid="tab-config">
                <Settings className="h-4 w-4 mr-1.5" /> Configurazione
              </TabsTrigger>
            )}
          </TabsList>

          <TabsContent value="nuovo" className="space-y-6">
            <div className="flex justify-end">
              <Button
                size="sm"
                variant="outline"
                onClick={resetPrescription}
                data-testid="btn-new-prescription"
              >
                <Plus className="h-4 w-4 mr-1.5" />
                Nuova prescrizione
              </Button>
            </div>

            <PatientForm patient={patient} setPatient={setPatient} />

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
        key={prescriptionKey}
        open={reportOpen}
        onOpenChange={setReportOpen}
        reportType={workspaceType}
        allergens={workspaceType === "ige" ? allergens : specificIgg}
        selectedCodes={selectedCodes}
        patient={patient}
        setPatient={setPatient}
        notes={notes}
        setNotes={setNotes}
        aggregation={aggregation}
      />
    </div>
  );
}
