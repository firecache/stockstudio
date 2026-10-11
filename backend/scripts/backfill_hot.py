# -*- coding: utf-8 -*-
"""回填前端默认展示的热门股（自选 + 行情 HOT + 快捷入口）。TDX 源。"""
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # backend/
import store
from sources import tdx

HOT = [
    'sh600519', 'sz000001', 'sz000858', 'sh600036', 'sz002415', 'sh601318', 'sh601398',
    'sh600030', 'sz000333', 'sh600887', 'sz300750', 'sh601012', 'sz002594', 'sh600276',
    'sz000651', 'sh601899', 'sz300059', 'sh600900', 'sz002714', 'sh601088',
]
# 上证指数（TDX 可能不支持，失败忽略）
EXTRA = ['sh000001']

codes = HOT + EXTRA

# 最近交易日（分时用）
try:
    cal = tdx.trading_dates("SH", "2020-01-01", "")
    latest = cal[-1] if cal else None
except Exception:
    latest = None
print("最近交易日:", latest)

ok = 0
for i, code in enumerate(codes, 1):
    # 日线 qfq + raw
    for fq in ("qfq", "raw"):
        try:
            bars = tdx.daily_bars(code, "2010-01-01", "2026-10-11", fq=fq)
            if bars:
                store.save_daily(code, bars, fq)
                ok += 1
        except Exception as e:
            print(f"  [{i}] {code} {fq} daily ERR: {e}")
    # 分钟 5 周期
    for scale in (1, 5, 15, 30, 60):
        try:
            bars = tdx.minute_bars(code, scale)
            if bars:
                store.save_minute(code, scale, bars)
                ok += 1
        except Exception as e:
            print(f"  [{i}] {code} m{scale} ERR: {e}")
    # 分时
    try:
        rows, date, _ = tdx.timeshare(code, date=latest)
        if rows and date:
            store.save_timeshare(code, date, rows)
            ok += 1
    except Exception as e:
        print(f"  [{i}] {code} timeshare ERR: {e}")
    print(f"[{i}/{len(codes)}] {code} 完成")
    time.sleep(0.05)

print(f"\n[done] 共落盘 {ok} 份")
