const BASE = "/api";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(BASE + path, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!resp.ok) throw new Error(`${resp.status}: ${await resp.text()}`);
  if (resp.status === 204) return undefined as T;
  return resp.json();
}

export interface Account {
  id: number;
  name: string;
  api_key: string | null;
  tax_type: string;
  tax_rate: string;
  vat_rate: string;
  created_at: string;
}

export interface Report {
  id: number;
  account_id: number;
  source: string;
  date_from: string;
  date_to: string;
  rows_count: number;
  created_at: string;
}

export interface ProfitSummary {
  date_from: string;
  date_to: string;
  revenue: string;
  sales_qty: number;
  returns_qty: number;
  to_pay: string;
  wb_commission: string;
  logistics: string;
  storage: string;
  acceptance: string;
  penalty: string;
  deduction: string;
  acquiring: string;
  rebill_logistic: string;
  additional_payment: string;
  cost_of_goods: string;
  vat: string;
  tax: string;
  external_expenses: string;
  net_profit: string;
  margin_pct: string;
}

export interface SkuRow {
  nm_id: number | null;
  sa_name: string | null;
  subject_name: string | null;
  brand_name: string | null;
  sales_qty: number;
  returns_qty: number;
  revenue: string;
  to_pay: string;
  wb_commission: string;
  logistics: string;
  storage: string;
  cost_of_goods: string;
  net_profit: string;
  margin_pct: string;
}

export interface WeeklyPoint {
  week_start: string;
  revenue: string;
  to_pay: string;
  cost_of_goods: string;
  vat: string;
  tax: string;
  external_expenses: string;
  net_profit: string;
}

export interface CostPrice {
  id: number;
  nm_id: number | null;
  sa_name: string | null;
  cost: string;
  valid_from: string;
  valid_to: string | null;
}

export interface Expense {
  id: number;
  category: string;
  amount: string;
  date_from: string;
  date_to: string;
  comment: string | null;
}

export const api = {
  accounts: {
    list: () => req<Account[]>("/accounts"),
    create: (data: Partial<Account>) =>
      req<Account>("/accounts", { method: "POST", body: JSON.stringify(data) }),
    update: (id: number, data: Partial<Account>) =>
      req<Account>(`/accounts/${id}`, { method: "PUT", body: JSON.stringify(data) }),
    delete: (id: number) => req<void>(`/accounts/${id}`, { method: "DELETE" }),
  },
  reports: {
    list: (accountId?: number) =>
      req<Report[]>("/reports" + (accountId ? `?account_id=${accountId}` : "")),
    delete: (id: number) => req<void>(`/reports/${id}`, { method: "DELETE" }),
    pull: (accountId: number, dateFrom: string, dateTo: string) =>
      req<Report>("/reports/pull", {
        method: "POST",
        body: JSON.stringify({ account_id: accountId, date_from: dateFrom, date_to: dateTo }),
      }),
    upload: async (accountId: number, dateFrom: string, dateTo: string, file: File) => {
      const fd = new FormData();
      fd.append("account_id", String(accountId));
      fd.append("date_from", dateFrom);
      fd.append("date_to", dateTo);
      fd.append("file", file);
      const resp = await fetch(BASE + "/reports/upload", { method: "POST", body: fd });
      if (!resp.ok) throw new Error(await resp.text());
      return (await resp.json()) as Report;
    },
  },
  analytics: {
    summary: (accountId: number, dateFrom: string, dateTo: string) =>
      req<ProfitSummary>(`/analytics/summary?account_id=${accountId}&date_from=${dateFrom}&date_to=${dateTo}`),
    bySku: (accountId: number, dateFrom: string, dateTo: string) =>
      req<SkuRow[]>(`/analytics/by-sku?account_id=${accountId}&date_from=${dateFrom}&date_to=${dateTo}`),
    weekly: (accountId: number, dateFrom: string, dateTo: string) =>
      req<WeeklyPoint[]>(`/analytics/weekly?account_id=${accountId}&date_from=${dateFrom}&date_to=${dateTo}`),
  },
  costs: {
    list: (accountId: number) => req<CostPrice[]>(`/costs?account_id=${accountId}`),
    create: (accountId: number, data: { nm_id?: number; sa_name?: string; cost: string; valid_from: string }) =>
      req<CostPrice>(`/costs?account_id=${accountId}`, { method: "POST", body: JSON.stringify(data) }),
    delete: (id: number) => req<void>(`/costs/${id}`, { method: "DELETE" }),
    upload: async (accountId: number, validFrom: string, file: File) => {
      const fd = new FormData();
      fd.append("account_id", String(accountId));
      fd.append("valid_from", validFrom);
      fd.append("file", file);
      const resp = await fetch(BASE + "/costs/upload", { method: "POST", body: fd });
      if (!resp.ok) throw new Error(await resp.text());
      return resp.json();
    },
  },
  expenses: {
    list: (accountId: number) => req<Expense[]>(`/expenses?account_id=${accountId}`),
    create: (accountId: number, data: Partial<Expense>) =>
      req<Expense>(`/expenses?account_id=${accountId}`, { method: "POST", body: JSON.stringify(data) }),
    delete: (id: number) => req<void>(`/expenses/${id}`, { method: "DELETE" }),
  },
};

export function fmtRub(v: string | number): string {
  const n = typeof v === "string" ? parseFloat(v) : v;
  return new Intl.NumberFormat("ru-RU", { style: "currency", currency: "RUB", maximumFractionDigits: 0 }).format(n);
}
