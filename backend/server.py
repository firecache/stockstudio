# -*- coding: utf-8 -*-
"""stockstudio 行情 API：把 Parquet 真实数据暴露为 JSON。无 mock。"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import store

app = FastAPI(title="stockstudio", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/symbols")
def symbols():
    df = store.load_symbols()
    if df is None:
        return {"data": [], "count": 0}
    return {"data": df.to_dict("records"), "count": len(df)}


@app.get("/kline/{code}")
def kline(code: str, fq: str = "qfq", limit: int = 300):
    df = store.load_daily(code, fq)
    if df is None:
        return {"data": [], "count": 0}
    if limit:
        df = df.tail(limit)
    return {"data": df.to_dict("records"), "count": len(df)}


@app.get("/minute/{code}")
def minute(code: str, scale: int = 5):
    df = store.load_minute(code, scale)
    if df is None:
        return {"data": [], "count": 0}
    return {"data": df.to_dict("records"), "count": len(df)}


@app.get("/timeshare/{code}")
def timeshare(code: str, date: str = None):
    d = store.TIMESHARE_DIR / code
    if not d.exists():
        return {"data": [], "date": None}
    dates = sorted([p.stem for p in d.glob("*.parquet")])
    if not dates:
        return {"data": [], "date": None}
    date = date or dates[-1]
    df = pd.read_parquet(d / f"{date}.parquet")
    return {"data": df.to_dict("records"), "date": date}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
