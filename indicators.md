### 5.1 单资产 & 组合收益类（Returns）

用到的数据：价格序列（close/adj_close）、持仓 NAV 序列。

1. 日简单收益率 `r_t = P_t / P_{t-1} - 1`
2. 日对数收益率 `ln(P_t / P_{t-1})`
3. 累计收益率 / 总收益曲线
4. 年化收益率（基于日收益，252 交易日假设）
5. CAGR（用起点/终点 NAV 和持有天数）
6. 月度收益率序列（聚合日收益）
7. 年度收益率序列
8. YTD 收益（今年初到今天）
9. MTD 收益（当月初到今天）
10. N 日滚动收益（rolling N-day return）

> 以上全部可以对「单资产」或「组合 NAV」重复使用。

**交易模式专属（用到用户交易价格，但不拉外部市场数据）**

11. 已实现盈亏（Realized P&L）
12. 未实现盈亏（Unrealized P&L）
13. 总盈亏
14. 每笔交易盈亏（用买卖价格简单算）

> 严格的 IRR / TWR 虽然理论上只用价格 + 现金流就行，但你不希望引入外部现金流（分红、利息），这里可以**只对用户充值/提现 + 交易现金流**做 IRR/TWR，这是合法的，因为这些现金流是你自己数据，不是“市场数据”。

15. 时间加权收益率 TWR（按你定义的 cash flow）
16. 资金加权收益率 IRR/XIRR（同上）

---

### 5.2 风险 / 波动（Risk & Volatility）

基于日收益序列（单资产或组合）。

17. 日波动率（std of daily returns）
18. 年化波动率（std * sqrt(252)）
19. N 日滚动波动率（rolling std）
20. 上行波动（只看 >0 的收益）
21. 下行波动（只看 <0 的收益）
22. 半方差（负收益平方的平均）

---

### 5.3 回撤相关（Drawdown）

基于 NAV 序列。

23. 每日回撤序列（从历史最高点的跌幅）
24. 最大回撤（Max Drawdown）
25. 最大回撤持续时间
26. 平均回撤深度
27. 平均回撤持续时间
28. 恢复时间（从谷底回到原高点所需天数）
29. 最大单日亏损（最小日收益）
30. 最大连续亏损天数
31. 最大连续盈利天数

---

### 5.4 风险调整收益比（Risk-adjusted）

只依赖**收益和波动**，不使用无风险利率（默认 rf=0），也不使用因子。

32. Sharpe Ratio（= 年化收益 / 年化波动）
33. Rolling Sharpe（基于 rolling window 的收益 + 波动）
34. Sortino Ratio（年化收益 / 下行波动年化）
35. Calmar Ratio（年化收益 / 最大回撤）

---

### 5.5 相关性 & Beta（Correlation & Beta）

这里如果你定义一个 benchmark ticker（比如 SPY），由于它也是一个价格序列，本质还是“股价”，不违背你的约束。

36. 单资产 vs 组合的相关系数（corr）
37. 资产之间的相关系数矩阵（组合内）
38. 协方差矩阵（组合内）
39. 对 benchmark 的 Beta（基于线性回归：组合日收益 vs benchmark 日收益）
40. 对 benchmark 的 Alpha（Jensen Alpha，相对 rf=0）
41. R²（回归解释度）

如果你愿意，也可以加：

42. Tracking Error（组合收益 - benchmark 收益 的 std）
43. Information Ratio（超额收益 / Tracking Error）

> 以上都只用两个价格序列，不用额外市场数据。

---

### 5.6 组合结构 & 暴露（Allocation & Exposure）

用到的数据：持仓市值、权重、sector / industry 等静态标签。

44. 单日权重：`weight[symbol] = value[symbol] / total_nav`
45. 历史权重时间序列（持仓 + 价格推导）
46. Top N 权重（前 5 / 10 大持仓的权重和）
47. HHI 集中度：`Σ w_i^2`
48. 按 sector 的权重分布（sector allocation）
49. 按 industry 的权重分布
50. 按「单资产」的 concentration：最大单一权重
51. 权重偏离等权：`|w_i - 1/N|` 的合计或平方和
52. 多头/空头总敞口（如果支持做空，shares < 0）

> 不涉及 FX，不区分 currency exposure。

---

### 5.7 组合风险分解（Risk Decomposition）

只用协方差矩阵 + 权重。

53. 各资产对组合波动率的**风险贡献**（% of total risk）
54. 按 sector 的风险贡献
55. Marginal Contribution to Risk（MCTR）

公式典型是：

* `portfolio_var = wᵀ Σ w`
* 每个资产的贡献 ~ `w_i * (Σ w)_i`

---

### 5.8 交易行为（Trading Behaviour）

只用用户自己的交易记录，不拉市场外部数据。

56. 总交易笔数
57. 年化换手率（交易额 / 平均市值）
58. 单资产的换手率
59. 平均持仓时间（从买入到卖出）
60. 胜率（盈利交易数量 / 总交易数量）
61. 盈亏比（平均盈利 / 平均亏损）
62. 单笔最大盈利
63. 单笔最大亏损
64. 最大连续盈利笔数
65. 最大连续亏损笔数

---

### 5.9 单资产价格技术指标（Technical，纯价格版）

只用 OHLC/close，不用 volume，不用分红。

**趋势类**

66. SMA（简单移动平均）
67. EMA（指数移动平均）
68. WMA（加权移动平均）
69. MACD（价格 EMA 组合：12-26-9）
70. MACD Signal & Histogram

**波动 / 通道类**

71. Bollinger Bands（中轨 = MA， 上下轨 = MA ± k * std）
72. Donchian Channel（N 日最高 / 最低）
73. ATR（Average True Range，用 high/low/close）

**动量类**

74. Rate of Change (ROC)
75. Momentum（`P_t - P_{t-n}`）
76. Stochastic Oscillator (%K, %D，用 high/low/close）
77. RSI（Relative Strength Index）
78. CCI（Commodity Channel Index，用 typical price）
79. Williams %R

**价格水平类**

80. 52 周最高价
81. 52 周最低价
82. 距离 52 周高点的回撤百分比
83. N 日高/低点及其相对当前价格的位置

---

### 5.10 Tail Risk（仍然只用收益分布）

84. 历史 VaR（比如基于日收益分布的 95% VaR）
85. 历史 CVaR/ES（最差 5% 日收益的平均）
86. 收益分布的 Skewness（偏度）
87. Kurtosis（峰度）
