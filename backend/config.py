# -*- coding: utf-8 -*-
"""全局配置。"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"

DAILY_DIR = DATA_DIR / "daily"        # daily/{fq}/{code}.parquet   fq in {qfq, raw}
MINUTE_DIR = DATA_DIR / "minute"      # minute/{code}_{scale}.parquet
TIMESHARE_DIR = DATA_DIR / "timeshare"  # timeshare/{code}/{date}.parquet
TICK_DIR = DATA_DIR / "tick"          # tick/{code}/{date}.parquet
DIVID_DIR = DATA_DIR / "divid"        # divid/{code}.parquet
SYMBOLS_FILE = DATA_DIR / "symbols.parquet"

DEFAULT_START = "2010-01-01"

# 分钟周期 -> 新浪 scale
MINUTE_SCALES = {1: 1, 5: 5, 15: 15, 30: 30, 60: 60}

UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}

for d in (DATA_DIR, DAILY_DIR, MINUTE_DIR, TIMESHARE_DIR, TICK_DIR, DIVID_DIR):
    d.mkdir(parents=True, exist_ok=True)
