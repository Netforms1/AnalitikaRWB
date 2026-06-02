from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import accounts, analytics, costs, expenses, reports


app = FastAPI(title="AnalitikaRWB", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(accounts.router)
app.include_router(reports.router)
app.include_router(costs.router)
app.include_router(expenses.router)
app.include_router(analytics.router)


@app.get("/health")
def health():
    return {"status": "ok"}
