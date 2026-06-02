import { useEffect, useMemo, useState } from "react";
import { CostPrice, Product, api, fmtRub } from "../api";

export default function Products({ accountId }: { accountId: number | null }) {
  const [items, setItems] = useState<Product[]>([]);
  const [costs, setCosts] = useState<CostPrice[]>([]);
  const [draft, setDraft] = useState<Record<number, string>>({});
  const [savingNm, setSavingNm] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [q, setQ] = useState("");

  const reload = async () => {
    if (!accountId) return;
    const [p, c] = await Promise.all([
      api.products.list(accountId),
      api.costs.list(accountId),
    ]);
    setItems(p);
    setCosts(c);
    setDraft({});
  };
  useEffect(() => { reload(); }, [accountId]);

  // Текущая себестоимость по nm_id: последняя запись без valid_to.
  const currentCost = useMemo(() => {
    const map: Record<number, CostPrice> = {};
    for (const c of costs) {
      if (c.nm_id != null && c.valid_to == null) map[c.nm_id] = c;
    }
    return map;
  }, [costs]);

  if (!accountId) return <p>Выберите магазин.</p>;

  const sync = async () => {
    setBusy(true); setMsg(null);
    try {
      const r = await api.products.sync(accountId);
      setMsg(`Синхронизировано карточек: ${r.synced}`);
      reload();
    } catch (e: any) { setMsg(`Ошибка: ${e.message || e}`); }
    finally { setBusy(false); }
  };

  const saveCost = async (nmId: number) => {
    const v = (draft[nmId] ?? "").replace(",", ".").trim();
    if (!v || isNaN(Number(v))) { setMsg("Введите число"); return; }
    setSavingNm(nmId); setMsg(null);
    try {
      await api.costs.create(accountId, {
        nm_id: nmId,
        cost: v,
        valid_from: new Date().toISOString().slice(0, 10),
      });
      await reload();
    } catch (e: any) { setMsg(`Ошибка: ${e.message || e}`); }
    finally { setSavingNm(null); }
  };

  const filtered = q
    ? items.filter((p) =>
        [p.title, p.sa_name, p.brand, String(p.nm_id)]
          .filter(Boolean)
          .some((s) => s!.toLowerCase().includes(q.toLowerCase()))
      )
    : items;

  return (
    <>
      <h2>Товары</h2>
      <div className="card">
        <div className="row">
          <button onClick={sync} disabled={busy}>
            {busy ? "Синхронизация..." : "Подтянуть из WB"}
          </button>
          <input
            placeholder="Поиск по названию/артикулу/бренду"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            style={{ minWidth: 300 }}
          />
          <span className="muted">{filtered.length} из {items.length}</span>
        </div>
        {msg && <p style={{ marginTop: 12 }}>{msg}</p>}
        <p className="muted" style={{ marginTop: 12 }}>
          Себестоимость сохраняется с текущей даты. История остаётся: при изменении
          предыдущая запись закрывается, новая действует с сегодняшнего дня.
        </p>
      </div>

      <div className="card">
        <table>
          <thead>
            <tr>
              <th>Фото</th>
              <th>nm_id</th>
              <th>Артикул</th>
              <th>Бренд</th>
              <th>Название</th>
              <th>Категория</th>
              <th>Себестоимость, ₽</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((p) => {
              const cur = currentCost[p.nm_id];
              const value = draft[p.nm_id] ?? (cur ? cur.cost : "");
              const changed = draft[p.nm_id] !== undefined && draft[p.nm_id] !== (cur?.cost ?? "");
              return (
                <tr key={p.id}>
                  <td>
                    {p.photo_url
                      ? <img src={p.photo_url} alt="" style={{ width: 48, height: 48, objectFit: "cover", borderRadius: 4 }} />
                      : <div style={{ width: 48, height: 48, background: "#e5e7eb", borderRadius: 4 }} />}
                  </td>
                  <td>{p.nm_id}</td>
                  <td>{p.sa_name}</td>
                  <td>{p.brand}</td>
                  <td>{p.title}</td>
                  <td>{p.subject_name}</td>
                  <td>
                    <input
                      type="text"
                      inputMode="decimal"
                      value={value}
                      placeholder={cur ? "" : "не задана"}
                      onChange={(e) => setDraft({ ...draft, [p.nm_id]: e.target.value })}
                      onKeyDown={(e) => { if (e.key === "Enter" && changed) saveCost(p.nm_id); }}
                      style={{ width: 110, textAlign: "right" }}
                    />
                  </td>
                  <td>
                    {changed && (
                      <button
                        onClick={() => saveCost(p.nm_id)}
                        disabled={savingNm === p.nm_id}
                      >
                        {savingNm === p.nm_id ? "..." : "Сохранить"}
                      </button>
                    )}
                    {!changed && cur && (
                      <span className="muted" style={{ fontSize: 11 }}>
                        с {cur.valid_from}
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </>
  );
}
