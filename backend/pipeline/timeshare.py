# -*- coding: utf-8 -*-
"""数据管道：当日分时，腾讯源。真实数据。"""
import time
import store
from sources import timeshare


def backfill(symbols):
    total = len(symbols)
    for i, sym in enumerate(symbols, 1):
        code = sym["code"]
        try:
            rows, date, qt = timeshare(code)
            if rows and date:
                store.save_timeshare(code, date, rows)
        except Exception as e:
            print(f"  [{i}/{total}] {code} ERROR: {e}")
        if i % 50 == 0 or i == total:
            print(f"[timeshare] {i}/{total} 完成")
        time.sleep(0.1)
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
