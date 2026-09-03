import { useEffect, useState, useCallback } from "react";
import { toast } from "sonner";
import { Users, Shield, ShieldOff, RefreshCw } from "lucide-react";
import { Card } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import api, { formatApiErrorDetail } from "../lib/api";

export default function AdminUsers({ currentUser }) {
  const [users, setUsers] = useState([]);
  const [busy, setBusy] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    api.get("/admin/users")
      .then((r) => setUsers(r.data))
      .catch(() => toast.error("Errore caricamento utenti"))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const changeRole = async (u, role) => {
    setBusy(u.user_id);
    try {
      await api.put(`/admin/users/${u.user_id}/role`, { role });
      toast.success(role === "admin" ? `${u.name} promosso ad amministratore` : `${u.name} rimosso dagli amministratori`);
      load();
    } catch (err) {
      toast.error(formatApiErrorDetail(err.response?.data?.detail) || err.message);
    } finally {
      setBusy(null);
    }
  };

  return (
    <Card className="p-5 border-slate-200">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Users className="h-4 w-4 text-sky-600" />
          <h3 className="font-heading font-semibold text-slate-900">Utenti & ruoli</h3>
          <Badge variant="secondary" data-testid="admin-users-count">{users.length}</Badge>
        </div>
        <Button size="sm" variant="outline" onClick={load} data-testid="admin-users-refresh">
          <RefreshCw className="h-4 w-4 mr-1.5" /> Aggiorna
        </Button>
      </div>

      <div className="rounded-lg border border-slate-200 overflow-hidden">
        <div className="max-h-[58vh] overflow-y-auto divide-y divide-slate-50">
          {users.map((u) => {
            const isSelf = u.user_id === currentUser?.user_id;
            const isAdmin = u.role === "admin";
            return (
              <div key={u.user_id} data-testid={`admin-user-row-${u.email}`} className="flex items-center gap-3 px-3 py-2.5 hover:bg-slate-50">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-medium text-slate-800 truncate">{u.name || u.email}</p>
                    <Badge className={isAdmin ? "bg-sky-600 hover:bg-sky-600" : ""} variant={isAdmin ? "default" : "secondary"} data-testid={`admin-user-role-${u.email}`}>
                      {isAdmin ? "Admin" : "Operatore"}
                    </Badge>
                    {u.auth_provider === "google" && (
                      <span className="text-[10px] text-slate-400 border border-slate-200 rounded px-1.5 py-0.5">Google</span>
                    )}
                  </div>
                  <p className="text-xs text-slate-500 truncate">{u.email}</p>
                </div>
                {isSelf ? (
                  <span className="text-xs text-slate-400 italic pr-2">tu</span>
                ) : isAdmin ? (
                  <Button size="sm" variant="outline" disabled={busy === u.user_id} onClick={() => changeRole(u, "user")} data-testid={`admin-demote-${u.email}`} className="text-rose-600 hover:text-rose-700">
                    <ShieldOff className="h-4 w-4 mr-1.5" /> Rimuovi admin
                  </Button>
                ) : (
                  <Button size="sm" disabled={busy === u.user_id} onClick={() => changeRole(u, "admin")} data-testid={`admin-promote-${u.email}`} className="bg-sky-600 hover:bg-sky-700">
                    <Shield className="h-4 w-4 mr-1.5" /> Promuovi ad admin
                  </Button>
                )}
              </div>
            );
          })}
          {!users.length && <p className="p-8 text-center text-sm text-slate-400">{loading ? "Caricamento…" : "Nessun utente"}</p>}
        </div>
      </div>
    </Card>
  );
}
