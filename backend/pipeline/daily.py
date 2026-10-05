# -*- coding: utf-8 -*-
"""数据管道：日线回填（2010-至今），腾讯源，前复权 + 不复权。断点续传。"""
import time
import store
from config import DEFAULT_START
from sources import resolve


def backfill(symbols, start=DEFAULT_START, end=None, fq_list=("qfq", "raw"),
             resume=True, source="free"):
    from datetime import datetime, timedelta
    end = end or datetime.now().strftime("%Y-%m-%d")
    # 宽限窗口：end 是今天，但最后交易日可能早于今天(周末/国庆8天)，用 10 天宽限避免重复回填
    grace_end = (datetime.strptime(end, "%Y-%m-%d") - timedelta(days=10)).strftime("%Y-%m-%d")
    daily_bars = resolve(source, "daily_bars")
    total = len(symbols)
    done = 0
    consecutive_err = 0
    for i, sym in enumerate(symbols, 1):
        code = sym["code"]
        ok_any = False
        for fq in fq_list:
            # 断点续传：已存在且最后一根在宽限窗口内则跳过
            if resume:
                existing = store.load_daily(code, fq)
                if existing is not None and len(existing) > 0 and existing["date"].max() >= grace_end:
                    ok_any = True
                    continue
            try:
                bars = daily_bars(code, start, end, fq=fq)
                if bars:
                    store.save_daily(code, bars, fq)
                ok_any = True
            except Exception as e:
                print(f"  [{i}/{total}] {code} {fq} ERROR: {e}")
        if ok_any:
            consecutive_err = 0
        else:
            consecutive_err += 1
            if consecutive_err >= 20:
                print(f"  [cooldown] 连续 {consecutive_err} 次失败，休眠 1800s 等限流重置")
                time.sleep(1800)
                consecutive_err = 0
            else:
                time.sleep(20 if source == "free" else 1)   # 免费源限流冷却，tdx 轻冷却
        done += 1
        if i % 50 == 0 or i == total:
            print(f"[daily:{source}] {i}/{total} 完成")
        time.sleep(0.6 if source == "free" else 0.05)
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
