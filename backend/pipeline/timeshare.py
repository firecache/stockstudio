# -*- coding: utf-8 -*-
"""数据管道：当日分时，腾讯源。真实数据。"""
import time
import store
from sources import resolve


def backfill(symbols, source="free"):
    timeshare = resolve(source, "timeshare")
    total = len(symbols)
    # tdx 分时需指定日期：取最近交易日一次，避免每只股票重复查交易日历
    latest_date = None
    if source == "tdx":
        from sources import tdx as _tdx
        try:
            cal = _tdx.trading_dates("SH", "2020-01-01", "")
            latest_date = cal[-1] if cal else None
        except Exception:
            latest_date = None
    for i, sym in enumerate(symbols, 1):
        code = sym["code"]
        try:
            if source == "tdx":
                if not latest_date:
                    raise RuntimeError("TDX 未取得最近交易日")
                rows, date, qt = timeshare(code, date=latest_date)
            else:
                rows, date, qt = timeshare(code)
            if rows and date:
                store.save_timeshare(code, date, rows)
        except Exception as e:
            print(f"  [{i}/{total}] {code} ERROR: {e}")
        if i % 50 == 0 or i == total:
            print(f"[timeshare:{source}] {i}/{total} 完成")
        time.sleep(0.1 if source == "free" else 0.05)
    return total


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    syms = store.load_symbols()
    if syms is None:
        from pipeline.symbols import run
        run()
        syms = store.load_symbols()
    rows = syms.to_dict("records")
    if args.limit:
        rows = rows[:args.limit]
    backfill(rows)
