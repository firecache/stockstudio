# TdxAiData 数据源（通达信后台数据）

通达信 `TdxAiData`（`tdxaidata` Python 包）是**付费增强数据源**，通过 `tqserver` 后台模式直连通达信数据服务器取数，不依赖本地通达信客户端。已融合进 stockstudio 数据源体系（`sources/tdx.py`），与免费源（腾讯/新浪）可切换、可互补。

## 相比免费源，TDX 补齐了什么

| 能力 | 免费源（腾讯/新浪） | TdxAiData |
|---|---|---|
| 日线 2010-至今 | ✅（腾讯，含前复权/不复权） | ✅（`get_market_data` 1d + `dividend_type` 复权） |
| 分钟线 1/5/15/30/60 | ⚠️ 近端（新浪 1min≈10天、5min≈6周…） | ✅ 深度历史（官方说明「一分钟周期云获取不再受限 100 天」） |
| 当日分时 | ✅ 腾讯 | ✅ `get_minute_data`，**且可指定任意历史日期** |
| 分笔（tick） | ❌ | ✅ `get_tick_data` |
| 除权除息因子 | ❌（只有腾讯前复权价） | ✅ `get_divid_factors` |
| 交易日历 | ❌ | ✅ `get_trading_dates` |
| 实时快照/订阅 | ✅ 腾讯快照 | ✅ `get_market_snapshot_batch` + `subscribe` 推送 |

## 安装

```bash
pip install tdxaidata -i https://pypi.tuna.tsinghua.edu.cn/simple
```

（已加入 `backend/requirements.txt`；包内自带各平台动态库 `TdxAiData.dll/.so/.dylib` 与 `TdxAiData.ini`。）

## 配置 Token（必需）

后台数据模式需要 Key 鉴权，否则所有接口返回空 `{}`（本模块会统一报「未配置 Token」）。

1. 登录通达信个人版商城「会员中心 → 积分和Key管理 → 创建数据服务Key（数据服务类型）」。
2. 把 Key 填入动态库目录下的配置文件：
   - Windows：`site-packages\tdxaidata\lib\TdxAiData.ini`
   - 本机路径：`D:\Python\Python310\Lib\site-packages\tdxaidata\lib\TdxAiData.ini`
3. 编辑 `[Token]` 节：

```ini
[Token]
token=你的数据服务Key
;user=用户名（部分服务需一并填写）
```

验证是否配置成功：

```bash
cd backend
python scripts/probe_tdx.py
# 输出 "Token 已配置: True" 即成功，否则显示未配置
```

## 使用

回填入口统一为 `backfill.py`，加 `--source tdx` 即可切换；另新增三个 tdx 专属模式：

```bash
cd backend

# 日线（前复权+不复权），TDX 源
python backfill.py daily --source tdx --limit 20

# 分钟线（1/5/15/30/60），TDX 源（深度历史）
python backfill.py minute --source tdx --limit 20

# 分时（最近交易日），TDX 源（可扩展为历史分时）
python backfill.py timeshare --source tdx --limit 20

# 分笔（默认最近交易日，可 --date 20260930）
python backfill.py tick --limit 20 --date 20260930

# 除权因子
python backfill.py divid --limit 20

# 交易日历
python backfill.py calendar
```

不传 `--source` 时默认 `free`（腾讯/新浪），行为不变。

## 代码格式与字段单位

- **代码格式**：TDX 用 `600519.SH`，项目内部用 `sh600519`。`sources/tdx.py` 内部自动双向转换，外部调用一律用项目内部格式（`sh600519` / `sz000001` / `bj920000`）。
- **字段单位**（官方文档口径）：
  - 开高低收 = 元
  - 成交量 = 手（与腾讯/新浪统一）
  - 成交额 = 万元（模块内已 ×10000 转成元，与新浪 minute.amount 口径一致）
- **复权**：`daily_bars(fq="qfq")` → `dividend_type="front"`（前复权）；`fq="raw"` → `"none"`（不复权）。

## 注意事项

- **付费**：数据服务 Key 需在通达信会员中心开通（具体额度/价格以官方为准）。
- **落地目录**：日线/分钟/分时与免费源共用同一 Parquet 目录（字段 schema 一致，可互相补齐）；分笔落 `data/tick/`，除权因子落 `data/divid/`。
- **仍需真实数据校准**：分时 `cum_amount`（累计成交额）由「均价×累计量」近似估算，接入真实 Key 后建议用真实成交额校准；分钟/日线 `volume` 单位假设为「手」，接入后同样用一笔已知标的核对。
- **合规**：自用学习 OK；商用需遵守通达信数据服务条款。
