"""Algoritmo di aggregazione codici SISS (Allegato 2)."""
import math

MOLECULAR = "Allergeni molecolari"


def _code(siss_code, description, quantity, items, note=""):
    return {
        "siss_code": siss_code,
        "description": description,
        "quantity": quantity,
        "allergen_count": len(items),
        "allergen_codes": [i["code"] for i in items],
        "note": note,
    }


def _packages(n):
    """QTA' = numero di pacchetti da max 12 (arrotondamento per eccesso, minimo 1)."""
    return max(1, math.ceil(n / 12))


def _molecular_code(mol):
    if not mol:
        return None
    if len(mol) <= 12:
        return _code("009068A", "Allergeni molecolari singoli (max 12)", len(mol), mol,
                     "Numero effettivo di allergeni molecolari (1-12).")
    return _code("009068D", "Allergeni molecolari da 13 in su", 1, mol,
                 "Codice unico per 13+ allergeni molecolari.")


def _inhalant_food_code(inal, alim):
    """Super-gruppo B: Inalanti + Alimenti."""
    if inal and alim:
        items = inal + alim
        return _code("009068B", "Allergeni inalanti e alimenti (max 12 per pacchetto)",
                     _packages(len(items)), items)
    if inal:
        if 5 <= len(inal) <= 8:
            return _code("0090688", "Allergeni inalanti (max 8)", 1, inal)
        return _code("009068B.01", "Allergeni inalanti (max 12 per pacchetto)",
                     _packages(len(inal)), inal)
    if alim:
        if 5 <= len(alim) <= 8:
            return _code("0090687", "Allergeni alimenti (max 8)", 1, alim)
        return _code("009068B.02", "Allergeni alimenti (max 12 per pacchetto)",
                     _packages(len(alim)), alim)
    return None


def _drug_venom_code(farm, vel):
    """Super-gruppo C: Farmaci + Veleni."""
    if farm and vel:
        items = farm + vel
        return _code("009068C", "Allergeni farmaci e veleni (max 12 per pacchetto)",
                     _packages(len(items)), items)
    if vel:
        return _code("009068C.01", "Allergeni veleni (max 12 per pacchetto)",
                     _packages(len(vel)), vel)
    if farm:
        return _code("009068C.02", "Allergeni farmaci (max 12 per pacchetto)",
                     _packages(len(farm)), farm)
    return None


def _standard_codes(total, std, allergens):
    """Codici per gli allergeni non molecolari, in base al conteggio totale."""
    if total < 5:
        if std:
            return [_code("0090681.00", "Allergene singolo (fino a 4)", len(std), std,
                          "Numero effettivo di allergeni non molecolari (1-4).")]
        return []
    if total > 60:
        return [_code("009068D", "Qualsiasi tipo di allergene da 61 in su", 1,
                      std if std else allergens,
                      "Codice unico per richieste da 61 allergeni in su.")]
    # Fascia 5-60: valutazione per tipologia
    cats = {}
    for a in std:
        cats.setdefault(a["type"], []).append(a)
    codes = []
    for maybe in (
        _inhalant_food_code(cats.get("Inalanti", []), cats.get("Alimenti", [])),
        _drug_venom_code(cats.get("Farmaci", []), cats.get("Veleni", [])),
    ):
        if maybe:
            codes.append(maybe)
    return codes


def _merge(results):
    """Unisce codici duplicati (es. 009068D emesso sia dai molecolari che dal totale>60)."""
    merged = {}
    order = []
    for r in results:
        c = r["siss_code"]
        if c not in merged:
            merged[c] = dict(r)
            merged[c]["allergen_codes"] = list(r["allergen_codes"])
            order.append(c)
            continue
        merged[c]["quantity"] = 1 if c == "009068D" else merged[c]["quantity"] + r["quantity"]
        existing = set(merged[c]["allergen_codes"])
        for code in r["allergen_codes"]:
            if code not in existing:
                merged[c]["allergen_codes"].append(code)
                existing.add(code)
        merged[c]["allergen_count"] = len(merged[c]["allergen_codes"])
    return [merged[c] for c in order]


def aggregate(allergens):
    """allergens: list of dicts with at least 'code' and 'type'."""
    total = len(allergens)
    mol = [a for a in allergens if a.get("type") == MOLECULAR]
    std = [a for a in allergens if a.get("type") != MOLECULAR]

    results = []
    mol_code = _molecular_code(mol)
    if mol_code:
        results.append(mol_code)
    results.extend(_standard_codes(total, std, allergens))

    return {
        "total": total,
        "molecular_count": len(mol),
        "standard_count": len(std),
        "codes": _merge(results),
    }
