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


@app.get("/quote")
def quote(codes: str = ""):
    """批量实时快照。codes=sh600519,sz000001。优先 TDX 实时，失败回退本地日线。"""
    cl = [c.strip() for c in codes.split(",") if c.strip()]
    if not cl:
        return {"data": [], "count": 0}
    data = []
    try:
        from sources import tdx
        if tdx.is_configured():
            data = tdx.snapshot(cl)
    except Exception:
        data = []
    # 回退：本地日线末两根算涨跌
    if not data:
        for c in cl:
            df = store.load_daily(c, "qfq")
            if df is None or len(df) < 2:
                continue
            last, prev = df.iloc[-1], df.iloc[-2]
            data.append({
                "code": c, "price": float(last["close"]),
                "prev_close": float(prev["close"]),
                "open": float(last["open"]), "high": float(last["high"]),
                "low": float(last["low"]), "volume": float(last["volume"]),
            })
    # 补名称 + 涨跌幅
    syms = store.load_symbols()
    name_map = {}
    if syms is not None:
        for r in syms.to_dict("records"):
            name_map[r["code"]] = r["name"]
    out = []
    for d in data:
        code = d.get("code")
        pc = d.get("prev_close")
        try:
            pct = round((d["price"] - pc) / pc * 100, 2) if pc else None
        except Exception:
            pct = None
        out.append({
            "code": code, "name": name_map.get(code, code),
            "price": d.get("price"), "prev_close": pc, "pct": pct,
            "open": d.get("open"), "high": d.get("high"), "low": d.get("low"),
            "volume": d.get("volume"), "amount": d.get("amount"),
        })
    return {"data": out, "count": len(out)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
