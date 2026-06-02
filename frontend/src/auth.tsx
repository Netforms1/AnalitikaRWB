import { createContext, useContext, useEffect, useState, ReactNode } from "react";

const TOKEN_KEY = "analitika.token";
const USER_KEY = "analitika.user";

export interface User {
  id: number;
  email: string;
}

interface AuthCtx {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const Ctx = createContext<AuthCtx | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState<User | null>(() => {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  });

  useEffect(() => {
    if (token) localStorage.setItem(TOKEN_KEY, token); else localStorage.removeItem(TOKEN_KEY);
  }, [token]);
  useEffect(() => {
    if (user) localStorage.setItem(USER_KEY, JSON.stringify(user)); else localStorage.removeItem(USER_KEY);
  }, [user]);

  const authReq = async (path: string, body: any) => {
    const resp = await fetch("/api" + path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!resp.ok) {
      const t = await resp.text();
      try { throw new Error(JSON.parse(t).detail || t); } catch { throw new Error(t); }
    }
    const data = await resp.json();
    setToken(data.access_token);
    setUser(data.user);
  };

  return (
    <Ctx.Provider value={{
      user, token,
      login: (email, password) => authReq("/auth/login", { email, password }),
      register: (email, password) => authReq("/auth/register", { email, password }),
      logout: () => { setToken(null); setUser(null); },
    }}>
      {children}
    </Ctx.Provider>
  );
}

export function useAuth() {
  const v = useContext(Ctx);
  if (!v) throw new Error("AuthProvider missing");
  return v;
}

export function authHeaders(): HeadersInit {
  const t = localStorage.getItem(TOKEN_KEY);
  return t ? { Authorization: `Bearer ${t}` } : {};
}
