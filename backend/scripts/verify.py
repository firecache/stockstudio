# -*- coding: utf-8 -*-
"""数据准确性校验：真实数据交叉验证 + 落盘。无 mock。"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # backend/
from datetime import datetime
from sources import daily_bars
import store


def check(code, start="2010-01-01"):
    end = datetime.now().strftime("%Y-%m-%d")
    print(f"\n=== {code} ===")
    qfq = daily_bars(code, start, end, fq="qfq")
    raw = daily_bars(code, start, end, fq="raw")
    print(f"  qfq bars={len(qfq)}  raw bars={len(raw)}")
    if qfq:
        print(f"  qfq first: {qfq[0]}")
        print(f"  qfq last : {qfq[-1]}")
    if raw:
        print(f"  raw first: {raw[0]}")
        print(f"  raw last : {raw[-1]}")
    for tag, arr in [("qfq", qfq), ("raw", raw)]:
        if not arr:
            continue
        bad = [b for b in arr
               if b["high"] < b["low"]
               or b["high"] < max(b["open"], b["close"])
               or b["low"] > min(b["open"], b["close"])]
        dates = [b["date"] for b in arr]
        ok_sorted = dates == sorted(dates)
        ok_unique = len(dates) == len(set(dates))
        print(f"  {tag}: high/low 逻辑异常={len(bad)}  升序={ok_sorted}  无重复={ok_unique}")
    if qfq and raw:
        q0, r0, q1, r1 = qfq[0], raw[0], qfq[-1], raw[-1]
        print(f"  最新日 close: qfq={q1['close']} raw={r1['close']} (应相等)")
        print(f"  2010首日 close: qfq={q0['close']} raw={r0['close']} (应不同, 历年分红复权)")
    if qfq:
        store.save_daily(code, qfq, "qfq")
    if raw:
        store.save_daily(code, raw, "raw")
    return qfq, raw


if __name__ == "__main__":
    for c in ["sh600519", "sz000001", "sh601398"]:
        try:
            check(c)
        except Exception as e:
            print(f"{c} ERROR {e}")
    print("\n[done]")
