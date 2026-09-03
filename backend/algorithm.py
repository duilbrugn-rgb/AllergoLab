"""Algoritmo di aggregazione codici SISS (Allegato 2)."""
import math

MOLECULAR = "Allergeni molecolari"


def aggregate(allergens):
    """allergens: list of dicts with at least 'code' and 'type'."""
    total = len(allergens)
    mol = [a for a in allergens if a.get("type") == MOLECULAR]
    std = [a for a in allergens if a.get("type") != MOLECULAR]
    n_mol = len(mol)
    n_std = len(std)

    results = []

    def add(code, description, quantity, items, note=""):
        results.append({
            "siss_code": code,
            "description": description,
            "quantity": quantity,
            "allergen_count": len(items),
            "allergen_codes": [i["code"] for i in items],
            "note": note,
        })

    # --- Conteggio allergeni molecolari (sempre, se presenti) ---
    if n_mol >= 1:
        if n_mol <= 12:
            add("009068A", "Allergeni molecolari singoli (max 12)", n_mol, mol,
                "Numero effettivo di allergeni molecolari (1-12).")
        else:
            add("009068D", "Allergeni molecolari da 13 in su", 1, mol,
                "Codice unico per 13+ allergeni molecolari.")

    # --- Conteggio totale (include tutte le tipologie) ---
    if total < 5:
        if n_std >= 1:
            add("0090681.00", "Allergene singolo (fino a 4)", n_std, std,
                "Numero effettivo di allergeni non molecolari (1-4).")
    elif total > 60:
        add("009068D", "Qualsiasi tipo di allergene da 61 in su", 1,
            std if std else allergens, "Codice unico per richieste da 61 allergeni in su.")
    else:
        # 5 <= total <= 60: valutazione per tipologia sui non-molecolari
        cats = {}
        for a in std:
            cats.setdefault(a["type"], []).append(a)
        inal = cats.get("Inalanti", [])
        alim = cats.get("Alimenti", [])
        farm = cats.get("Farmaci", [])
        vel = cats.get("Veleni", [])

        # Super-gruppo B: Inalanti + Alimenti
        if inal and alim:
            items = inal + alim
            add("009068B", "Allergeni inalanti e alimenti (max 12 per pacchetto)",
                math.ceil(len(items) / 12), items)
        elif inal:
            n = len(inal)
            if 5 <= n <= 8:
                add("0090688", "Allergeni inalanti (max 8)", 1, inal)
            else:
                add("009068B.01", "Allergeni inalanti (max 12 per pacchetto)",
                    max(1, math.ceil(n / 12)), inal)
        elif alim:
            n = len(alim)
            if 5 <= n <= 8:
                add("0090687", "Allergeni alimenti (max 8)", 1, alim)
            else:
                add("009068B.02", "Allergeni alimenti (max 12 per pacchetto)",
                    max(1, math.ceil(n / 12)), alim)

        # Super-gruppo C: Farmaci + Veleni
        if farm and vel:
            items = farm + vel
            add("009068C", "Allergeni farmaci e veleni (max 12 per pacchetto)",
                math.ceil(len(items) / 12), items)
        elif vel:
            add("009068C.01", "Allergeni veleni (max 12 per pacchetto)",
                max(1, math.ceil(len(vel) / 12)), vel)
        elif farm:
            add("009068C.02", "Allergeni farmaci (max 12 per pacchetto)",
                max(1, math.ceil(len(farm) / 12)), farm)

    # --- Merge duplicati (es. 009068D emesso due volte) ---
    merged = {}
    order = []
    for r in results:
        c = r["siss_code"]
        if c in merged:
            if c == "009068D":
                merged[c]["quantity"] = 1
            else:
                merged[c]["quantity"] += r["quantity"]
            existing = set(merged[c]["allergen_codes"])
            for code in r["allergen_codes"]:
                if code not in existing:
                    merged[c]["allergen_codes"].append(code)
                    existing.add(code)
            merged[c]["allergen_count"] = len(merged[c]["allergen_codes"])
        else:
            merged[c] = dict(r)
            merged[c]["allergen_codes"] = list(r["allergen_codes"])
            order.append(c)

    final = [merged[c] for c in order]
    return {
        "total": total,
        "molecular_count": n_mol,
        "standard_count": n_std,
        "codes": final,
    }
