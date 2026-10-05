# 客户端（uni-app）

## 运行

1. HBuilderX 打开 `app/` 目录（文件 → 打开目录，选 stockstudio/app）。
2. 先启动后端：
   ```bash
   cd backend
   D:/Python/Python310/python.exe server.py   # 或 python -m uvicorn server:app --port 8000
   ```
3. HBuilderX → 运行 → 运行到浏览器（H5 预览，默认 http://localhost:5173）或 运行到手机。

## 后端地址

`app/utils/api.js` 中的 `BASE`：

| 场景 | 地址 |
|---|---|
| H5 / 浏览器预览 | `http://127.0.0.1:8000` |
| 真机调试 | 电脑局域网 IP（如 `http://192.168.x.x:8000`） |
| 小程序 | HTTPS 域名 + 后台配置 request 合法域名 |

## 页面结构

| 页面 | 路径 | 数据 |
|---|---|---|
| 首页 | `pages/index/index` | `/symbols`（数量）+ `/kline/sh600519`（茅台样例） |
| 行情 | `pages/market/market` | `/symbols`（5571 只列表） |
| 个股 | `pages/stock/stock?code=sh600519` | `/kline` + `/timeshare` |
| 我的 | `pages/mine/mine` | 静态说明 |

## 鸿蒙 NEXT（纯血）说明

当前为传统 uni-app Vue3 项目：**Android / iOS / 小程序 / H5 立即可用**。

鸿蒙 NEXT 需用 **uni-app x** 模板（HBuilderX 新建「uni-app x」项目），`.uvue`/`uts` 语法，
编译为 ArkTS 原生。迁移要点：

- 页面 `.vue` → `.uvue`（Vue 语法大体兼容）
- 工具 `.js` → `.uts`
- K 线/分时图 klinecharts 走 renderjs/webview 承载（鸿蒙端 canvas）

## 下一阶段（Phase 1-2）

1. klinecharts 接入 K 线 / 分时图（核心 UI）。
2. 快照接口（`/snapshot`）+ 自选股。
3. 鸿蒙 NEXT（uni-app x）迁移。
