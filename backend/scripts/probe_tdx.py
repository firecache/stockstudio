# -*- coding: utf-8 -*-
"""TDX 数据源探针：验证安装、Token 配置状态、以及（若有 Token）真实取数。"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sources import tdx

print("tdxaidata 已安装:", tdx._HAS_TDX)
print("Token 已配置:", tdx.is_configured())

# 代码格式转换自检
assert tdx.to_tdx_code("sh600519") == "600519.SH"
assert tdx.to_tdx_code("sz000001") == "000001.SZ"
assert tdx.to_tdx_code("bj920000") == "920000.BJ"
assert tdx.from_tdx_code("600519.SH") == "sh600519"
print("代码转换自检: OK")

if not tdx.is_configured():
    print("\n[未配置] 无法取真实数据。请按 docs/TDX.md 配置 Token 后重跑。")
    sys.exit(0)

print("\n交易日历 SH(近一个月):", tdx.trading_dates("SH", "2026-09-01", "2026-10-01")[:5])

print("\n日线 600519 前复权(末3根):")
for r in tdx.daily_bars("sh600519", "2026-09-01", "2026-09-30", fq="qfq")[-3:]:
    print("  ", r)

print("\n分钟线 600519 m5(末3根):")
for r in tdx.minute_bars("sh600519", 5)[-3:]:
    print("  ", r)

print("\n分时 600519(最近交易日):")
rows, date, _ = tdx.timeshare("sh600519")
print("  date:", date, "rows:", len(rows), "last:", rows[-1] if rows else None)

print("\n分笔 600519(20260930, 前3笔):")
print("  ", tdx.tick_data("sh600519", "20260930")[:3])

print("\n除权因子 600519(前3条):")
print("  ", tdx.divid_factors("sh600519")[:3])

print("\n快照:")
print("  ", tdx.snapshot(["sh600519", "sz000001"]))
