import { useState } from "react";
import { Account, api } from "../api";

export default function Accounts({ accounts, onChange }: { accounts: Account[]; onChange: () => void }) {
  const [name, setName] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [taxType, setTaxType] = useState("usn_6");
  const [taxRate, setTaxRate] = useState("0.06");

  const submit = async () => {
    if (!name.trim()) return;
    await api.accounts.create({ name, api_key: apiKey || null, tax_type: taxType, tax_rate: taxRate as any });
    setName(""); setApiKey("");
    onChange();
  };

  const remove = async (id: number) => {
    if (!confirm("Удалить магазин со всеми отчётами?")) return;
    await api.accounts.delete(id);
    onChange();
  };

  return (
    <>
      <h2>Магазины</h2>
      <div className="card">
        <h3 style={{ marginTop: 0 }}>Добавить магазин</h3>
        <div className="row">
          <input placeholder="Название" value={name} onChange={(e) => setName(e.target.value)} />
          <input placeholder="WB API ключ (опционально)" value={apiKey} onChange={(e) => setApiKey(e.target.value)} style={{ minWidth: 320 }} />
          <select value={taxType} onChange={(e) => setTaxType(e.target.value)}>
            <option value="usn_6">УСН 6% (доходы)</option>
            <option value="usn_15">УСН 15% (доходы−расходы)</option>
            <option value="none">Без налога</option>
          </select>
          <input placeholder="Ставка" value={taxRate} onChange={(e) => setTaxRate(e.target.value)} style={{ width: 80 }} />
          <button onClick={submit}>Добавить</button>
        </div>
      </div>

      <div className="card">
        <table>
          <thead>
            <tr><th>ID</th><th>Название</th><th>API ключ</th><th>Налог</th><th>Ставка</th><th></th></tr>
          </thead>
          <tbody>
            {accounts.map((a) => (
              <tr key={a.id}>
                <td>{a.id}</td>
                <td>{a.name}</td>
                <td>{a.api_key ? "•••" + a.api_key.slice(-6) : "—"}</td>
                <td>{a.tax_type}</td>
                <td>{a.tax_rate}</td>
                <td><button className="danger" onClick={() => remove(a.id)}>Удалить</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
