export const REPORT_TYPES = {
  ige: {
    id: "ige",
    label: "IgE",
    titleLines: ["ALLERGENI", "PER DETERMINAZIONE"],
    subtitle: "IgE SPECIFICHE (RAST)",
    modulo: "MODULO",
    formCode: "Mod-LABCENT13.08.01.01",
    revision: "00",
    date: "04/09/2026",
    codeField: "code",
    groupByCategory: true,
  },
  igg: {
    id: "igg",
    label: "IgG",
    titleLines: ["MODULO DI", "RICHIESTA"],
    subtitle: "IgG SPECIFICHE",
    modulo: "MODULO",
    formCode: "Mod-LABCENT13.08.01.02",
    revision: "00",
    date: "01/09/2026",
    codeField: "dnlab_code",
    groupByCategory: false,
  },
};

export function getReportTypeConfig(reportType) {
  return REPORT_TYPES[reportType] || REPORT_TYPES.ige;
}
