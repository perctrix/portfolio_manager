# 投资组合管理器

[English](README.md) | [中文](README_zh.md)

轻量级、注重隐私的投资组合管理和分析工具，提供全面的绩效指标。

## 功能特性

### 投资组合类型
- **交易模式**：跟踪完整交易历史的个人交易
- **快照模式**：管理当前持仓及成本基础

### 绩效分析
- **95+综合指标**：收益率、风险指标、回撤分析、风险调整比率、尾部风险度量、配置分析、风险分解和交易指标
- **5个基本指标**：总收益率、CAGR、波动率、夏普比率和最大回撤，用于快速分析
- **基准比较**：与8个主要市场指数进行投资组合绩效比较，支持高级指标（Beta、Alpha、特雷诺比率、M2度量、捕获比率等）
- **马科维茨有效前沿**：均值-方差优化，交互式可视化展示最优组合配置（最小方差组合和最大夏普比率组合）

<details>
<summary><b>📊 完整指标列表（点击展开）</b></summary>

#### 收益指标（16个）
- 简单收益率、对数收益率、累计收益率
- 年化收益率、CAGR（复合年增长率）
- 月度收益率、年度收益率
- YTD收益率（年初至今）、MTD收益率（月初至今）
- 滚动收益率
- 已实现盈亏、未实现盈亏、总盈亏
- 交易盈亏
- TWR（时间加权收益率）
- IRR（内部收益率）

#### 风险指标（6个）
- 日波动率、年化波动率
- 滚动波动率
- 上行波动率、下行波动率
- 半方差

#### 回撤分析（10个）
- 回撤序列
- 最大回撤、平均回撤、溃疡指数
- 回撤持续时间、恢复时间
- 最大单日损失、最大单日收益
- 连续亏损天数、连续盈利天数

#### 风险调整比率（9个）
- 夏普比率、滚动夏普比率
- 索提诺比率
- 卡尔马比率
- 特雷诺比率
- 欧米茄比率
- M2度量（莫迪利安尼-莫迪利安尼）
- 收益痛苦比
- 溃疡绩效指数

#### 尾部风险度量（5个）
- VaR（95%置信度风险价值）
- CVaR（95%置信度条件风险价值）
- 偏度
- 峰度
- 尾部比率（95/5百分位）

#### 配置分析（13个）
- 投资组合权重、权重历史
- 前N集中度、HHI（赫芬达尔指数）
- 行业配置、产业配置
- 最大权重、权重偏离等权
- 多空敞口
- 组合波动率
- MCTR（边际风险贡献）
- 资产风险贡献
- 行业风险贡献

#### 交易指标（14个 - 仅交易模式）
- 交易次数
- 换手率、分资产换手率
- 平均持仓期
- 胜率、盈亏比
- 最大交易盈利、最大交易亏损
- 连续盈利交易、连续亏损交易
- 盈利因子（总盈利/总亏损）
- 恢复因子（净盈利/最大回撤）
- 凯利公式（最优仓位）
- 综合交易指标

#### 相关性与Beta分析（16个）
- 与组合的相关性
- 相关性矩阵、协方差矩阵
- Beta系数、Alpha系数、R平方
- 跟踪误差、信息比率
- 特雷诺比率（相对基准）
- M2度量（相对基准）
- 上行捕获率
- 下行捕获率
- 所有基准指标
- 多基准指标
- 平均两两相关性
- 最大/最小相关性

#### 马科维茨有效前沿
- 有效前沿曲线（50个点）
- 全局最小方差（GMV）组合
- 最大夏普比率（切线）组合
- 当前组合与前沿位置对比
- 最优权重对比
- 资产级预期收益和波动率
- 支持卖空开关

</details>

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

### 国际化 (i18n)
- 提供多语言用户界面支持。
- 目前支持英语 (English) 和中文 (简体中文)。

## 架构

- **后端**：Python (FastAPI) 配合 pandas、numpy、scipy、TA-Lib
- **前端**：Next.js 16 (React 19) 配合 TypeScript、TailwindCSS、Recharts
- **存储**：本地CSV/JSON文件（无需数据库）
- **调度器**：APScheduler用于自动化基准更新

### SSE流式传输与并行I/O

`/api/calculate/portfolio-full` 端点使用Server-Sent Events (SSE)，结合优化的并行I/O和请求级缓存，实现最佳性能。


**关键优化：**

| 优化项 | 优化前 | 优化后 | 提升 |
|-------|--------|--------|------|
| 价格加载 | 串行 (N * T) | 并行 (T) | ~N倍 |
| NAV计算 | 重复3次 | 缓存1次 | 3倍 |
| 价格获取 | 多次调用 | 请求级缓存 | 2-3倍 |
| 基本指标+基准 | 串行 | 并行 | ~2倍 |

**缓存策略：**
- `_price_cache`：存储价格DataFrames，从并行加载注入或按需填充
- `_nav_cache`：缓存NAV Series，避免重复计算
- `_base_data_cache`：缓存共享数据（收益率、持仓、权重、价格历史）供指标方法使用

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
- `POST /api/calculate/portfolio-full` - **SSE流式端点**，支持并行I/O（推荐）
- `POST /api/calculate/nav` - 计算净值历史
- `POST /api/calculate/indicators` - 计算绩效指标（旧版）
- `POST /api/calculate/indicators/all` - 计算全部79个指标
- `POST /api/calculate/indicators/basic` - 计算5个基本指标（快速）
- `POST /api/calculate/benchmark-comparison` - 投资组合与基准比较
- `POST /api/calculate/markowitz` - 计算马科维茨有效前沿分析

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
│   │   │       ├── markowitz.py      # 有效前沿优化
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
