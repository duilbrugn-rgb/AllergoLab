import { distribuisciRicette } from "./ricette";
import { buildIggPrestazioni } from "./iggPrestazioni";

describe("distribuzione ricette IgG", () => {
  test("9 IgG producono 2 ricette 8+1", () => {
    const aggregation = buildIggPrestazioni(9);
    expect(aggregation.total).toBe(9);
    expect(aggregation.codes[0].siss_code).toBe("0090685");
    expect(aggregation.codes[0].quantity).toBe(9);
    const ricette = distribuisciRicette(aggregation.codes);
    expect(ricette).toHaveLength(2);
    expect(ricette[0]).toEqual([
      { siss_code: "0090685", description: "IGG SPECIFICHE ALLERGOLOGICHE", quantity: 8 },
    ]);
    expect(ricette[1]).toEqual([
      { siss_code: "0090685", description: "IGG SPECIFICHE ALLERGOLOGICHE", quantity: 1 },
    ]);
  });

  test("8 IgG producono 1 ricetta da 8", () => {
    const ricette = distribuisciRicette(buildIggPrestazioni(8).codes);
    expect(ricette).toHaveLength(1);
    expect(ricette[0][0].quantity).toBe(8);
  });
});
