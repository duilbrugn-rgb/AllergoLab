import { applyPrescriptionReset, createEmptyPrescriptionState, EMPTY_PATIENT } from "./prescription";

describe("resetPrescription", () => {
  test("createEmptyPrescriptionState azzera i dati della prescrizione corrente", () => {
    const next = createEmptyPrescriptionState("ige");
    expect(next.patient).toEqual(EMPTY_PATIENT);
    expect(next.notes).toBe("");
    expect(next.selectedCodes).toEqual([]);
    expect(next.aggregation).toEqual({
      codes: [],
      total: 0,
      molecular_count: 0,
      standard_count: 0,
    });
    expect(next.reportOpen).toBe(false);
  });

  test("applyPrescriptionReset elimina paziente, note, esami e PDF aperto", () => {
    const setters = {
      setPatient: jest.fn(),
      setNotes: jest.fn(),
      setSelectedCodes: jest.fn(),
      setAggregation: jest.fn(),
      setReportOpen: jest.fn(),
    };
    applyPrescriptionReset(setters, "igg");
    expect(setters.setPatient).toHaveBeenCalledWith({ first_name: "", last_name: "", dob: "" });
    expect(setters.setNotes).toHaveBeenCalledWith("");
    expect(setters.setSelectedCodes).toHaveBeenCalledWith([]);
    expect(setters.setAggregation).toHaveBeenCalledWith({ total: 0, codes: [] });
    expect(setters.setReportOpen).toHaveBeenCalledWith(false);
  });
});
