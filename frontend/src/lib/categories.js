import { Apple, Wind, Pill, Bug, Dna } from "lucide-react";

export const CATEGORIES = {
  Alimenti: {
    label: "Alimenti",
    icon: Apple,
    pill: "bg-amber-50 text-amber-800 border-amber-200",
    dot: "bg-amber-500",
    active: "bg-amber-500 text-white border-amber-500",
  },
  Inalanti: {
    label: "Inalanti",
    icon: Wind,
    pill: "bg-sky-50 text-sky-800 border-sky-200",
    dot: "bg-sky-500",
    active: "bg-sky-600 text-white border-sky-600",
  },
  Farmaci: {
    label: "Farmaci",
    icon: Pill,
    pill: "bg-emerald-50 text-emerald-800 border-emerald-200",
    dot: "bg-emerald-500",
    active: "bg-emerald-600 text-white border-emerald-600",
  },
  Veleni: {
    label: "Veleni",
    icon: Bug,
    pill: "bg-rose-50 text-rose-800 border-rose-200",
    dot: "bg-rose-500",
    active: "bg-rose-600 text-white border-rose-600",
  },
  "Allergeni molecolari": {
    label: "Molecolari",
    icon: Dna,
    pill: "bg-indigo-50 text-indigo-800 border-indigo-200",
    dot: "bg-indigo-500",
    active: "bg-indigo-600 text-white border-indigo-600",
  },
};

export const CATEGORY_ORDER = [
  "Alimenti",
  "Inalanti",
  "Farmaci",
  "Veleni",
  "Allergeni molecolari",
];
