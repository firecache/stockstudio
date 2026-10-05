# -*- coding: utf-8 -*-
"""数据管道：分钟线（近端），新浪源，1/5/15/30/60 分钟。真实数据。"""
import time
import store
from sources import minute_bars
from config import MINUTE_SCALES


def backfill(symbols, scales=(1, 5, 15, 30, 60), resume=True):
    total = len(symbols)
    for i, sym in enumerate(symbols, 1):
        code = sym["code"]
        for scale in scales:
            if resume and store.load_minute(code, scale) is not None:
                continue
            try:
                bars = minute_bars(code, scale)
                if bars:
                    store.save_minute(code, scale, bars)
            except Exception as e:
                print(f"  [{i}/{total}] {code} m{scale} ERROR: {e}")
        if i % 50 == 0 or i == total:
            print(f"[minute] {i}/{total} 完成")
        time.sleep(0.1)
    return total


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--scale", type=int, default=0, help="只回填单周期（1/5/15/30/60，0=全部）")
    args = ap.parse_args()

    syms = store.load_symbols()
    if syms is None:
        from pipeline.symbols import run
        run()
        syms = store.load_symbols()
    rows = syms.to_dict("records")
    if args.limit:
        rows = rows[:args.limit]
    scales = (args.scale,) if args.scale else (1, 5, 15, 30, 60)
    backfill(rows, scales=scales)
