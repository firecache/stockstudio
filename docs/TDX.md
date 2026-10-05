# TdxAiData 数据源（通达信后台数据）

通达信 `TdxAiData`（`tdxaidata` Python 包）是**付费增强数据源**，通过 `tqserver` 后台模式直连通达信数据服务器取数，不依赖本地通达信客户端。已融合进 stockstudio 数据源体系（`sources/tdx.py`），与免费源（腾讯/新浪）可切换、可互补。

## 实测数据深度（已用真实 Key 校准）

以贵州茅台（600519）为例，2026-09-30 实测：

| 数据类型 | 免费源（腾讯/新浪） | TdxAiData 实测 | 能否补 2010-至今 |
|---|---|---|---|
| 日线 2010-至今 | ✅ 腾讯（当前被 501 限流） | ✅ **全历史**（4061 根，首 2010-01-04） | ✅ 完全覆盖 |
| 分时（分时图） | ✅ 腾讯（仅当日） | ✅ **任意历史日期**（2010-01-04 起，每日 240 点） | ✅ 完全覆盖 |
| 分钟 1m | ⚠️ 新浪 ~10 天 | ~94 交易日（约 4.5 个月） | ❌ 仅近端 |
| 分钟 5m/15m/30m/60m | ⚠️ 新浪 6周~2年 | ~2 年（2024-09 起，23760 根 5m） | ❌ 仅近端 |
| 分笔（tick） | ❌ | ✅ | — |
| 除权除息因子 | ❌（仅腾讯前复权价） | ✅（2002 年起） | ✅ |
| 交易日历 | ❌ | ✅ | ✅ |
| 实时快照/订阅 | ✅ 腾讯快照 | ✅ 批量快照 + `subscribe` 推送 | ✅ |

**结论**：TDX 把「日线」和「分时」两个 2010-至今 的硬需求补齐了（免费源做不到历史分时）；分钟 K 线的 2010-至今 深度历史仍需更高等级 Key 或其它付费源（TickFlow/聚宽/米筐）。

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

# 日线（前复权+不复权），TDX 源 —— 可替代当前被 501 限流的腾讯日线
python backfill.py daily --source tdx --limit 20

# 分钟线（1/5/15/30/60），TDX 源
python backfill.py minute --source tdx --limit 20

# 分时（最近交易日），TDX 源
python backfill.py timeshare --source tdx --limit 20

# 分笔（默认最近交易日，可 --date 20260930）
python backfill.py tick --limit 20 --date 20260930

# 除权因子
python backfill.py divid --limit 20

# 交易日历
python backfill.py calendar
```

不传 `--source` 时默认 `free`（腾讯/新浪），行为不变。

## 代码格式与字段单位（已实测校准）

- **代码格式**：TDX 用 `600519.SH`，项目内部用 `sh600519`。`sources/tdx.py` 内部自动双向转换，外部调用一律用项目内部格式（`sh600519` / `sz000001` / `bj920000`）。
- **字段单位**（实测，注意与官方文档描述有出入）：
  - `get_market_data`（日线/分钟 K 线）：OHLC=元、**volume=股**（内部 ÷100 转手）、**amount=万元**（内部 ×10000 转元）
  - `get_minute_data`（分时）：**volume=手**；累计成交额由「均价 × 累计量(手) × 100」估算（元）
  - `get_market_snapshot_batch`（快照）：volume=手、amount=万元（内部转元）；**最高/最低字段名是 `Max`/`Min`（不是 `High`/`Low`）**，无 `Name` 字段
- **复权**：`daily_bars(fq="qfq")` → `dividend_type="front"`（前复权）；`fq="raw"` → `"none"`（不复权）。
- 返回结构：`get_market_data` 返回 `{field: DataFrame(index=时间, columns=代码)}`，模块已解析成与免费源一致的 list[dict]（日线 `{date,open,close,high,low,volume}`、分钟 `{datetime,open,high,low,close,volume,amount}`，volume 统一「手」、amount 统一「元」）。

## 验证锚点（600519 贵州茅台）

- 2026-09-30：open 1239.53 / high 1268.0 / low 1236.05 / close 1258.62 / volume 38331手 / 成交额 47.97亿 —— 与腾讯/新浪交叉验证一致
- 2010-01-04：收盘 169.94（不复权）—— 与免费源一致
- 分时 2010-01-04 共 240 点、末价 169.94

## 注意事项

- **付费**：数据服务 Key 需在通达信会员中心开通；分钟 K 线深度受 Key 等级限制（1m≈94 交易日、5m+≈2 年）。
- **落地目录**：日线/分钟/分时与免费源共用同一 Parquet 目录（schema 一致，可互相补齐）；分笔落 `data/tick/`，除权因子落 `data/divid/`。
- **合规**：自用学习 OK；商用需遵守通达信数据服务条款。
