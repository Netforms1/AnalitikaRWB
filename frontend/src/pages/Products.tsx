import { useEffect, useState } from "react";
import { Product, api } from "../api";

export default function Products({ accountId }: { accountId: number | null }) {
  const [items, setItems] = useState<Product[]>([]);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [q, setQ] = useState("");

  const reload = async () => {
    if (!accountId) return;
    setItems(await api.products.list(accountId));
  };
  useEffect(() => { reload(); }, [accountId]);

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
          <input placeholder="Поиск по названию/артикулу/бренду" value={q}
                 onChange={(e) => setQ(e.target.value)} style={{ minWidth: 300 }} />
          <span className="muted">{filtered.length} из {items.length}</span>
        </div>
        {msg && <p style={{ marginTop: 12 }}>{msg}</p>}
      </div>

      <div className="card">
        <table>
          <thead>
            <tr>
              <th>Фото</th><th>nm_id</th><th>Артикул</th><th>Бренд</th><th>Название</th><th>Категория</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((p) => (
              <tr key={p.id}>
                <td>{p.photo_url
                  ? <img src={p.photo_url} alt="" style={{ width: 48, height: 48, objectFit: "cover", borderRadius: 4 }} />
                  : "—"}</td>
                <td>{p.nm_id}</td>
                <td>{p.sa_name}</td>
                <td>{p.brand}</td>
                <td>{p.title}</td>
                <td>{p.subject_name}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
