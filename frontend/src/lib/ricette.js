// Distribuisce i codici SISS su ricette con al massimo `maxPerRicetta` prestazioni ciascuna
export function distribuisciRicette(codes, maxPerRicetta = 8) {
  const ricette = [];
  let current = [];
  let cap = maxPerRicetta;
  for (const c of codes) {
    let q = c.quantity;
    while (q > 0) {
      const take = Math.min(q, cap);
      current.push({ siss_code: c.siss_code, description: c.description, quantity: take });
      cap -= take;
      q -= take;
      if (cap === 0) {
        ricette.push(current);
        current = [];
        cap = maxPerRicetta;
      }
    }
  }
  if (current.length) ricette.push(current);
  return ricette;
}
