import { useState } from "react";
import { Account, api } from "../api";

const USN_PRESETS: Record<string, { type: string; rate: string; label: string }> = {
  "usn_income_1": { type: "usn_income", rate: "0.01", label: "УСН Доходы 1% (рег. льгота)" },
  "usn_income_6": { type: "usn_income", rate: "0.06", label: "УСН Доходы 6%" },
  "usn_expenses_5": { type: "usn_expenses", rate: "0.05", label: "УСН Доходы−Расходы 5% (рег. льгота)" },
  "usn_expenses_15": { type: "usn_expenses", rate: "0.15", label: "УСН Доходы−Расходы 15%" },
  "none": { type: "none", rate: "0", label: "Без УСН" },
};

const VAT_PRESETS: Record<string, string> = {
  "0": "Без НДС",
  "0.05": "НДС 5% (без вычета)",
  "0.07": "НДС 7% (без вычета)",
  "0.20": "НДС 20%",
  "0.22": "НДС 22%",
};

export default function Accounts({ accounts, onChange }: { accounts: Account[]; onChange: () => void }) {
  const [name, setName] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [usnKey, setUsnKey] = useState("usn_income_6");
  const [vatRate, setVatRate] = useState("0");

  const submit = async () => {
    if (!name.trim()) return;
    const usn = USN_PRESETS[usnKey];
    await api.accounts.create({
      name,
      api_key: apiKey || null,
      tax_type: usn.type,
      tax_rate: usn.rate as any,
      vat_rate: vatRate as any,
    });
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
        <div className="row" style={{ marginBottom: 8 }}>
          <input placeholder="Название" value={name} onChange={(e) => setName(e.target.value)} />
          <input
            placeholder="WB API ключ (опционально)"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            style={{ minWidth: 360 }}
          />
        </div>
        <div className="row">
          <label>
            УСН:&nbsp;
            <select value={usnKey} onChange={(e) => setUsnKey(e.target.value)}>
              {Object.entries(USN_PRESETS).map(([k, v]) => (
                <option key={k} value={k}>{v.label}</option>
              ))}
            </select>
          </label>
          <label>
            НДС:&nbsp;
            <select value={vatRate} onChange={(e) => setVatRate(e.target.value)}>
              {Object.entries(VAT_PRESETS).map(([k, v]) => (
                <option key={k} value={k}>{v}</option>
              ))}
            </select>
          </label>
          <button onClick={submit}>Добавить</button>
        </div>
        <p className="muted" style={{ marginTop: 12 }}>
          Регион даёт льготу по УСН — выбирайте 1% (Доходы) или 5% (Доходы−Расходы). НДС начисляется
          с 2026 при доходе &gt; 20 млн ₽ за год: 5% (без вычета) до 272,5 млн, 7% до 490,5 млн или 20/22%
          (с вычетом входного НДС — оформляйте его как «Расходы»).
        </p>
      </div>

      <div className="card">
        <table>
          <thead>
            <tr>
              <th>ID</th><th>Название</th><th>API ключ</th><th>УСН</th><th>Ставка</th><th>НДС</th><th></th>
            </tr>
          </thead>
          <tbody>
            {accounts.map((a) => (
              <tr key={a.id}>
                <td>{a.id}</td>
                <td>{a.name}</td>
                <td>{a.api_key ? "•••" + a.api_key.slice(-6) : "—"}</td>
                <td>{a.tax_type}</td>
                <td>{(parseFloat(a.tax_rate) * 100).toFixed(2)}%</td>
                <td>{parseFloat(a.vat_rate) > 0 ? (parseFloat(a.vat_rate) * 100).toFixed(0) + "%" : "—"}</td>
                <td><button className="danger" onClick={() => remove(a.id)}>Удалить</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
