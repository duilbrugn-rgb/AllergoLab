import { useEffect, useState, useRef, useCallback } from "react";
import { toast } from "sonner";
import { FileText, ClipboardList, History, Trash2, Eye, Settings } from "lucide-react";
import Header from "../components/Header";
import PatientForm from "../components/PatientForm";
import DualList from "../components/DualList";
import SissSummary from "../components/SissSummary";
import ReportModal from "../components/ReportModal";
import AdminAllergens from "../components/AdminAllergens";
import { Button } from "../components/ui/button";
import { Card } from "../components/ui/card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "../components/ui/tabs";
import api from "../lib/api";
import { useAuth } from "../context/AuthContext";

export default function AppPage() {
  const { user } = useAuth();
  const [allergens, setAllergens] = useState([]);
  const [selectedCodes, setSelectedCodes] = useState([]);
  const [patient, setPatient] = useState({ first_name: "", last_name: "", dob: "" });
  const [doctorName, setDoctorName] = useState(user?.name || "");
  const [aggregation, setAggregation] = useState({ codes: [], total: 0, molecular_count: 0, standard_count: 0 });
  const [reportOpen, setReportOpen] = useState(false);
  const [history, setHistory] = useState([]);
  const debounceRef = useRef(null);

  const loadAllergens = useCallback(() => {
    api.get("/allergens").then((r) => setAllergens(r.data)).catch(() => toast.error("Errore caricamento allergeni"));
  }, []);

  const loadHistory = useCallback(() => {
    api.get("/reports").then((r) => setHistory(r.data)).catch(() => {});
  }, []);

  useEffect(() => {
    loadAllergens();
    loadHistory();
  }, [loadAllergens, loadHistory]);

  useEffect(() => {
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
  }, [selectedCodes]);

  const saveReport = async (overrides) => {
    try {
      await api.post("/reports", {
        patient: overrides?.patient || patient,
        doctor_name: overrides?.doctor_name || doctorName,
        allergen_codes: selectedCodes,
        notes: overrides?.notes || "",
        letterhead: overrides?.letterhead || "",
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
    setSelectedCodes(rep.allergen_codes || []);
    setPatient(rep.patient || { first_name: "", last_name: "", dob: "" });
    setDoctorName(rep.doctor_name || doctorName);
    toast.success("Report caricato nell'editor");
  };

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

            <DualList allergens={allergens} selectedCodes={selectedCodes} setSelectedCodes={setSelectedCodes} />

            <SissSummary aggregation={aggregation} />

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
              <div className="grid gap-3">
                {history.map((rep) => (
                  <Card key={rep.report_id} className="p-4 flex items-center justify-between" data-testid={`history-item-${rep.report_id}`}>
                    <div>
                      <p className="font-medium text-slate-900">
                        {rep.patient?.first_name} {rep.patient?.last_name || "— Paziente"}
                      </p>
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
                ))}
              </div>
            )}
          </TabsContent>

          {user?.role === "admin" && (
            <TabsContent value="config">
              <AdminAllergens allergens={allergens} onChanged={loadAllergens} />
            </TabsContent>
          )}
        </Tabs>
      </main>

      <ReportModal
        open={reportOpen}
        onOpenChange={setReportOpen}
        allergens={allergens}
        selectedCodes={selectedCodes}
        patient={patient}
        doctorName={doctorName}
        aggregation={aggregation}
        onSave={saveReport}
      />
    </div>
  );
}
