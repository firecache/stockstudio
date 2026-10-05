# -*- coding: utf-8 -*-
"""腾讯行情源：日线(前复权/不复权, 分页)、分时、实时快照。真实数据，无 mock。"""
import time
import requests
from config import UA


def _get(url, referer="https://gu.qq.com/", retries=5):
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
        # 限流(501/429)与临时错误退避：1,2,4,8,16 秒（封顶 20）
        time.sleep(min(2 ** i + 1, 20))
    raise RuntimeError(f"tencent fetch failed: {url} ({last})")


def _prev_day(d):
    """'YYYY-MM-DD' -> 前一天。"""
    from datetime import datetime, timedelta
    return (datetime.strptime(d, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")


def daily_bars(code, start, end, fq="qfq", count=800):
    """分页拉取日线，返回按日期升序的 list[dict]。

    腾讯 fqkline 字段顺序: [date, open, close, high, low, volume(手)]，
    单次最多约 800 根、按最新在前返回。这里循环把 end 往前推，回填到 start。
    """
    bars = {}
    cur_end = end
    field = "qfqday" if fq == "qfq" else "day"
    while True:
        url = (f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
               f"?param={code},day,{start},{cur_end},{count},{fq}")
        d = _get(url).json()
        if d.get("code") != 0:
            raise RuntimeError(f"tencent error code={d.get('code')} msg={d.get('msg')}")
        node = d["data"][code]
        arr = node.get(field) or node.get("qfqday") or node.get("day")
        if not arr:
            break
        page_min = None
        for row in arr:
            date = row[0]
            if page_min is None or date < page_min:
                page_min = date
            bars[date] = {
                "date": date,
                "open": float(row[1]),
                "close": float(row[2]),
                "high": float(row[3]),
                "low": float(row[4]),
                "volume": float(row[5]),   # 手
            }
        # 已覆盖到 start 或本次返回不足一页 => 结束
        if page_min <= start or len(arr) < count:
            break
        cur_end = _prev_day(page_min)

    out = [bars[k] for k in sorted(bars) if k >= start]
    return out


def timeshare(code):
    """当日分时。返回 (rows, date, qt)。rows: list[dict] time/price/volume(手)/cum_amount/cum_volume。
    北交所(bj)等腾讯不覆盖的标的返回空 list，不抛异常。"""
    url = f"https://web.ifzq.gtimg.cn/appstock/app/minute/query?code={code}"
    d = _get(url).json()
    node = (d.get("data") or {}).get(code)
    if not isinstance(node, dict):
        return [], None, {}
    inner = node.get("data")
    if not isinstance(inner, dict):
        return [], None, {}
    date = inner.get("date")
    qt = node.get("qt", {})
    out = []
    prev_vol = 0.0
    for r in inner.get("data", []):
        try:
            p = r.split()
            if len(p) < 4:
                continue
            t = p[0]
            price = float(p[1])
            cum_vol = float(p[2])        # 累计成交量(手)
            cum_amt = float(p[3])        # 累计成交额(元)
        except (ValueError, IndexError):
            continue
        out.append({
            "time": t,
            "price": price,
            "volume": cum_vol - prev_vol,   # 本分钟成交量(手)
            "cum_volume": cum_vol,
            "cum_amount": cum_amt,
        })
        prev_vol = cum_vol
    return out, date, qt


def snapshot(codes):
    """批量实时快照。codes: ['sh600519','sz000001'] -> list[dict]。
    字段来源 qt.gtimg.cn，GBK 编码，~ 分隔。"""
    url = "https://qt.gtimg.cn/q=" + ",".join(codes)
    r = _get(url)
    r.encoding = "gbk"
    out = []
    for line in r.text.strip().split(";"):
        line = line.strip()
        if not line or "=" not in line:
            continue
        key, val = line.split("=", 1)
        code = key.replace("v_", "")
        f = val.strip('"').split("~")
        if len(f) < 40:
            continue
        out.append({
            "code": code,
            "name": f[1],
            "price": _f(f[3]),
            "prev_close": _f(f[4]),
            "open": _f(f[5]),
            "volume": _f(f[6]),        # 手
            "amount_wan": _f(f[37]),   # 成交额(万元)
            "high": _f(f[33]),
            "low": _f(f[34]),
            "change": _f(f[31]),
            "pct": _f(f[32]),
            "turnover": _f(f[38]),
            "pe": _f(f[39]),
            "time": f[30],
        })
    return out


def _f(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None
