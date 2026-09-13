import { buildReportPdfFilename, buildReportPdfSignature, sanitizePdfFilenamePart } from "./reportPdf";
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

  test("PDF signature uses only local patient state and no doctor name", () => {
    const signature = buildReportPdfSignature({
      reportType: "ige",
      patient: { first_name: "Mario", last_name: "Rossi", dob: "1990-01-01" },
      notes: "note locali",
      selectedCodes: ["f1"],
      aggregation: { total: 1, codes: [{ siss_code: "0090681.00", description: "x", quantity: 1 }] },
    });
    const parsed = JSON.parse(signature);
    expect(parsed.patient).toEqual({
      first_name: "Mario",
      last_name: "Rossi",
      dob: "1990-01-01",
    });
    expect(parsed.notes).toBe("note locali");
    expect(parsed).not.toHaveProperty("doctorName");
    expect(parsed).not.toHaveProperty("letterhead");
  });
});
