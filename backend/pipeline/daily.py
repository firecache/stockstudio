# -*- coding: utf-8 -*-
"""数据管道：日线回填（2010-至今），腾讯源，前复权 + 不复权。断点续传。"""
import time
import store
from config import DEFAULT_START
from sources import daily_bars


def backfill(symbols, start=DEFAULT_START, end=None, fq_list=("qfq", "raw"), resume=True):
    from datetime import datetime
    end = end or datetime.now().strftime("%Y-%m-%d")
    total = len(symbols)
    done = 0
    for i, sym in enumerate(symbols, 1):
        code = sym["code"]
        for fq in fq_list:
            # 断点续传：已存在且最后一根接近今天则跳过
            if resume:
                existing = store.load_daily(code, fq)
                if existing is not None and len(existing) > 0:
                    last = existing["date"].max()
                    if last >= end:  # 已同步到 end
                        continue
            try:
                bars = daily_bars(code, start, end, fq=fq)
                if bars:
                    store.save_daily(code, bars, fq)
            except Exception as e:
                print(f"  [{i}/{total}] {code} {fq} ERROR: {e}")
                continue
        done += 1
        if i % 50 == 0 or i == total:
            print(f"[daily] {i}/{total} 完成")
        time.sleep(0.15)   # 温和限速
    return done


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="只回填前 N 只（0=全部）")
    ap.add_argument("--start", default=DEFAULT_START)
    args = ap.parse_args()

    syms = store.load_symbols()
    if syms is None:
        from pipeline.symbols import run
        run()
        syms = store.load_symbols()
    rows = syms.to_dict("records")
    if args.limit:
        rows = rows[:args.limit]
    backfill(rows, start=args.start)
