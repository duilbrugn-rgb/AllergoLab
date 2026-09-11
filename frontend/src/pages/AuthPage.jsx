import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { FlaskConical, Mail, Lock, UserRound } from "lucide-react";
import { toast } from "sonner";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "../components/ui/tabs";
import api, { formatApiErrorDetail } from "../lib/api";
import { useAuth } from "../context/AuthContext";

export default function AuthPage() {
  const navigate = useNavigate();
  const { setUser } = useAuth();
  const [loading, setLoading] = useState(false);
  const googleButtonRef = useRef(null);
  const [login, setLogin] = useState({ email: "", password: "" });
  const [reg, setReg] = useState({ first_name: "", last_name: "", email: "", password: "" });

  useEffect(() => {
    const clientId = process.env.REACT_APP_GOOGLE_CLIENT_ID;
  
    if (!clientId) {
      console.error("REACT_APP_GOOGLE_CLIENT_ID non configurato");
      return;
    }
  
    const initializeGoogle = () => {
      if (!window.google?.accounts?.id || !googleButtonRef.current) {
        return;
      }
  
      window.google.accounts.id.initialize({
        client_id: clientId,
        callback: async (response) => {
          try {
            setLoading(true);
  
            const { data } = await api.post("/auth/google", {
              credential: response.credential,
            });
  
            setUser(data);
            navigate("/app", { replace: true });
          } catch (err) {
            toast.error(
              formatApiErrorDetail(err.response?.data?.detail) ||
                "Accesso con Google non riuscito"
            );
          } finally {
            setLoading(false);
          }
        },
      });
  
      googleButtonRef.current.innerHTML = "";
  
      window.google.accounts.id.renderButton(
        googleButtonRef.current,
        {
          type: "standard",
          theme: "outline",
          size: "large",
          text: "continue_with",
          shape: "rectangular",
          logo_alignment: "left",
          width: 400,
        }
      );
    };
  
    if (window.google?.accounts?.id) {
      initializeGoogle();
      return;
    }
  
    const existingScript = document.querySelector(
      'script[src="https://accounts.google.com/gsi/client"]'
    );
  
    if (existingScript) {
      existingScript.addEventListener("load", initializeGoogle);
      return () => {
        existingScript.removeEventListener("load", initializeGoogle);
      };
    }
  
    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    script.onload = initializeGoogle;
  
    document.head.appendChild(script);
  
    return () => {
      script.onload = null;
    };
  }, [navigate, setUser]);

  const doLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const { data } = await api.post("/auth/login", login);
      setUser(data);
      navigate("/app", { replace: true });
    } catch (err) {
      toast.error(formatApiErrorDetail(err.response?.data?.detail) || err.message);
    } finally {
      setLoading(false);
    }
  };

  const doRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const { data } = await api.post("/auth/register", reg);
      setUser(data);
      navigate("/app", { replace: true });
    } catch (err) {
      toast.error(formatApiErrorDetail(err.response?.data?.detail) || err.message);
    } finally {
      setLoading(false);
    }
  };

  
  return (
    <div className="min-h-screen grid lg:grid-cols-2 bg-slate-50">
      {/* Left brand panel */}
      <div className="relative hidden lg:flex flex-col justify-between p-12 bg-slate-900 text-white overflow-hidden">
        <div
          className="absolute inset-0 opacity-25"
          style={{
            backgroundImage:
              "url('https://images.unsplash.com/photo-1582560475093-ba66accbc424?crop=entropy&cs=srgb&fm=jpg&q=85&w=1200')",
            backgroundSize: "cover",
            backgroundPosition: "center",
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-t from-slate-900 via-slate-900/70 to-slate-900/40" />
        <div className="relative flex items-center gap-3">
          <div className="h-11 w-11 rounded-xl bg-sky-500 flex items-center justify-center">
            <FlaskConical className="h-6 w-6 text-white" />
          </div>
          <span className="font-heading text-2xl font-bold">AllergoLab</span>
        </div>
        <div className="relative max-w-md">
          <h2 className="font-heading text-3xl font-bold leading-tight">
            Dalla selezione degli allergeni alla ricetta corretta.
          </h2>
          <p className="mt-4 text-slate-300 text-sm leading-relaxed">
            Componi il pannello di esami, lascia che l'algoritmo attribuisca i codici SISS
            e la quantità corretta, e stampa il promemoria per il paziente.
          </p>
        </div>
        <div className="relative text-xs text-slate-400">
          Codici SISS · Aggregazione automatica · Report stampabile
        </div>
      </div>

      {/* Right form panel */}
      <div className="flex items-center justify-center p-6">
        <div className="w-full max-w-md">
          <div className="lg:hidden flex items-center gap-2 mb-8 justify-center">
            <div className="h-10 w-10 rounded-xl bg-sky-600 flex items-center justify-center">
              <FlaskConical className="h-5 w-5 text-white" />
            </div>
            <span className="font-heading text-xl font-bold text-slate-900">AllergoLab</span>
          </div>

          <Tabs defaultValue="login" className="w-full">
            <TabsList className="grid grid-cols-2 w-full mb-6">
              <TabsTrigger value="login" data-testid="tab-login">Accedi</TabsTrigger>
              <TabsTrigger value="register" data-testid="tab-register">Registrati</TabsTrigger>
            </TabsList>

            <TabsContent value="login">
              <form onSubmit={doLogin} className="space-y-4">
                <div className="space-y-1.5">
                  <Label>Email</Label>
                  <div className="relative">
                    <Mail className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-400" />
                    <Input type="email" required value={login.email} onChange={(e) => setLogin({ ...login, email: e.target.value })} className="pl-8" placeholder="nome@studio.it" data-testid="login-email-input" />
                  </div>
                </div>
                <div className="space-y-1.5">
                  <Label>Password</Label>
                  <div className="relative">
                    <Lock className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-400" />
                    <Input type="password" required value={login.password} onChange={(e) => setLogin({ ...login, password: e.target.value })} className="pl-8" placeholder="••••••••" data-testid="login-password-input" />
                  </div>
                </div>
                <Button type="submit" disabled={loading} className="w-full bg-sky-600 hover:bg-sky-700" data-testid="login-submit-button">
                  {loading ? "Accesso…" : "Accedi"}
                </Button>
              </form>
            </TabsContent>

            <TabsContent value="register">
              <form onSubmit={doRegister} className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1.5">
                    <Label>Nome</Label>
                    <Input required value={reg.first_name} onChange={(e) => setReg({ ...reg, first_name: e.target.value })} placeholder="Mario" data-testid="register-firstname-input" />
                  </div>
                  <div className="space-y-1.5">
                    <Label>Cognome</Label>
                    <Input required value={reg.last_name} onChange={(e) => setReg({ ...reg, last_name: e.target.value })} placeholder="Rossi" data-testid="register-lastname-input" />
                  </div>
                </div>
                <div className="space-y-1.5">
                  <Label>Email</Label>
                  <Input type="email" required value={reg.email} onChange={(e) => setReg({ ...reg, email: e.target.value })} placeholder="nome@studio.it" data-testid="register-email-input" />
                </div>
                <div className="space-y-1.5">
                  <Label>Password</Label>
                  <Input type="password" required minLength={6} value={reg.password} onChange={(e) => setReg({ ...reg, password: e.target.value })} placeholder="min. 6 caratteri" data-testid="register-password-input" />
                </div>
                <p className="flex items-start gap-1.5 text-xs text-slate-500">
                  <UserRound className="h-3.5 w-3.5 mt-0.5 shrink-0" />
                  Nome e Cognome verranno usati come <strong className="mx-1">Medico richiedente</strong> nei report.
                </p>
                <Button type="submit" disabled={loading} className="w-full bg-sky-600 hover:bg-sky-700" data-testid="register-submit-button">
                  {loading ? "Registrazione…" : "Crea account"}
                </Button>
              </form>
            </TabsContent>
          </Tabs>

          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t border-slate-200" />
            </div>
            <div className="relative flex justify-center text-xs">
              <span className="bg-slate-50 px-2 text-slate-400">oppure</span>
            </div>
          </div>

          <div
  ref={googleButtonRef}
  className="w-full flex justify-center"
  data-testid="google-login-button"
/>
        </div>
      </div>
    </div>
  );
}
