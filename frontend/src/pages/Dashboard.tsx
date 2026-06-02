import { useEffect, useState } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from "recharts";
import { ProfitSummary, SkuRow, WeeklyPoint, api, fmtRub } from "../api";

function defaultRange(): { from: string; to: string } {
  const now = new Date();
  const to = now.toISOString().slice(0, 10);
  const past = new Date(now.getTime() - 30 * 86400_000);
  return { from: past.toISOString().slice(0, 10), to };
}

export default function Dashboard({ accountId }: { accountId: number | null }) {
  const [{ from, to }, setRange] = useState(defaultRange);
  const [summary, setSummary] = useState<ProfitSummary | null>(null);
  const [weekly, setWeekly] = useState<WeeklyPoint[]>([]);
  const [skus, setSkus] = useState<SkuRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reload = async () => {
    if (!accountId) return;
    setLoading(true); setError(null);
    try {
      const [s, w, sk] = await Promise.all([
        api.analytics.summary(accountId, from, to),
        api.analytics.weekly(accountId, from, to),
        api.analytics.bySku(accountId, from, to),
      ]);
      setSummary(s); setWeekly(w); setSkus(sk);
    } catch (e: any) {
      setError(String(e.message || e));
    } finally { setLoading(false); }
  };
  useEffect(() => { reload(); }, [accountId, from, to]);

  if (!accountId) return <p>Сначала добавьте магазин на вкладке «Магазины».</p>;

  return (
    <>
      <h2>Дашборд</h2>
      <div className="card">
        <div className="row">
          <label>С <input type="date" value={from} onChange={(e) => setRange((r) => ({ ...r, from: e.target.value }))} /></label>
          <label>по <input type="date" value={to} onChange={(e) => setRange((r) => ({ ...r, to: e.target.value }))} /></label>
          <button onClick={reload} disabled={loading}>{loading ? "..." : "Обновить"}</button>
          {error && <span style={{ color: "#dc2626" }}>{error}</span>}
        </div>
      </div>

      {summary && (
        <>
          <div className="grid cols-4">
            <Metric label="Выручка" value={summary.revenue} />
            <Metric label="К перечислению" value={summary.to_pay} />
            <Metric label="Себестоимость" value={summary.cost_of_goods} />
            <Metric label="Чистая прибыль" value={summary.net_profit} signed />
          </div>
          <div className="grid cols-4" style={{ marginTop: 12 }}>
            <Metric label="Комиссия ВБ" value={summary.wb_commission} />
            <Metric label="Логистика" value={summary.logistics} />
            <Metric label="Хранение" value={summary.storage} />
            <Metric label="Эквайринг" value={summary.acquiring} />
          </div>
          <div className="grid cols-4" style={{ marginTop: 12 }}>
            <Metric label="Штрафы" value={summary.penalty} />
            <Metric label="Удержания" value={summary.deduction} />
            <Metric label="Налог" value={summary.tax} />
            <Metric label="Маржа" value={`${summary.margin_pct}%`} signed />
          </div>

          <div className="card" style={{ marginTop: 16 }}>
            <h3 style={{ marginTop: 0 }}>По неделям</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={weekly}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="week_start" />
                <YAxis />
                <Tooltip formatter={(v: any) => fmtRub(v)} />
                <Legend />
                <Line type="monotone" dataKey="to_pay" name="К перечислению" stroke="#6d28d9" />
                <Line type="monotone" dataKey="cost_of_goods" name="Себестоимость" stroke="#f59e0b" />
                <Line type="monotone" dataKey="net_profit" name="Чистая прибыль" stroke="#059669" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="card">
            <h3 style={{ marginTop: 0 }}>Топ SKU по прибыли</h3>
            <table>
              <thead>
                <tr>
                  <th>SKU</th>
                  <th>Артикул</th>
                  <th>Бренд</th>
                  <th>Продано</th>
                  <th>Возвраты</th>
                  <th>Выручка</th>
                  <th>К перечислению</th>
                  <th>Себестоимость</th>
                  <th>Чистая прибыль</th>
                  <th>Маржа %</th>
                </tr>
              </thead>
              <tbody>
                {skus.slice(0, 50).map((r) => (
                  <tr key={`${r.nm_id}-${r.sa_name}`}>
                    <td>{r.nm_id}</td>
                    <td>{r.sa_name}</td>
                    <td>{r.brand_name}</td>
                    <td>{r.sales_qty}</td>
                    <td>{r.returns_qty}</td>
                    <td>{fmtRub(r.revenue)}</td>
                    <td>{fmtRub(r.to_pay)}</td>
                    <td>{fmtRub(r.cost_of_goods)}</td>
                    <td style={{ color: parseFloat(r.net_profit) >= 0 ? "#059669" : "#dc2626" }}>
                      {fmtRub(r.net_profit)}
                    </td>
                    <td>{r.margin_pct}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </>
  );
}

function Metric({ label, value, signed }: { label: string; value: string; signed?: boolean }) {
  const num = parseFloat(value);
  const cls = signed ? (num >= 0 ? "pos" : "neg") : "";
  const text = value.endsWith("%") ? value : fmtRub(value);
  return (
    <div className="card">
      <div className="muted">{label}</div>
      <div className={`metric ${cls}`}>{text}</div>
    </div>
  );
}
