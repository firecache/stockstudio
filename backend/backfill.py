# -*- coding: utf-8 -*-
"""统一回填入口。用法：
    python backfill.py symbols
    python backfill.py daily     [--limit 20] [--start 2010-01-01] [--source free|tdx]
    python backfill.py minute    [--limit 20] [--source free|tdx]
    python backfill.py timeshare [--limit 20] [--source free|tdx]
    python backfill.py tick      [--limit 20] [--date 20260930]    # tdx 分笔
    python backfill.py divid     [--limit 20]                      # tdx 除权因子
    python backfill.py calendar                                    # tdx 交易日历
    python backfill.py all       [--limit 20] [--source free|tdx]

source: free = 腾讯(日线/分时)+新浪(分钟) 免费源(默认)；
        tdx  = 通达信 TdxAiData(需在会员中心创建数据服务 Key 并填 TdxAiData.ini)。
"""
import sys
import argparse


def main():
    ap = argparse.ArgumentParser(description="stockstudio 数据回填")
    ap.add_argument("mode", choices=["symbols", "daily", "minute", "timeshare",
                                     "tick", "divid", "calendar", "all"])
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--start", default="2010-01-01")
    ap.add_argument("--date", default="", help="tick 模式：分笔日期(YYYYMMDD)")
    ap.add_argument("--source", default="free", choices=["free", "tdx"])
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

    # tdx 源：先做 Token 检查，未配置直接退出（避免逐只空跑报错）
    if args.source == "tdx" and args.mode in ("daily", "minute", "timeshare", "all"):
        from sources import tdx as _tdx
        if not _tdx.is_configured():
            print("[tdx] 未配置 Token：请在通达信会员中心创建「数据服务」Key，填入 "
                  "site-packages/tdxaidata/lib/TdxAiData.ini 的 [Token] token= 后重试")
            sys.exit(1)

    if args.mode == "symbols":
        p_symbols.run()
    elif args.mode == "daily":
        p_daily.backfill(get_syms(), start=args.start, source=args.source)
    elif args.mode == "minute":
        p_minute.backfill(get_syms(), source=args.source)
    elif args.mode == "timeshare":
        p_timeshare.backfill(get_syms(), source=args.source)
    elif args.mode == "tick":
        _backfill_tick(get_syms(), args.date)
    elif args.mode == "divid":
        _backfill_divid(get_syms())
    elif args.mode == "calendar":
        _run_calendar()
    elif args.mode == "all":
        p_daily.backfill(get_syms(), start=args.start, source=args.source)
        p_minute.backfill(get_syms(), source=args.source)
        p_timeshare.backfill(get_syms(), source=args.source)
    print("[done]")


def _backfill_tick(symbols, date):
    """tdx 分笔回填，落盘 data/tick/{code}/{date}.parquet。"""
    from sources import tdx
    import store as _store
    if not date:
        cal = tdx.trading_dates("SH", "2020-01-01", "")
        date = cal[-1] if cal else ""
    if not date:
        print("[tick] 未指定 --date 且无法取最近交易日")
        return
    total = len(symbols)
    for i, sym in enumerate(symbols, 1):
        code = sym["code"]
        try:
            rows = tdx.tick_data(code, date)
            if rows:
                _store.save_tick(code, date, rows)
        except Exception as e:
            print(f"  [{i}/{total}] {code} ERROR: {e}")
        if i % 100 == 0 or i == total:
            print(f"[tick] {i}/{total} 完成")
    return total


def _backfill_divid(symbols):
    """tdx 除权因子回填，落盘 data/divid/{code}.parquet。"""
    from sources import tdx
    import store as _store
    total = len(symbols)
    for i, sym in enumerate(symbols, 1):
        code = sym["code"]
        try:
            rows = tdx.divid_factors(code)
            if rows:
                _store.save_divid(code, rows)
        except Exception as e:
            print(f"  [{i}/{total}] {code} ERROR: {e}")
        if i % 100 == 0 or i == total:
            print(f"[divid] {i}/{total} 完成")
    return total


def _run_calendar():
    from sources import tdx
    for mkt in ("SH", "SZ"):
        cal = tdx.trading_dates(mkt, "2010-01-01", "")
        print(f"[calendar] {mkt}: {len(cal)} 个交易日, "
              f"首={cal[0] if cal else '-'} 末={cal[-1] if cal else '-'}")


if __name__ == "__main__":
    main()
