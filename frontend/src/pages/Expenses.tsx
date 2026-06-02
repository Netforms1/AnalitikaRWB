import { useEffect, useState } from "react";
import { Expense, api } from "../api";

export default function Expenses({ accountId }: { accountId: number | null }) {
  const [items, setItems] = useState<Expense[]>([]);
  const [category, setCategory] = useState("ФОТ");
  const [amount, setAmount] = useState("");
  const [from, setFrom] = useState(new Date().toISOString().slice(0, 10));
  const [to, setTo] = useState(new Date().toISOString().slice(0, 10));
  const [comment, setComment] = useState("");

  const reload = async () => {
    if (!accountId) return;
    setItems(await api.expenses.list(accountId));
  };
  useEffect(() => { reload(); }, [accountId]);

  if (!accountId) return <p>Выберите магазин.</p>;

  const add = async () => {
    if (!amount) return;
    await api.expenses.create(accountId, {
      category, amount, date_from: from, date_to: to, comment,
    } as any);
    setAmount(""); setComment("");
    reload();
  };

  const remove = async (id: number) => {
    await api.expenses.delete(id);
    reload();
  };

  return (
    <>
      <h2>Прочие расходы</h2>
      <div className="card">
        <div className="row">
          <select value={category} onChange={(e) => setCategory(e.target.value)}>
            <option>ФОТ</option>
            <option>Реклама вне ВБ</option>
            <option>Упаковка</option>
            <option>Налог авансом</option>
            <option>Аренда</option>
            <option>Прочее</option>
          </select>
          <input placeholder="Сумма, ₽" value={amount} onChange={(e) => setAmount(e.target.value)} />
          <label>с <input type="date" value={from} onChange={(e) => setFrom(e.target.value)} /></label>
          <label>по <input type="date" value={to} onChange={(e) => setTo(e.target.value)} /></label>
          <input placeholder="Комментарий" value={comment} onChange={(e) => setComment(e.target.value)} />
          <button onClick={add}>Добавить</button>
        </div>
      </div>

      <div className="card">
        <table>
          <thead>
            <tr><th>Категория</th><th>Сумма</th><th>С</th><th>По</th><th>Коммент</th><th></th></tr>
          </thead>
          <tbody>
            {items.map((r) => (
              <tr key={r.id}>
                <td>{r.category}</td><td>{r.amount}</td>
                <td>{r.date_from}</td><td>{r.date_to}</td>
                <td>{r.comment}</td>
                <td><button className="danger" onClick={() => remove(r.id)}>×</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
