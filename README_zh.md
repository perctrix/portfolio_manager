# 投资组合管理器

[English](README.md) | [中文](README.zh-CN.md)

轻量级、注重隐私的投资组合管理和分析工具，提供全面的绩效指标。

## 功能特性

### 投资组合类型
- **交易模式**：跟踪完整交易历史的个人交易
- **快照模式**：管理当前持仓及成本基础

### 绩效分析
- **79个综合指标**：收益率、风险指标、回撤分析、风险调整比率、尾部风险度量、配置分析、风险分解和交易指标
- **5个基本指标**：总收益率、CAGR、波动率、夏普比率和最大回撤，用于快速分析
- **基准比较**：与8个主要市场指数进行投资组合绩效比较（标普500、纳斯达克、道琼斯、罗素2000、德国DAX、富时100、恒生指数、上证综指）

### 技术分析
- 移动平均线（SMA、EMA、WMA）
- 动量指标（RSI、MACD、随机指标、CCI、威廉姆斯%R、康纳斯RSI）
- 波动率指标（布林带、唐奇安通道、ATR）
- 高级过滤（卡尔曼滤波器、FFT滤波器）

### 数据管理
- 通过调度器自动更新基准数据（工作日服务器时间6:00、10:00、12:00、14:00、16:00、18:00）
- Yahoo Finance集成获取实时价格数据
- 带速率限制的股票代码验证
- 本地CSV存储价格历史

## 架构

- **后端**：Python (FastAPI) 配合 pandas、numpy、scipy、TA-Lib
- **前端**：Next.js 16 (React 19) 配合 TypeScript、TailwindCSS、Recharts
- **存储**：本地CSV/JSON文件（无需数据库）
- **调度器**：APScheduler用于自动化基准更新

## 设置

### 后端

1. 进入 `backend/` 目录
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 运行服务器：
   ```bash
   uvicorn main:app --reload
   ```
   API将在 `http://localhost:8000` 上运行

### 前端

1. 进入 `frontend/` 目录
2. 安装依赖：
   ```bash
   npm install
   ```
3. 运行开发服务器：
   ```bash
   npm run dev
   ```
   应用将在 `http://localhost:3001` 上运行

## API端点

### 投资组合分析
- `POST /api/calculate/nav` - 计算净值历史
- `POST /api/calculate/indicators` - 计算绩效指标（旧版）
- `POST /api/calculate/indicators/all` - 计算全部79个指标
- `POST /api/calculate/indicators/basic` - 计算5个基本指标（快速）
- `POST /api/calculate/benchmark-comparison` - 投资组合与基准比较

### 市场数据
- `GET /api/prices/{symbol}/history` - 获取股票代码的历史价格
- `POST /api/prices/update` - 更新股票代码的价格缓存
- `GET /api/benchmarks/list` - 列出可用的基准指数
- `GET /api/benchmarks/{symbol}/history` - 获取基准历史数据

### 股票代码管理
- `POST /api/tickers/validate` - 验证股票代码（有速率限制）

### 调度器
- `GET /api/scheduler/status` - 获取调度器状态和下次运行时间
- `POST /api/scheduler/update-now` - 手动触发基准更新

## 数据存储

所有数据本地存储在 `backend/data/` 目录：
- `prices/` - 历史价格数据（CSV文件）
- `benchmarks.json` - 基准指数配置
- `tickers/` - 股票代码验证和元数据
- `cache/` - 临时缓存文件

## 项目结构

```
portfolio_manager/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── endpoints.py          # API路由处理器
│   │   ├── core/
│   │   │   ├── engine.py             # 投资组合计算引擎
│   │   │   ├── prices.py             # 价格数据管理
│   │   │   ├── benchmarks.py         # 基准加载器
│   │   │   ├── scheduler.py          # 自动更新调度器
│   │   │   ├── ticker_validator.py   # 股票代码验证
│   │   │   └── indicators/           # 绩效指标
│   │   │       ├── returns.py        # 收益指标
│   │   │       ├── risk.py           # 风险指标
│   │   │       ├── drawdown.py       # 回撤分析
│   │   │       ├── ratios.py         # 夏普、索提诺、卡尔马比率
│   │   │       ├── tail_risk.py      # VaR、CVaR、偏度、峰度
│   │   │       ├── allocation.py     # 持仓配置与风险分解
│   │   │       ├── trading.py        # 交易指标
│   │   │       ├── technical.py      # 技术指标
│   │   │       ├── correlation_beta.py # 基准比较
│   │   │       └── aggregator.py     # 指标聚合
│   │   └── models/
│   │       └── portfolio.py          # 投资组合数据模型
│   ├── data/
│   │   ├── fetch_data.py             # Yahoo Finance数据获取器
│   │   ├── benchmarks.json           # 基准配置
│   │   └── prices/                   # 价格数据缓存
│   └── main.py                       # FastAPI应用
└── frontend/
    ├── app/
    │   ├── page.tsx                  # 投资组合列表
    │   ├── create/page.tsx           # 创建投资组合
    │   └── portfolio/[id]/page.tsx   # 投资组合详情视图
    └── lib/
        └── storage.ts                # 本地存储管理
```

## 依赖项

### 后端
- fastapi - Web框架
- uvicorn - ASGI服务器
- pandas - 数据处理
- numpy - 数值计算
- scipy - 科学计算
- yfinance - Yahoo Finance API
- TA-Lib - 技术分析库
- apscheduler - 任务调度
- portalocker - 文件锁定
- pydantic - 数据验证

### 前端
- next - React框架
- react - UI库
- typescript - 类型安全
- tailwindcss - 样式框架
- recharts - 图表库
- lucide-react - 图标库
