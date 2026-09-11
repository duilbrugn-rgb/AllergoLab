import { getReportTypeConfig } from "./reportTypes";

export function sanitizePdfFilenamePart(value) {
  const cleaned = String(value || "")
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[\\/:*?"<>|\s]+/g, "_")
    .replace(/[^A-Za-z0-9._-]+/g, "_")
    .replace(/_+/g, "_")
    .replace(/^_+|_+$/g, "");
  return cleaned.slice(0, 40);
}

export function formatPdfDate(date = new Date()) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

export function buildReportPdfFilename({ reportType, patient, date = new Date() }) {
  const cfg = getReportTypeConfig(reportType);
  const label = cfg.label || "IgE";
  const last = sanitizePdfFilenamePart(patient?.last_name) || "Paziente";
  const first = sanitizePdfFilenamePart(patient?.first_name);
  const who = first ? `${last}_${first}` : last;
  return `AllergoLab_${label}_${who}_${formatPdfDate(date)}.pdf`;
}

export function getReportPdfLogoSrc() {
  if (typeof window === "undefined") return "/logo-asst.png";
  const base = (process.env.PUBLIC_URL || "").replace(/\/$/, "");
  return `${window.location.origin}${base}/logo-asst.png`;
}

export function buildReportPdfSignature({
  reportType,
  patient,
  doctorName,
  notes,
  letterhead,
  selectedCodes,
  aggregation,
}) {
  return JSON.stringify({
    reportType: reportType || "ige",
    patient: {
      first_name: patient?.first_name || "",
      last_name: patient?.last_name || "",
      dob: patient?.dob || "",
    },
    doctorName: doctorName || "",
    notes: notes || "",
    letterhead: letterhead || "",
    selectedCodes: [...(selectedCodes || [])],
    aggregation: aggregation
      ? {
          total: aggregation.total ?? 0,
          codes: (aggregation.codes || []).map((c) => ({
            siss_code: c.siss_code,
            description: c.description,
            quantity: c.quantity,
          })),
        }
      : null,
  });
}
