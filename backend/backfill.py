# -*- coding: utf-8 -*-
"""统一回填入口。用法：
    python backfill.py symbols
    python backfill.py daily   --limit 20 --start 2010-01-01
    python backfill.py minute  --limit 20
    python backfill.py timeshare --limit 20
    python backfill.py all     --limit 20
"""
import sys
import argparse


def main():
    ap = argparse.ArgumentParser(description="stockstudio 数据回填")
    ap.add_argument("mode", choices=["symbols", "daily", "minute", "timeshare", "all"])
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--start", default="2010-01-01")
    args = ap.parse_args()

    import store
    from pipeline import symbols as p_symbols
    from pipeline import daily as p_daily
    from pipeline import minute as p_minute
    from pipeline import timeshare as p_timeshare

    def get_syms():
        syms = store.load_symbols()
        if syms is None:
            p_symbols.run()
            syms = store.load_symbols()
        rows = syms.to_dict("records")
        return rows[:args.limit] if args.limit else rows

    if args.mode == "symbols":
        p_symbols.run()
    elif args.mode == "daily":
        p_daily.backfill(get_syms(), start=args.start)
    elif args.mode == "minute":
        p_minute.backfill(get_syms())
    elif args.mode == "timeshare":
        p_timeshare.backfill(get_syms())
    elif args.mode == "all":
        p_daily.backfill(get_syms(), start=args.start)
        p_minute.backfill(get_syms())
        p_timeshare.backfill(get_syms())
    print("[done]")


if __name__ == "__main__":
    main()
