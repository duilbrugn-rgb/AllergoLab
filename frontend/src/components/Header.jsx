import { FlaskConical, LogOut } from "lucide-react";
import { Button } from "./ui/button";
import { useAuth } from "../context/AuthContext";

export default function Header() {
  const { user, logout } = useAuth();
  const initials = (user?.name || user?.email || "?")
    .split(" ")
    .map((s) => s[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  return (
    <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/90 backdrop-blur-md no-print">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-sky-600 flex items-center justify-center shadow-sm">
            <FlaskConical className="h-5 w-5 text-white" />
          </div>
          <div className="leading-tight">
            <h1 className="font-heading text-lg font-bold tracking-tight text-slate-900">
              AllergoLab
            </h1>
            <p className="text-[11px] text-slate-500 -mt-0.5">
              Selezione allergeni & codici SISS
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden sm:flex flex-col items-end leading-tight" data-testid="header-doctor">
            <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold">
              Medico richiedente
            </span>
            <span className="text-sm font-medium text-slate-800">
              {user?.name || user?.email}
            </span>
          </div>
          <div className="h-9 w-9 rounded-full bg-slate-800 text-white flex items-center justify-center text-xs font-semibold">
            {initials}
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={logout}
            data-testid="logout-button"
            className="text-slate-600 hover:text-rose-600"
          >
            <LogOut className="h-4 w-4 sm:mr-1.5" />
            <span className="hidden sm:inline">Esci</span>
          </Button>
        </div>
      </div>
    </header>
  );
}
