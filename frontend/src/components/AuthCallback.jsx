import { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { FlaskConical } from "lucide-react";
import api from "../lib/api";
import { useAuth } from "../context/AuthContext";

export default function AuthCallback() {
  const navigate = useNavigate();
  const { setUser } = useAuth();
  const hasProcessed = useRef(false);

  useEffect(() => {
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const hash = window.location.hash || "";
    const match = hash.match(/session_id=([^&]+)/);
    const sessionId = match ? decodeURIComponent(match[1]) : null;

    const run = async () => {
      if (!sessionId) {
        navigate("/", { replace: true });
        return;
      }
      try {
        const { data } = await api.post(
          "/auth/google/session",
          {},
          { headers: { "X-Session-ID": sessionId } }
        );
        setUser(data);
        window.history.replaceState(null, "", window.location.pathname);
        navigate("/app", { replace: true });
      } catch {
        navigate("/", { replace: true });
      }
    };
    run();
  }, [navigate, setUser]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50">
      <FlaskConical className="h-10 w-10 text-sky-600 animate-pulse" />
      <p className="mt-4 text-slate-600 text-sm">Accesso in corso…</p>
    </div>
  );
}
