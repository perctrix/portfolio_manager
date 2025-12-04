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

---

## 扩展指标（高级分析）

### 5.11 高级风险调整比率

88. Omega Ratio（收益概率 / 损失概率的比值，比Sharpe更全面）
89. Ulcer Index（sqrt(mean(drawdown²))，衡量回撤的"痛苦程度"）
90. Martin Ratio / Ulcer Performance Index（收益 / Ulcer Index）
91. Burke Ratio（收益 / sqrt(sum(drawdown²))）
92. Gain-Loss Ratio（sum(正收益) / abs(sum(负收益))）
93. Kappa 3 Ratio（收益 / 下偏三阶矩，考虑偏度的风险调整收益）

---

### 5.12 回撤深度分析

94. Time Underwater %（处于回撤中的时间占比）
95. 回撤频率（单位时间内进入回撤的次数）
96. 平均恢复时间（所有回撤的平均恢复天数）
97. Drawdown 95th Percentile（回撤深度的95分位数）
98. Pain Index（sum(abs(每日回撤)) / 总天数）

---

### 5.13 收益分布统计

99. 正收益天数占比（positive_days / total_days）
100. 收益百分位数序列（p5, p25, p50, p75, p95）
101. 最佳/最差月度收益
102. 最佳/最差季度收益
103. 收益稳定性（std(月度收益) / mean(月度收益)）
104. 异常收益频率（abs(return) > 2*std的天数占比）
105. Best/Worst N-day periods（最佳/最差连续N天的累计收益）

---

### 5.14 组合多样化指标

106. Effective Number of Assets（1 / HHI，有效资产数量）
107. Diversification Ratio（Σ(w_i * σ_i) / σ_portfolio）
108. 组合内资产相关性均值
109. 最大/最小两两相关系数

---

### 5.15 交易质量分析

110. 平均交易成本占比（total_fees / total_trade_value）
111. 按资产的交易频率（trades_per_asset）
112. 持仓期分布（histogram of holding periods）
113. 买入价格质量（买入价vs后续N日均价的对比）
114. 卖出价格质量（卖出价vs前N日均价的对比）
115. Round-trip成本（买卖一个完整周期的总成本）

---

### 5.16 收益时间序列特性

116. Autocorrelation (lag 1-5)（收益的自相关性）
117. Hurst Exponent（收益的持续性/反转性，H>0.5趋势, H<0.5反转）
118. Longest Flat Period（最长的NAV不创新高时间）
119. New High Frequency（创历史新高的频率）
120. Rolling Beta to Equal-Weight Portfolio（相对等权组合的滚动beta）

---

### 5.17 技术指标补充

121. ADX (Average Directional Index)（趋势强度）
122. Aroon Indicator（趋势方向和强度）
123. Parabolic SAR（止损和反转点）
124. Ichimoku Cloud (Tenkan, Kijun, Senkou A/B)（综合趋势系统）
125. Pivot Points（支撑/阻力位）
126. Elder Ray (Bull/Bear Power)
127. TRIX (Triple EMA Oscillator)
128. Vortex Indicator（趋势反转）

---

### 5.18 压力和尾部风险扩展

129. Expected Tail Loss (ETL)（超过VaR后的期望损失）
130. 最差N日平均收益（mean(worst N days)）
131. 最差N月平均收益（mean(worst N months)）
132. Tail Ratio（abs(p95) / abs(p5)，右尾vs左尾）

---

### 5.19 高级收益质量

133. Return Smoothness（1 - std(daily_returns) / std(cumulative_returns的一阶差分)）
134. Linearity of Equity Curve（R² of linear regression on log(NAV)）
135. Consistency Score（正收益月数 / 总月数）
136. Recovery Factor（net_profit / max_drawdown）
137. Lake Ratio（回撤面积 / NAV曲线下面积）

---

### 5.20 季节性和周期

138. 月度季节性得分（每个月的平均收益）
139. 季度季节性得分（每个季度的平均收益）
140. 年末效应（12月vs其他月的收益对比）
141. 月初/月末效应（每月前5天vs后5天的收益对比）

---

### 5.21 相对表现（无需大盘数据）

142. vs Equal-Weight（组合收益 - 等权组合收益）
143. vs Best Asset（组合收益 - 表现最好单一资产收益）
144. vs Worst Asset（组合收益 - 表现最差单一资产收益）
145. Diversification Benefit（组合收益 - 加权平均单资产收益）

---

### 5.22 高级Sharpe变体

146. Adjusted Sharpe Ratio（考虑skewness和kurtosis修正后的Sharpe）
147. Probabilistic Sharpe Ratio（Sharpe > threshold的概率）
148. Deflated Sharpe Ratio（考虑多次测试后的Sharpe）
149. Information Ratio (vs Equal-Weight)（超额收益 / 跟踪误差）

---

### 5.23 波动率扩展

150. Volatility of Volatility（std(rolling_volatility)）
151. Parkinson Volatility（基于high-low的波动率估计，更高效）
152. Garman-Klass Volatility（综合OHLC的波动率）
153. Volatility Regime（高/低波动状态的识别）

---

### 5.24 组合再平衡分析

154. Weight Drift Speed（权重偏离初始值的速度）
155. Rebalancing Need Score（当前权重vs目标权重的偏离度）
156. Drift Contribution to Return（权重漂移对收益的贡献）

---

### 5.25 高级数学指标（研究向）

157. Fractal Dimension（收益序列的分形维度）
158. Shannon Entropy（收益分布的熵）
159. Sample Entropy（时间序列的复杂度）
160. Lyapunov Exponent（混沌程度）

---

### 5.26 机器学习特征

161. Rolling Z-Score（(current - rolling_mean) / rolling_std）
162. Regime Probability（HMM识别的市场状态概率）
163. Trend Strength Score（多指标综合的趋势得分）
164. Mean Reversion Score（基于统计的均值回归强度）
165. Momentum Composite（多周期动量的加权组合）

---

## 大盘对比指标

使用8个全球主要指数作为benchmark：
- ^GSPC (S&P 500)
- ^DJI (Dow Jones)
- ^IXIC (NASDAQ)
- ^RUT (Russell 2000)
- ^GDAXI (DAX)
- ^FTSE (FTSE 100)
- ^HSI (Hang Seng)
- 000001.SS (Shanghai Composite)

对每个benchmark计算：
- Beta（线性回归系数）
- Alpha（Jensen Alpha）
- R²（回归解释度）
- Tracking Error（超额收益的标准差）
- Information Ratio（超额收益 / Tracking Error）
- Correlation（相关系数）

---

## 马科维茨有效前沿（Markowitz Efficient Frontier）

基于现代投资组合理论（MPT），使用均值-方差优化计算有效前沿。

### 核心公式

**组合预期收益：**
`E(R_p) = w'μ = Σ w_i * μ_i`

**组合方差：**
`σ²_p = w'Σw = Σ Σ w_i * w_j * σ_ij`

**全局最小方差组合 (GMV)：**
```
w_GMV = (Σ⁻¹ · 1) / (1ᵀ · Σ⁻¹ · 1)
σ²_GMV = 1 / (1ᵀ · Σ⁻¹ · 1)
```

**最大夏普比率组合（切线组合）：**
```
w_tan = Σ⁻¹(μ - rf) / (1ᵀ · Σ⁻¹ · (μ - rf))
```

**有效前沿优化问题：**
```
Minimize:   w'Σw
Subject to: w'μ = μ_target
            w'1 = 1
            w ≥ 0 (可选，禁止卖空时)
```

### 输出指标

1. **有效前沿曲线**（50个点）
   - 每个点包含：预期收益率、波动率、夏普比率、权重分配

2. **全局最小方差组合 (GMV)**
   - 预期收益率
   - 波动率（所有可行组合中最低）
   - 夏普比率
   - 最优权重分配

3. **最大夏普比率组合（切线组合）**
   - 预期收益率
   - 波动率
   - 夏普比率（所有组合中最高）
   - 最优权重分配

4. **当前组合位置**
   - 预期收益率
   - 波动率
   - 夏普比率
   - 与有效前沿的距离

5. **资产统计**
   - 每个资产的预期收益率（基于历史均值年化）
   - 每个资产的波动率

### 约束条件

- **权重和约束**：所有权重之和等于1
- **非负约束**（可选）：禁止卖空时 w_i ≥ 0
- **允许卖空**：无权重下限约束，可使用解析解

### 实现细节

- 使用 `scipy.optimize.minimize` 的 SLSQP 方法进行约束优化
- 协方差矩阵正则化：`Σ + ε·I` 防止奇异矩阵
- 预期收益使用历史平均收益年化（252交易日）
- 协方差矩阵使用历史协方差年化

### 最低要求

- 至少2个资产
- 至少30天的价格历史数据
