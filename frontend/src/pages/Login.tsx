import { useState } from "react";
import { useAuth } from "../auth";

export default function Login() {
  const { login, register } = useAuth();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true); setErr(null);
    try {
      if (mode === "login") await login(email, password);
      else await register(email, password);
    } catch (ex: any) {
      setErr(String(ex.message || ex));
    } finally { setBusy(false); }
  };

  return (
    <div style={{
      minHeight: "100vh", display: "flex", alignItems: "center",
      justifyContent: "center", background: "#f6f7f9",
    }}>
      <form onSubmit={submit} className="card" style={{ width: 360, padding: 24 }}>
        <h2 style={{ marginTop: 0 }}>AnalitikaRWB</h2>
        <p className="muted" style={{ marginTop: -8 }}>
          {mode === "login" ? "Войти в аккаунт" : "Создать аккаунт"}
        </p>
        <div style={{ display: "grid", gap: 10 }}>
          <input
            type="email" placeholder="email" required
            value={email} onChange={(e) => setEmail(e.target.value)}
          />
          <input
            type="password" placeholder="пароль (мин. 6 символов)" required minLength={6}
            value={password} onChange={(e) => setPassword(e.target.value)}
          />
          {err && <div style={{ color: "#dc2626", fontSize: 13 }}>{err}</div>}
          <button type="submit" disabled={busy}>
            {busy ? "..." : (mode === "login" ? "Войти" : "Зарегистрироваться")}
          </button>
          <a href="#" onClick={(e) => { e.preventDefault(); setMode(mode === "login" ? "register" : "login"); setErr(null); }}
             style={{ textAlign: "center", fontSize: 13 }}>
            {mode === "login" ? "Нет аккаунта? Зарегистрироваться" : "Уже есть аккаунт? Войти"}
          </a>
        </div>
      </form>
    </div>
  );
}
