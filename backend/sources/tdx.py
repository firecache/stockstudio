# -*- coding: utf-8 -*-
"""通达信 TdxAiData 数据源（tqserver 后台数据模式）。

依赖：pip install tdxaidata（包内已含各平台动态库与 TdxAiData.ini）。
鉴权：需在通达信会员中心「积分和Key管理」创建「数据服务」类型 Key，填入
      site-packages/tdxaidata/lib/TdxAiData.ini 的 [Token] 节 token=（及 user=）。
      未配置 Token 时所有接口返回空 {}，本模块统一抛 RuntimeError 提示配置。

相比免费源（腾讯/新浪），TDX 补齐的能力：
  1) 1 分钟线深度历史（官方说明「一分钟周期云获取不再受限 100 天」）
  2) 任意历史分时（get_minute_data 指定日期）
  3) 分笔数据（get_tick_data）
  4) 除权除息因子（get_divid_factors）
  5) 交易日历（get_trading_dates）
  6) 实时快照批量 / 行情订阅（subscribe）

代码格式：TDX 用 `600000.SH`，本项目内部用 `sh600000`，此处做双向转换。
字段单位（官方文档）：OHLC=元，成交量=手，成交额=万元。
"""
from __future__ import annotations

# 惰性导入：未安装 tdxaidata 时 import 本模块不报错，调用时才报错。
try:
    from tdxaidata import tqs
    _HAS_TDX = True
except Exception as _e:  # pragma: no cover
    tqs = None
    _HAS_TDX = False
    _IMPORT_ERR = _e

# 周期映射：本项目 scale -> TDX period
_SCALE_TO_PERIOD = {1: "1m", 5: "5m", 15: "15m", 30: "30m", 60: "1h"}

_MARKET_SUFFIX = {"sh": "SH", "sz": "SZ", "bj": "BJ"}


def to_tdx_code(code: str) -> str:
    """sh600519 -> 600519.SH；已是 600519.SH 则原样返回。"""
    code = code.strip().lower()
    if "." in code:
        num, suf = code.split(".", 1)
        return f"{num}.{suf.upper()}"
    if code[:2] in _MARKET_SUFFIX:
        return f"{code[2:]}.{_MARKET_SUFFIX[code[:2]]}"
    # 裸代码，按上交所默认
    return f"{code}.SH"


def from_tdx_code(tcode: str) -> str:
    """600519.SH -> sh600519。"""
    if "." in tcode:
        num, suf = tcode.split(".", 1)
        return f"{suf.lower()}{num}"
    return tcode


def is_configured() -> bool:
    """Token 是否已配置（直接读包内 TdxAiData.ini 的 [Token] token=，不发网络请求）。"""
    if not _HAS_TDX:
        return False
    try:
        import configparser
        from pathlib import Path
        import tdxaidata
        ini = configparser.ConfigParser()
        ini.read(Path(tdxaidata.__file__).parent / "lib" / "TdxAiData.ini", encoding="utf-8")
        return bool(ini.get("Token", "token", fallback="").strip())
    except Exception:
        return False


def _require():
    if not _HAS_TDX:
        raise RuntimeError(
            "tdxaidata 未安装：pip install tdxaidata -i https://pypi.tuna.tsinghua.edu.cn/simple"
        )
    return tqs


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _norm_dt(t, want_time: bool):
    """把 TDX 返回的时间索引归一化为 'YYYY-MM-DD' 或 'YYYY-MM-DD HH:MM:SS'。"""
    if hasattr(t, "strftime"):
        return t.strftime("%Y-%m-%d %H:%M:%S") if want_time else t.strftime("%Y-%m-%d")
    s = str(t).strip()
    s = s.replace("T", " ").split(".")[0]
    digits = "".join(ch for ch in s if ch.isdigit())
    if not want_time:
        if len(digits) >= 8:
            d = digits[:8]
            return f"{d[:4]}-{d[4:6]}-{d[6:8]}"
        return s
    if len(digits) >= 12:
        d, tm = digits[:8], digits[8:14]
        return f"{d[:4]}-{d[4:6]}-{d[6:8]} {tm[:2]}:{tm[2:4]}:{tm[4:6]}"
    if len(digits) >= 8:
        d = digits[:8]
        return f"{d[:4]}-{d[4:6]}-{d[6:8]}"
    return s


def _df_to_bars(d, tcode, time_is_date: bool):
    """把 get_market_data 返回的 {field: DataFrame(index=时间, columns=代码)} 转成
    与腾讯/新浪一致的 list[dict]（升序）。"""
    if not d or not isinstance(d, dict):
        return []
    close = d.get("Close")
    if close is None:
        return []
    # pandas DataFrame 路径
    if hasattr(close, "columns"):
        df = close
        col = tcode if tcode in df.columns else df.columns[0]
        times = list(df.index)
        out = []
        for t in times:
            key = "date" if time_is_date else "datetime"
            row = {key: _norm_dt(t, want_time=not time_is_date)}
            for field, src in (("open", "Open"), ("high", "High"),
                               ("low", "Low"), ("close", "Close"),
                               ("volume", "Volume"), ("amount", "Amount")):
                fdf = d.get(src)
                if fdf is None or not hasattr(fdf, "loc"):
                    row[field] = None
                    continue
                try:
                    row[field] = _num(fdf.loc[t, col])
                except Exception:
                    row[field] = None
            # 成交额：万元 -> 元（与新浪 minute.amount 口径一致）
            if row.get("amount") is not None:
                row["amount"] = row["amount"] * 10000.0
            out.append(row)
        return out
    # 无 pandas 兜底：field -> {code: [values]}
    times = d.get("Time") or d.get("Date") or []
    vals = {}
    for src in ("Open", "High", "Low", "Close", "Volume", "Amount"):
        f = d.get(src)
        if isinstance(f, dict):
            vals[src] = f.get(tcode) or f.get(from_tdx_code(tcode)) or []
        else:
            vals[src] = f or []
    out = []
    for i, t in enumerate(times):
        key = "date" if time_is_date else "datetime"
        row = {key: _norm_dt(t, want_time=not time_is_date)}
        for field, src in (("open", "Open"), ("high", "High"),
                           ("low", "Low"), ("close", "Close"),
                           ("volume", "Volume"), ("amount", "Amount")):
            seq = vals.get(src, [])
            v = seq[i] if i < len(seq) else None
            row[field] = _num(v)
        if row.get("amount") is not None:
            row["amount"] = row["amount"] * 10000.0
        out.append(row)
    return out


def daily_bars(code, start, end, fq="qfq"):
    """日线。fq: 'qfq'(前复权)/'raw'(不复权)。返回与腾讯一致：
    list[dict] {date, open, close, high, low, volume(手)}，升序。"""
    tqs_mod = _require()
    tcode = to_tdx_code(code)
    div = "front" if fq == "qfq" else "none"
    d = tqs_mod.get_market_data(
        field_list=["Open", "High", "Low", "Close", "Volume", "Amount"],
        stock_list=[tcode], period="1d",
        start_time=start, end_time=end, dividend_type=div,
    )
    bars = _df_to_bars(d, tcode, time_is_date=True)
    if not bars:
        raise RuntimeError(
            f"TDX 日线返回空：{code}（若未配置 Token 请检查 TdxAiData.ini [Token]）"
        )
    return bars


def minute_bars(code, scale):
    """分钟线。scale in {1,5,15,30,60}。返回与新浪一致：
    list[dict] {datetime, open, high, low, close, volume(手), amount(元)}，升序。"""
    tqs_mod = _require()
    tcode = to_tdx_code(code)
    period = _SCALE_TO_PERIOD.get(scale)
    if not period:
        raise ValueError(f"unsupported scale: {scale}")
    d = tqs_mod.get_market_data(
        field_list=["Open", "High", "Low", "Close", "Volume", "Amount"],
        stock_list=[tcode], period=period,
    )
    bars = _df_to_bars(d, tcode, time_is_date=False)
    if not bars:
        raise RuntimeError(f"TDX 分钟线返回空：{code} m{scale}（Token 未配置或无数据）")
    return bars


def timeshare(code, date=None):
    """当日分时（可指定历史日期）。返回 (rows, date, qt)。
    rows: list[dict] {time, price, volume(手), cum_volume, average, cum_amount(元, 近似)}。"""
    tqs_mod = _require()
    tcode = to_tdx_code(code)
    if not date:
        # 默认最近交易日：用交易日历取最后一天
        try:
            cal = trading_dates("SH", "2020-01-01", "")
            date = cal[-1] if cal else ""
        except Exception:
            date = ""
    if not date:
        raise RuntimeError(f"TDX 分时需指定日期：{code}")
    d = tqs_mod.get_minute_data(stock_code=tcode, date=date)
    if not d or not d.get("Time"):
        return [], date, {}
    times = d.get("Time", [])
    prices = d.get("Price", [])
    vols = d.get("Volume", [])
    avgs = d.get("Average", [])
    rows, cum = [], 0.0
    for i, t in enumerate(times):
        p = _num(prices[i]) if i < len(prices) else None
        v = _num(vols[i]) if i < len(vols) else None
        a = _num(avgs[i]) if i < len(avgs) else None
        cum += (v or 0.0)
        # 成交额近似 = 均价 * 累计量(手) * 100
        cum_amt = (a * cum * 100.0) if (a and v is not None) else None
        rows.append({
            "time": _norm_dt(t, want_time=True)[-8:],
            "price": p,
            "volume": v,
            "cum_volume": cum,
            "average": a,
            "cum_amount": cum_amt,
        })
    return rows, _norm_dt(date, want_time=False), {}


def snapshot(codes):
    """批量实时快照。codes: ['sh600519','sz000001'] -> list[dict]。"""
    tqs_mod = _require()
    tcodes = [to_tdx_code(c) for c in codes]
    d = tqs_mod.get_market_snapshot_batch(
        stock_list=tcodes,
        field_list=["Code", "Name", "Now", "Open", "High", "Low",
                    "Volume", "Amount", "LastClose"],
        return_df=False,
    )
    out = []
    for tcode in tcodes:
        item = (d or {}).get(tcode) or {}
        if not item:
            continue
        out.append({
            "code": from_tdx_code(tcode),
            "name": item.get("Name"),
            "price": _num(item.get("Now")),
            "prev_close": _num(item.get("LastClose")),
            "open": _num(item.get("Open")),
            "high": _num(item.get("High")),
            "low": _num(item.get("Low")),
            "volume": _num(item.get("Volume")),   # 手
            "amount": (_num(item.get("Amount")) or 0.0) * 10000.0,  # 万元->元
        })
    return out


def tick_data(code, date):
    """分笔数据。返回 list[dict] {time, price, volume, bs}。"""
    tqs_mod = _require()
    tcode = to_tdx_code(code)
    d = tqs_mod.get_tick_data(stock_code=tcode, date=date)
    if not d or not d.get("Time"):
        return []
    times = d.get("Time", [])
    prices = d.get("Price", [])
    vols = d.get("Volume", [])
    flags = d.get("BSFlag", [])
    out = []
    for i, t in enumerate(times):
        out.append({
            "time": str(t),
            "price": _num(prices[i]) if i < len(prices) else None,
            "volume": _num(vols[i]) if i < len(vols) else None,
            "bs": flags[i] if i < len(flags) else None,
        })
    return out


def divid_factors(code, start="", end=""):
    """除权除息因子。返回 list[dict] {date, type, bonus, allot_price, share_bonus, allotment}。"""
    tqs_mod = _require()
    tcode = to_tdx_code(code)
    r = tqs_mod.get_divid_factors(stock_code=tcode, start_time=start, end_time=end)
    if r is None:
        return []
    out = []
    if hasattr(r, "iterrows"):
        for idx, row in r.iterrows():
            out.append({
                "date": _norm_dt(idx, want_time=False),
                "type": row.get("Type"),
                "bonus": _num(row.get("Bonus")),
                "allot_price": _num(row.get("AllotPrice")),
                "share_bonus": _num(row.get("ShareBonus")),
                "allotment": _num(row.get("Allotment")),
            })
    elif isinstance(r, list):
        for row in r:
            out.append({
                "date": _norm_dt(row.get("Date"), want_time=False),
                "type": row.get("Type"),
                "bonus": _num(row.get("Bonus")),
                "allot_price": _num(row.get("AllotPrice")),
                "share_bonus": _num(row.get("ShareBonus")),
                "allotment": _num(row.get("Allotment")),
            })
    return out


def trading_dates(market="SH", start="", end="", count=-1):
    """交易日列表。market in {SH,SZ}。返回 ['YYYYMMDD', ...] 升序。"""
    tqs_mod = _require()
    r = tqs_mod.get_trading_dates(market, start, end, count)
    if r is None:
        return []
    if isinstance(r, dict):
        r = r.get("Date") or r.get("Value") or []
    return [str(x).strip() for x in r if str(x).strip()]


def stock_list(market=None):
    """TDX 股票列表。返回 list[dict] {code('sh600000'), num, name}。"""
    tqs_mod = _require()
    r = tqs_mod.get_stock_list(market=market, list_type=0)
    if r is None:
        return []
    out = []
    if isinstance(r, list):
        for it in r:
            code = it.get("Code") or it.get("code") or it.get("StockCode")
            name = it.get("Name") or it.get("name")
            if code:
                out.append({"code": from_tdx_code(str(code)),
                            "num": str(code).split(".")[0], "name": name})
    return out
