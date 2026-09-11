export const IGG_SISS_CODE = "0090685";
export const IGG_SISS_DESCRIPTION = "IGG SPECIFICHE ALLERGOLOGICHE";
export const IGG_MAX_PER_RECIPE = 8;

export function buildIggPrestazioni(count) {
  const n = Number(count) || 0;
  if (n <= 0) {
    return { total: 0, codes: [] };
  }
  return {
    total: n,
    codes: [
      {
        siss_code: IGG_SISS_CODE,
        description: IGG_SISS_DESCRIPTION,
        quantity: n,
      },
    ],
  };
}

export function iggRecipeCount(count) {
  const n = Number(count) || 0;
  if (n <= 0) return 0;
  return Math.ceil(n / IGG_MAX_PER_RECIPE);
}
