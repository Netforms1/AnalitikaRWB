# AnalitikaRWB

Аналитика чистой прибыли селлера Wildberries — аналог mphunter.ru/decoder.

Подтягивает еженедельные отчёты реализации из WB API и/или Excel,
считает чистую прибыль с учётом себестоимости, налога и прочих расходов,
показывает дашборд: выручка, комиссия ВБ, логистика, хранение, штрафы,
эквайринг, маржа, рентабельность по SKU/брендам/неделям.

## Стек

- Backend: FastAPI, SQLAlchemy 2, Alembic, pandas, openpyxl, httpx, Pydantic v2
- БД: PostgreSQL 16
- Frontend: React 18 + Vite + TypeScript + Recharts
- Деплой: docker-compose

## Структура

```
backend/      # FastAPI
frontend/     # React SPA
docker-compose.yml
```

## Быстрый старт

```bash
cp .env.example .env
docker compose up -d db
cd backend && pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000

cd ../frontend && npm install && npm run dev
```

Открыть http://localhost:5173.

## Методика расчёта чистой прибыли

Источник: детализация еженедельного отчёта реализации ВБ
(`/api/v5/supplier/reportDetailByPeriod`).

```
Выручка              = Σ retail_price_withdisc_rub (Продажа) − Σ (Возврат)
К перечислению (ВБ)  = Σ ppvz_for_pay
Комиссия ВБ          = Σ ppvz_sales_commission
Логистика            = Σ delivery_rub
Хранение             = Σ storage_fee
Приёмка              = Σ acceptance
Штрафы               = Σ penalty
Удержания            = Σ deduction
Эквайринг            = Σ acquiring_fee
Себестоимость        = Σ quantity × cost(nm_id)
Налог                = ставка × база (УСН 6% / 15% / НДС 20%)
Прочие расходы       = пользовательские (ФОТ, реклама вне ВБ, ...)

Чистая прибыль = К перечислению − Себестоимость − Налог − Прочие
Маржа          = Чистая прибыль / Выручка × 100%
```
