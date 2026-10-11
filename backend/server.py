# -*- coding: utf-8 -*-
"""stockstudio 行情 API：把 Parquet 真实数据暴露为 JSON。无 mock。"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import time as _time
import store

_MARKET_CACHE = {"ts": 0.0, "data": []}

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
    """批量实时快照。优先腾讯(免费/快/字段全)，备选 TDX，最后本地日线回退。"""
    cl = [c.strip() for c in codes.split(",") if c.strip()]
    if not cl:
        return {"data": [], "count": 0}
    data = []
    # 1) 腾讯快照（qt.gtimg.cn，实时，字段最全）
    try:
        from sources import tencent
        data = tencent.snapshot(cl)
    except Exception:
        data = []
    # 2) TDX 快照（备选；长驻进程里实时接口可能 hang，故仅兜底）
    if not data:
        try:
            from sources import tdx
            if tdx.is_configured():
                data = tdx.snapshot(cl)
        except Exception:
            data = []
    # 3) 回退：本地日线末两根算涨跌
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
    # 补名称 + 涨跌幅 + 统一字段
    syms = store.load_symbols()
    name_map = {}
    if syms is not None:
        for r in syms.to_dict("records"):
            name_map[r["code"]] = r["name"]
    out = []
    for d in data:
        code = d.get("code")
        pc = d.get("prev_close")
        pct = d.get("pct")
        try:
            if pct is None:
                pct = round((d["price"] - pc) / pc * 100, 2) if pc else None
        except Exception:
            pct = None
        amount = d.get("amount")
        if amount is None and d.get("amount_wan") is not None:
            amount = d["amount_wan"] * 10000.0   # 万元 -> 元
        out.append({
            "code": code, "name": d.get("name") or name_map.get(code, code),
            "price": d.get("price"), "prev_close": pc, "pct": pct,
            "open": d.get("open"), "high": d.get("high"), "low": d.get("low"),
            "volume": d.get("volume"), "amount": amount,
            "turnover": d.get("turnover"), "pe": d.get("pe"),
        })
    return {"data": out, "count": len(out)}


@app.get("/market")
def market(sort: str = "pct"):
    """全市场实时快照（默认按涨跌幅降序）。缓存 30 秒，分批拉腾讯快照(800只/批)。"""
    now = _time.time()
    if _MARKET_CACHE["data"] and now - _MARKET_CACHE["ts"] < 30:
        data = _MARKET_CACHE["data"]
    else:
        syms = store.load_symbols()
        if syms is None:
            return {"data": [], "count": 0}
        codes = syms["code"].tolist()
        from sources import tencent
        raw = []
        for i in range(0, len(codes), 800):
            try:
                raw += tencent.snapshot(codes[i:i + 800])
            except Exception as e:
                print(f"[market] batch {i} err: {e}")
        data = []
        for d in raw:
            amount = d.get("amount_wan")
            data.append({
                "code": d.get("code"), "name": d.get("name"),
                "price": d.get("price"), "prev_close": d.get("prev_close"),
                "pct": d.get("pct"), "change": d.get("change"),
                "open": d.get("open"), "high": d.get("high"), "low": d.get("low"),
                "volume": d.get("volume"),
                "amount": amount * 10000.0 if amount is not None else None,
                "turnover": d.get("turnover"), "pe": d.get("pe"),
            })
        data.sort(key=lambda d: (d["pct"] is None, -(d["pct"] or 0)))
        _MARKET_CACHE["data"] = data
        _MARKET_CACHE["ts"] = now
    if sort != "pct":
        data = sorted(data, key=lambda d: (d.get(sort) is None, -(d.get(sort) or 0)))
    return {"data": data, "count": len(data)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
