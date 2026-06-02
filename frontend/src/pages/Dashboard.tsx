import { useEffect, useState } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from "recharts";
import { PeriodCompare, SkuRow, WeeklyPoint, api, fmtRub } from "../api";

function defaultRange(): { from: string; to: string } {
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

export default function Dashboard({ accountId }: { accountId: number | null }) {
  const [{ from, to }, setRange] = useState(defaultRange);
  const [cmp, setCmp] = useState<PeriodCompare | null>(null);
  const [weekly, setWeekly] = useState<WeeklyPoint[]>([]);
  const [skus, setSkus] = useState<SkuRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reload = async () => {
    if (!accountId) return;
    setLoading(true); setError(null);
    try {
      const [c, w, sk] = await Promise.all([
        api.analytics.compare(accountId, from, to),
        api.analytics.weekly(accountId, from, to),
        api.analytics.bySku(accountId, from, to),
      ]);
      setCmp(c); setWeekly(w); setSkus(sk);
    } catch (e: any) {
      setError(String(e.message || e));
    } finally { setLoading(false); }
  };
  useEffect(() => { reload(); }, [accountId, from, to]);

  if (!accountId) return <p>Сначала добавьте магазин на вкладке «Магазины».</p>;

  const s = cmp?.current;
  const d = cmp?.delta_pct;

  return (
    <>
      <h2>Дашборд</h2>
      <div className="card">
        <div className="row">
          <label>С <input type="date" value={from} onChange={(e) => setRange((r) => ({ ...r, from: e.target.value }))} /></label>
          <label>по <input type="date" value={to} onChange={(e) => setRange((r) => ({ ...r, to: e.target.value }))} /></label>
          <button onClick={reload} disabled={loading}>{loading ? "..." : "Обновить"}</button>
          {error && <span style={{ color: "#dc2626" }}>{error}</span>}
          {cmp && (
            <span className="muted" style={{ marginLeft: "auto" }}>
              сравнение с {cmp.previous.date_from} … {cmp.previous.date_to}
            </span>
          )}
        </div>
      </div>

      {s && d && (
        <>
          <div className="grid cols-4">
            <Metric label="Выручка" value={s.revenue} delta={d.revenue} />
            <Metric label="К перечислению" value={s.to_pay} delta={d.to_pay} />
            <Metric label="Себестоимость" value={s.cost_of_goods} delta={d.cost_of_goods} invert />
            <Metric label="Чистая прибыль" value={s.net_profit} delta={d.net_profit} signed />
          </div>
          <div className="grid cols-4" style={{ marginTop: 12 }}>
            <Metric label="Заказы (шт)" value={String(s.sales_qty)} suffix="" />
            <Metric label="Возвраты (шт)" value={String(s.returns_qty)} suffix="" invert />
            <Metric label="Комиссия ВБ" value={s.wb_commission} delta={d.wb_commission} invert />
            <Metric label="Логистика" value={s.logistics} delta={d.logistics} invert />
          </div>
          <div className="grid cols-4" style={{ marginTop: 12 }}>
            <Metric label="Хранение" value={s.storage} delta={d.storage} invert />
            <Metric label="Штрафы" value={s.penalty} invert />
            <Metric label="НДС" value={s.vat} delta={d.vat} invert />
            <Metric label="УСН" value={s.tax} delta={d.tax} invert />
          </div>
          <div className="grid cols-4" style={{ marginTop: 12 }}>
            <Metric label="Прочие расходы" value={s.external_expenses} invert />
            <Metric label="Маржа" value={`${s.margin_pct}%`} signed />
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
                  <th>Товар</th>
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
                    <td>
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        {r.photo_url
                          ? <img src={r.photo_url} alt="" style={{ width: 36, height: 36, objectFit: "cover", borderRadius: 4 }} />
                          : <div style={{ width: 36, height: 36, background: "#e5e7eb", borderRadius: 4 }} />}
                        <div>
                          <div style={{ fontWeight: 500 }}>{r.title ?? r.subject_name ?? "—"}</div>
                          <div className="muted" style={{ fontSize: 11 }}>{r.nm_id}</div>
                        </div>
                      </div>
                    </td>
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

function Metric({
  label, value, delta, signed, invert, suffix,
}: {
  label: string; value: string; delta?: string | null;
  signed?: boolean; invert?: boolean; suffix?: string;
}) {
  const num = parseFloat(value);
  const cls = signed ? (num >= 0 ? "pos" : "neg") : "";
  const isPct = typeof suffix === "string" ? false : value.endsWith("%");
  const text = isPct || suffix === "" ? value + (suffix ?? "") : fmtRub(value);
  let deltaEl: JSX.Element | null = null;
  if (delta != null) {
    const dn = parseFloat(delta);
    const up = dn >= 0;
    const good = invert ? !up : up;
    const color = good ? "#059669" : "#dc2626";
    deltaEl = (
      <span style={{ color, fontSize: 12, marginLeft: 6 }}>
        {up ? "▲" : "▼"} {Math.abs(dn).toFixed(1)}%
      </span>
    );
  }
  return (
    <div className="card">
      <div className="muted">{label}</div>
      <div className={`metric ${cls}`}>{text}{deltaEl}</div>
    </div>
  );
}
