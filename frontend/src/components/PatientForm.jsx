import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Card } from "./ui/card";
import { User } from "lucide-react";

export default function PatientForm({ patient, setPatient, doctorName, setDoctorName }) {
  const upd = (k) => (e) => setPatient({ ...patient, [k]: e.target.value });

  return (
    <Card className="p-5 border-slate-200">
      <div className="flex items-center gap-2 mb-4">
        <User className="h-4 w-4 text-sky-600" />
        <h3 className="font-heading font-semibold text-slate-900">Dati Paziente</h3>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="space-y-1.5">
          <Label className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Nome
          </Label>
          <Input
            value={patient.first_name}
            onChange={upd("first_name")}
            placeholder="Mario"
            data-testid="patient-firstname-input"
          />
        </div>
        <div className="space-y-1.5">
          <Label className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Cognome
          </Label>
          <Input
            value={patient.last_name}
            onChange={upd("last_name")}
            placeholder="Rossi"
            data-testid="patient-lastname-input"
          />
        </div>
        <div className="space-y-1.5">
          <Label className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Data di nascita
          </Label>
          <Input
            type="date"
            value={patient.dob}
            onChange={upd("dob")}
            data-testid="patient-dob-input"
          />
        </div>
        <div className="space-y-1.5">
          <Label className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Medico richiedente
          </Label>
          <Input
            value={doctorName}
            onChange={(e) => setDoctorName(e.target.value)}
            placeholder="Dott. …"
            data-testid="doctor-name-input"
          />
        </div>
      </div>
    </Card>
  );
}
