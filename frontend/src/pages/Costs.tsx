import { useEffect, useRef, useState } from "react";
import { CostPrice, api } from "../api";

export default function Costs({ accountId }: { accountId: number | null }) {
  const [items, setItems] = useState<CostPrice[]>([]);
  const [nmId, setNmId] = useState("");
  const [sa, setSa] = useState("");
  const [cost, setCost] = useState("");
  const [from, setFrom] = useState(new Date().toISOString().slice(0, 10));
  const fileRef = useRef<HTMLInputElement>(null);
  const [msg, setMsg] = useState<string | null>(null);

  const reload = async () => {
    if (!accountId) return;
    setItems(await api.costs.list(accountId));
  };
  useEffect(() => { reload(); }, [accountId]);

  if (!accountId) return <p>Выберите магазин.</p>;

  const add = async () => {
    if (!cost) return;
    await api.costs.create(accountId, {
      nm_id: nmId ? Number(nmId) : undefined,
      sa_name: sa || undefined,
      cost,
      valid_from: from,
    });
    setNmId(""); setSa(""); setCost("");
    reload();
  };

  const upload = async () => {
    const f = fileRef.current?.files?.[0];
    if (!f) return;
    try {
      const r = await api.costs.upload(accountId, from, f);
      setMsg(`Загружено: ${r.created}`);
      reload();
    } catch (e: any) { setMsg(`Ошибка: ${e.message || e}`); }
  };

  const remove = async (id: number) => {
    await api.costs.delete(id);
    reload();
  };

  return (
    <>
      <h2>Себестоимость</h2>
      <div className="card">
        <h3 style={{ marginTop: 0 }}>Добавить запись</h3>
        <div className="row">
          <input placeholder="nm_id (артикул ВБ)" value={nmId} onChange={(e) => setNmId(e.target.value)} />
          <span>или</span>
          <input placeholder="артикул поставщика" value={sa} onChange={(e) => setSa(e.target.value)} />
          <input placeholder="себестоимость, ₽" value={cost} onChange={(e) => setCost(e.target.value)} />
          <label>с <input type="date" value={from} onChange={(e) => setFrom(e.target.value)} /></label>
          <button onClick={add}>Сохранить</button>
        </div>
        <hr style={{ margin: "16px 0" }} />
        <h3>Массовая загрузка</h3>
        <div className="row">
          <input ref={fileRef} type="file" accept=".xlsx,.xls,.csv" />
          <span>Колонки: nm_id (или sa_name) и cost. Дата действия — из поля выше.</span>
          <button className="secondary" onClick={upload}>Загрузить</button>
        </div>
        {msg && <p>{msg}</p>}
      </div>

      <div className="card">
        <table>
          <thead>
            <tr><th>nm_id</th><th>Артикул</th><th>Себестоимость</th><th>С</th><th>По</th><th></th></tr>
          </thead>
          <tbody>
            {items.map((r) => (
              <tr key={r.id}>
                <td>{r.nm_id ?? "—"}</td>
                <td>{r.sa_name ?? "—"}</td>
                <td>{r.cost}</td>
                <td>{r.valid_from}</td>
                <td>{r.valid_to ?? "сейчас"}</td>
                <td><button className="danger" onClick={() => remove(r.id)}>×</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
