# -*- coding: utf-8 -*-
"""数据管道：全A股列表。"""
import store
from sources import all_a_symbols


def run():
    rows = all_a_symbols()
    if not rows:
        raise RuntimeError("symbol list empty")
    path = store.save_symbols(rows)
    print(f"[symbols] {len(rows)} 只 -> {path}")
    return rows


if __name__ == "__main__":
    run()
