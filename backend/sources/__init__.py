# -*- coding: utf-8 -*-
"""行情源导出。"""
from sources.tencent import daily_bars, timeshare, snapshot
from sources.sina import minute_bars, all_a_symbols
from sources import tdx

__all__ = ["daily_bars", "timeshare", "snapshot", "minute_bars",
           "all_a_symbols", "tdx"]


def resolve(source, func):
    """按 source 名解析函数：'free' 用默认免费源，'tdx' 用通达信源。

    例：resolve('tdx', 'daily_bars') -> sources.tdx.daily_bars
    """
    if source == "tdx":
        return getattr(tdx, func)
    return globals()[func]
