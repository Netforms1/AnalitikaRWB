import { useEffect, useRef, useState } from "react";
import { Report, api } from "../api";

function defaultWeek(): { from: string; to: string } {
  const now = new Date();
  const day = now.getDay() || 7;
  const monday = new Date(now.getTime() - (day - 1) * 86400_000);
  const lastMonday = new Date(monday.getTime() - 7 * 86400_000);
  const lastSunday = new Date(monday.getTime() - 86400_000);
  return {
    from: lastMonday.toISOString().slice(0, 10),
    to: lastSunday.toISOString().slice(0, 10),
  };
}

export default function Reports({ accountId }: { accountId: number | null }) {
  const [reports, setReports] = useState<Report[]>([]);
  const [{ from, to }, setRange] = useState(defaultWeek);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [cooldown, setCooldown] = useState(0);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (cooldown <= 0) return;
    const t = setInterval(() => setCooldown((c) => Math.max(0, c - 1)), 1000);
    return () => clearInterval(t);
  }, [cooldown]);

  const reload = async () => {
    if (!accountId) return;
    setReports(await api.reports.list(accountId));
  };
  useEffect(() => { reload(); }, [accountId]);

  if (!accountId) return <p>Выберите магазин.</p>;

  const pull = async () => {
    setBusy(true); setMsg(null);
    setCooldown(65);
    try {
      const r = await api.reports.pull(accountId, from, to);
      setMsg(`Загружено ${r.rows_count} строк из API`);
      reload();
    } catch (e: any) {
      const m = String(e.message || e);
      const match = m.match(/Подождите (\d+) сек/);
      if (match) setCooldown(parseInt(match[1], 10));
      setMsg(`Ошибка: ${m}`);
    }
    finally { setBusy(false); }
  };

  const upload = async () => {
    const f = fileRef.current?.files?.[0];
    if (!f) { setMsg("Выберите файл"); return; }
    setBusy(true); setMsg(null);
    try {
      const r = await api.reports.upload(accountId, from, to, f);
      setMsg(`Загружено ${r.rows_count} строк из Excel`);
      reload();
    } catch (e: any) { setMsg(`Ошибка: ${e.message || e}`); }
    finally { setBusy(false); }
  };

  const remove = async (id: number) => {
    if (!confirm("Удалить отчёт?")) return;
    await api.reports.delete(id);
    reload();
  };

  return (
    <>
      <h2>Отчёты реализации</h2>
      <div className="card">
        <div className="row">
          <label>С <input type="date" value={from} onChange={(e) => setRange((r) => ({ ...r, from: e.target.value }))} /></label>
          <label>по <input type="date" value={to} onChange={(e) => setRange((r) => ({ ...r, to: e.target.value }))} /></label>
          <button onClick={pull} disabled={busy || cooldown > 0}>
            {busy ? "Загружаю..." : cooldown > 0 ? `Подождите ${cooldown}с` : "Подтянуть из WB API"}
          </button>
          <span>или</span>
          <input ref={fileRef} type="file" accept=".xlsx,.xls" />
          <button onClick={upload} disabled={busy} className="secondary">Загрузить Excel</button>
        </div>
        {msg && <p style={{ marginTop: 12 }}>{msg}</p>}
      </div>

      <div className="card">
        <table>
          <thead>
            <tr>
              <th>ID</th><th>Источник</th><th>С</th><th>По</th><th>Строк</th><th>Создано</th><th></th>
            </tr>
          </thead>
          <tbody>
            {reports.map((r) => (
              <tr key={r.id}>
                <td>{r.id}</td><td>{r.source}</td>
                <td>{r.date_from}</td><td>{r.date_to}</td>
                <td>{r.rows_count}</td>
                <td>{new Date(r.created_at).toLocaleString("ru-RU")}</td>
                <td><button className="danger" onClick={() => remove(r.id)}>×</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
