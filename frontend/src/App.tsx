import { useEffect, useState } from "react";
import { NavLink, Route, Routes, Navigate } from "react-router-dom";
import { Account, api } from "./api";
import Dashboard from "./pages/Dashboard";
import Accounts from "./pages/Accounts";
import Reports from "./pages/Reports";
import Costs from "./pages/Costs";
import Expenses from "./pages/Expenses";
import Products from "./pages/Products";

export default function App() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [accountId, setAccountId] = useState<number | null>(null);

  const reload = async () => {
    const list = await api.accounts.list();
    setAccounts(list);
    if (list.length && accountId == null) setAccountId(list[0].id);
    if (accountId != null && !list.find((a) => a.id === accountId)) {
      setAccountId(list[0]?.id ?? null);
    }
  };
  useEffect(() => { reload(); }, []);

  return (
    <div className="layout">
      <aside className="sidebar">
        <h1>AnalitikaRWB</h1>
        <div style={{ marginBottom: 16 }}>
          <div className="muted" style={{ marginBottom: 4 }}>Магазин</div>
          <select
            value={accountId ?? ""}
            onChange={(e) => setAccountId(Number(e.target.value))}
            style={{ width: "100%" }}
          >
            {accounts.length === 0 && <option value="">— нет —</option>}
            {accounts.map((a) => (
              <option key={a.id} value={a.id}>{a.name}</option>
            ))}
          </select>
        </div>
        <nav>
          <NavLink to="/" end>Дашборд</NavLink>
          <NavLink to="/reports">Отчёты</NavLink>
          <NavLink to="/products">Товары</NavLink>
          <NavLink to="/costs">Себестоимость</NavLink>
          <NavLink to="/expenses">Расходы</NavLink>
          <NavLink to="/accounts">Магазины</NavLink>
        </nav>
      </aside>
      <main className="main">
        <Routes>
          <Route path="/" element={<Dashboard accountId={accountId} />} />
          <Route path="/reports" element={<Reports accountId={accountId} />} />
          <Route path="/products" element={<Products accountId={accountId} />} />
          <Route path="/costs" element={<Costs accountId={accountId} />} />
          <Route path="/expenses" element={<Expenses accountId={accountId} />} />
          <Route path="/accounts" element={<Accounts onChange={reload} accounts={accounts} />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </main>
    </div>
  );
}
