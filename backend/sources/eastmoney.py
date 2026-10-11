# -*- coding: utf-8 -*-
"""东方财富行情源：日线(前复权/不复权)、分时。真实数据，无 mock。

东财 push2his 接口比腾讯 fqkline 快约 20 倍：日线一次请求全历史(2010至今)，
无需分页，且限流远宽松于腾讯。
"""
import requests
from config import UA


def _to_secid(code):
    """sh600519 -> 1.600519；sz000001 -> 0.000001；bj920000 -> 0.920000。"""
    if code.startswith("sh"):
        return "1." + code[2:]
    return "0." + code[2:]   # sz / bj


def daily_bars(code, start, end, fq="qfq"):
    """日线。返回升序 list[dict] {date, open, close, high, low, volume(手), amount(元)}。

    fq: 'qfq'(前复权) / 'raw'(不复权)。
    字段顺序(实测)：date, open, close, high, low, volume, amount, 振幅。
    """
    secid = _to_secid(code)
    fqt = 1 if fq == "qfq" else 0
    beg = start.replace("-", "")
    end_ = end.replace("-", "")
    url = (f"https://push2his.eastmoney.com/api/qt/stock/kline/get"
           f"?secid={secid}&fields1=f1,f2,f3,f4,f5,f6"
           f"&fields2=f51,f52,f53,f54,f55,f56,f57,f58"
           f"&klt=101&fqt={fqt}&beg={beg}&end={end_}")
    r = requests.get(url, headers=dict(UA), timeout=25)
    d = r.json()
    klines = (d.get("data") or {}).get("klines") or []
    out = []
    for k in klines:
        p = k.split(",")
        if len(p) < 7:
            continue
        out.append({
            "date": p[0],
            "open": float(p[1]),
            "close": float(p[2]),
            "high": float(p[3]),
            "low": float(p[4]),
            "volume": float(p[5]),   # 手
            "amount": float(p[6]),   # 元
        })
    return out


def timeshare(code):
    """当日分时。返回 (rows, date, qt)。rows: list[dict] time/price/volume/cum_volume/average/cum_amount。"""
    secid = _to_secid(code)
    url = (f"https://push2his.eastmoney.com/api/qt/stock/trends2/get"
           f"?secid={secid}&fields1=f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13"
           f"&fields2=f51,f52,f53,f54,f55,f56,f57,f58&ndays=1&iscr=0")
    r = requests.get(url, headers=dict(UA), timeout=25)
    d = r.json()
    data = (d.get("data") or {})
    trends = data.get("trends") or []
    date = (data.get("prePrice") and trends and trends[0].split(",")[0][:10]) or None
    out = []
    prev_vol = 0.0
    for t in trends:
        p = t.split(",")
        if len(p) < 8:
            continue
        # fields2: f51=时间, f52=价, f53=均价, f54=累计量(手), f55=?, f56=?, f57=?, f58=?
        tm = p[0]
        price = float(p[1])
        avg = float(p[2]) if p[2] else None
        cum_vol = float(p[3])
        cum_amt = float(p[4]) if p[4] else None
        out.append({
            "time": tm.split(" ")[1].replace(":", "") if " " in tm else tm,
            "price": price,
            "volume": cum_vol - prev_vol,
            "cum_volume": cum_vol,
            "average": avg,
            "cum_amount": cum_amt,
        })
        prev_vol = cum_vol
    return out, date, {}
