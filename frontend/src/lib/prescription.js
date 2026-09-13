import { buildIggPrestazioni } from "./iggPrestazioni";

export const EMPTY_PATIENT = { first_name: "", last_name: "", dob: "" };
export const EMPTY_IGE_AGGREGATION = {
  codes: [],
  total: 0,
  molecular_count: 0,
  standard_count: 0,
};

export function emptyAggregation(workspaceType) {
  return workspaceType === "igg"
    ? buildIggPrestazioni(0)
    : { ...EMPTY_IGE_AGGREGATION };
}

export function createEmptyPrescriptionState(workspaceType = "ige") {
  return {
    patient: { ...EMPTY_PATIENT },
    notes: "",
    selectedCodes: [],
    aggregation: emptyAggregation(workspaceType),
    reportOpen: false,
  };
}

export function applyPrescriptionReset(setters, workspaceType = "ige") {
  const next = createEmptyPrescriptionState(workspaceType);
  setters.setPatient(next.patient);
  setters.setNotes(next.notes);
  setters.setSelectedCodes(next.selectedCodes);
  setters.setAggregation(next.aggregation);
  if (setters.setReportOpen) setters.setReportOpen(next.reportOpen);
  return next;
}
