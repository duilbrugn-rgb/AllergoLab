import { buildReportPdfFilename, sanitizePdfFilenamePart } from "./reportPdf";
import { getReportTypeConfig } from "./reportTypes";

describe("report PDF helpers", () => {
  test("builds IgE filename", () => {
    const name = buildReportPdfFilename({
      reportType: "ige",
      patient: { first_name: "Mario", last_name: "Rossi" },
      date: new Date(2026, 8, 10),
    });
    expect(name).toBe("AllergoLab_IgE_Rossi_Mario_2026-09-10.pdf");
  });

  test("builds IgG filename and sanitizes invalid chars", () => {
    const name = buildReportPdfFilename({
      reportType: "igg",
      patient: { first_name: "Mario", last_name: "Ro/ssi*" },
      date: new Date(2026, 8, 10),
    });
    expect(name).toBe("AllergoLab_IgG_Ro_ssi_Mario_2026-09-10.pdf");
    expect(sanitizePdfFilenamePart("a/b c")).toBe("a_b_c");
  });

  test("IgG config uses dnlab_code", () => {
    const cfg = getReportTypeConfig("igg");
    expect(cfg.codeField).toBe("dnlab_code");
    expect(cfg.formCode).toBe("Mod-LABCENT13.08.01.02");
  });

  test("IgE config uses code and grouping", () => {
    const cfg = getReportTypeConfig("ige");
    expect(cfg.codeField).toBe("code");
    expect(cfg.groupByCategory).toBe(true);
  });
});
