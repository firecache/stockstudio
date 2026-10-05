# -*- coding: utf-8 -*-
"""新浪行情源：分钟线(近端)、全A股列表。真实数据，无 mock。"""
import time
import requests
from config import UA


def _get(url, referer="https://finance.sina.com.cn/", retries=3):
    headers = dict(UA)
    headers["Referer"] = referer
    last = None
    for i in range(retries):
        try:
            r = requests.get(url, headers=headers, timeout=25)
            if r.status_code == 200:
                return r
            last = f"HTTP {r.status_code}"
        except requests.RequestException as e:
            last = str(e)
        time.sleep(1 + i)
    raise RuntimeError(f"sina fetch failed: {url} ({last})")


def minute_bars(code, scale):
    """新浪分钟线，scale in {1,5,15,30,60}。近端数据（约 datalen=1970 根）。
    返回按时间升序的 list[dict]，volume 由股换算为手。"""
    url = (f"https://quotes.sina.cn/cn/api/json_v2.php/CN_MarketDataService.getKLineData"
           f"?symbol={code}&scale={scale}&ma=no&datalen=1970")
    arr = _get(url).json()
    if not isinstance(arr, list):
        raise RuntimeError(f"sina minute unexpected: {str(arr)[:200]}")
    out = []
    for row in arr:
        out.append({
            "datetime": row["day"],
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
            "volume": float(row["volume"]) / 100.0,   # 股 -> 手
            "amount": float(row.get("amount", 0.0)),  # 元
        })
    return out


def all_a_symbols():
    """全A股列表。返回 list[dict]: code('sh600000'), num('600000'), name。"""
    out = []
    for page in range(1, 200):
        url = (f"https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/"
               f"Market_Center.getHQNodeData?page={page}&num=100&sort=symbol&asc=1&node=hs_a")
        r = _get(url)
        data = r.json()
        if not data:
            break
        for it in data:
            sym = it.get("symbol")       # sh600000
            num = it.get("code")         # 600000
            name = it.get("name")
            if sym and num:
                out.append({"code": sym, "num": num, "name": name})
        if len(data) < 100:
            break
    return out
