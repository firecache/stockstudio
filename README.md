# stockstudio

移动端 A 股看盘 App（Android / iOS / 鸿蒙 NEXT / 小程序），界面对标开盘啦。
数据全部来自公开免费行情源，**真实数据，无 mock**。

## 目录结构

```
stockstudio/
├── backend/          # 数据管道（Python 3.10 + pandas/pyarrow）
│   ├── sources/      # 行情源：腾讯(日线/分时/快照)、新浪(分钟/股票列表)
│   ├── pipeline/     # 回填管道：日线/分钟/分时/股票列表
│   ├── store.py      # Parquet 落盘
│   ├── backfill.py   # 统一回填入口
│   └── data/         # 真实行情数据（git 忽略）
├── app/              # uni-app x 客户端（后续）
└── docs/             # 设计文档
```

## 数据源与覆盖范围

| 数据 | 源 | 覆盖 | 说明 |
|---|---|---|---|
| 日线（前复权/不复权） | 腾讯 fqkline | 2010 至今 · 全市场 | 分页回填，字段 date/open/high/low/close/volume(手) |
| 分钟线 1/5/15/30/60 | 新浪 getKLineData | 近端（60min≈2年、1min≈10日） | 免费源无 2010 至今分钟历史 |
| 分时（当日） | 腾讯 minute/query | 当日实时 ~267 点 | 含累计量额 |
| 实时快照 | 腾讯 qt.gtimg.cn | 实时 | 价/涨跌/量额/换手/PE |

> 已知限制：分钟线历史（2010 至今）免费源不提供；1 分钟仅近端。商用需购买数据授权。

## 快速开始

```bash
cd backend
# 依赖
D:/Python/Python310/python.exe -m pip install -r requirements.txt

# 1) 拉全 A 股列表
python backfill.py symbols

# 2) 日线回填 2010-至今（前 20 只示例）
python backfill.py daily --limit 20

# 3) 分钟线 / 分时
python backfill.py minute --limit 20
python backfill.py timeshare --limit 20

# 4) 一次性全量
python backfill.py all --limit 20
```

## 数据校验

数据落盘为 Parquet，可用 pandas 读取校验：
```python
import pandas as pd
df = pd.read_parquet("data/daily/qfq/sh600519.parquet")
print(df.head(), df.shape)
```
