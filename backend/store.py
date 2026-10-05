# -*- coding: utf-8 -*-
"""Parquet 存储层。真实数据落盘，无 mock。"""
import pandas as pd
from config import DAILY_DIR, MINUTE_DIR, TIMESHARE_DIR, SYMBOLS_FILE


def save_daily(code, bars, fq="qfq"):
    """bars: list[dict] 升序。"""
    df = pd.DataFrame(bars)
    if df.empty:
        return None
    path = DAILY_DIR / fq / f"{code}.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
    return path


def load_daily(code, fq="qfq"):
    path = DAILY_DIR / fq / f"{code}.parquet"
    return pd.read_parquet(path) if path.exists() else None


def save_minute(code, scale, bars):
    df = pd.DataFrame(bars)
    if df.empty:
        return None
    path = MINUTE_DIR / f"{code}_{scale}.parquet"
    df.to_parquet(path, index=False)
    return path


def load_minute(code, scale):
    path = MINUTE_DIR / f"{code}_{scale}.parquet"
    return pd.read_parquet(path) if path.exists() else None


def save_timeshare(code, date, rows):
    df = pd.DataFrame(rows)
    if df.empty:
        return None
    path = TIMESHARE_DIR / code / f"{date}.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
    return path


def save_symbols(rows):
    df = pd.DataFrame(rows)
    df.to_parquet(SYMBOLS_FILE, index=False)
    return SYMBOLS_FILE


def load_symbols():
    return pd.read_parquet(SYMBOLS_FILE) if SYMBOLS_FILE.exists() else None
