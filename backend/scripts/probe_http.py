# -*- coding: utf-8 -*-
"""数据源连通性/深度探测 — 真实数据，无 mock"""
import requests, json

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
REF_QQ = {"Referer": "https://gu.qq.com/"}
REF_SINA = {"Referer": "https://finance.sina.com.cn/"}

def tget(url, ref=REF_QQ):
    return requests.get(url, headers={**UA, **ref}, timeout=25)

print("=" * 60)
print("[1] 腾讯 日线 fqkline — 结构 + 2010 深度")
u = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600519,day,2010-01-01,2026-10-05,4000,qfq"
r = tget(u)
d = r.json()
print("  http", r.status_code, "| code", d.get("code"), "| msg", d.get("msg"))
data = d.get("data")
print("  data type:", type(data).__name__)
if isinstance(data, dict):
    k = data.get("sh600519", {})
    print("  sym keys:", list(k.keys()))
    arr = k.get("qfqday") or k.get("day") or []
    if arr:
        print("  bars:", len(arr))
        print("  first:", arr[0])
        print("  last:", arr[-1])
else:
    print("  data (list) first 3:", data[:3] if isinstance(data, list) else data)

print("=" * 60)
print("[2] 腾讯 分时 minute/query — 当日实时")
u2 = "https://web.ifzq.gtimg.cn/appstock/app/minute/query?code=sh600519"
r2 = tget(u2)
d2 = r2.json()
k2 = d2.get("data", {}).get("sh600519", {}).get("data", {})
arr2 = k2.get("data", [])
print("  http", r2.status_code, "| bars:", len(arr2))
if arr2:
    print("  first:", arr2[0])
    print("  last:", arr2[-1])

print("=" * 60)
print("[3] 腾讯 实时快照 qt.gtimg.cn (GBK)")
r3 = requests.get("https://qt.gtimg.cn/q=sh600519,sz000001", headers=UA, timeout=20)
r3.encoding = "gbk"
print("  ", r3.text[:200].replace("\n", " | "))

print("=" * 60)
print("[4] 新浪 分钟线 — 各周期近端深度 (datalen=1970)")
for scale, name in [(1, "1min"), (5, "5min"), (15, "15min"), (30, "30min"), (60, "60min"), (240, "日线")]:
    u4 = f"https://quotes.sina.cn/cn/api/json_v2.php/CN_MarketDataService.getKLineData?symbol=sh600519&scale={scale}&ma=no&datalen=1970"
    try:
        r4 = tget(u4, REF_SINA)
        arr4 = r4.json()
        if isinstance(arr4, list) and arr4:
            print(f"  {name:6s} bars={len(arr4):5d}  earliest={arr4[0]['day']}  latest={arr4[-1]['day']}")
        else:
            print(f"  {name:6s} empty/err: {str(arr4)[:120]}")
    except Exception as e:
        print(f"  {name:6s} ERR {e}")
