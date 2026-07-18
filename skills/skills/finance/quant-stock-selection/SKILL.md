---
name: quant-stock-selection
description: Data-driven A-share (Chinese stock market) multi-factor stock selection with IC-driven weight optimization and a backtest self-optimization loop. Use when asked to build, improve, or self-optimize a stock-picking strategy, validate a screening/factor model against real historical returns, or avoid "cheap but falling" value traps. Covers akshare stable endpoints, factor Information-Coefficient (IC) evaluation, rolling backtest, and honest reporting of negative results.
---

# A股量化选股 / 多因子自优化

## When to use
- 搭建或"优化选股方向"（用户说"自己逐步优化一下选股策略"）
- 验证某套评分/因子模型是否真能跑赢基准 —— 防"综合评分高却跌30%"类事故
- 任何"便宜/基本面好就该买"类假设 → 用真实回测证伪，不顺着假设编

## Core principle: 让数据定权重，不拍脑袋
1. 先建 v1（任意合理权重）跑回测
2. **回测跑输基准 ≠ 完事，必须查死因**（不要粉饰负结果）
3. 测每个因子的真实预测力 **IC = 因子值与未来收益的 Spearman 秩相关**，多个历史时点滚动取均值
4. IC>0 正向用、IC<0 反向用、IC≈0 直接删（纯噪音，当主力权重会亏）
5. 按 |IC| 幅度设定权重 → v2；重跑回测，超额转正才算过
6. 每次迭代留版本号(v1/v2)与回测数字，可复现

## Hard trend filter (淘汰"上海机场式")
任何静态基本面/价值打分都该加硬约束：`r_6m > 0` 且 `现价 > MA120`。
否则像 600009 上海机场（PB 1.29 看着便宜，但 6月 −30.7%、跌破年线）会被排前面然后跌30%。
**铁律：过去基本面 ≠ 未来收益；趋势 + 当前市场风格才是主导。**

## Self-optimization loop (落盘 + 可复现闭环)
`build_data.py`(拉数) → `factor_ic.py`(测IC定权重方向) → `pick.py`(选股+回测)。
源数据落盘到共享文件夹，别只留群消息（群消息会被清，历史不可恢复 → 不编假数据补位）。

## Data pipeline (本环境已验证)
| 用途 | akshare 调用 | 备注 |
|---|---|---|
| 沪深300成分+快照(PE/PB/市值/换手) | `ak.index_stock_cons_sina(symbol="000300")` | 一次拿300只，含实时价 |
| 历史日线(前复权) | `ak.stock_zh_a_daily(symbol="sh600009", adjust="qfq")` | **Sina源，稳定** |
| 全市场代码名 | `ak.stock_info_a_code_name()` | 5529只 |

❌ **东财 `push2.eastmoney.com/api/qt/clist/get` 在本环境频繁 `RemoteDisconnected` / `TimeoutError` → 别用**
❌ `ak.stock_zh_a_spot`(腾讯) 70分片、极慢(>180s超时)
⚠️ 落盘用 **CSV**：pandas `to_parquet` 需 pyarrow/fastparquet，本环境未装
⚠️ 新浪限速 ~5只/秒，沪深300全历史(~260日/只)约 15 分钟

## Pitfalls (必查，真实踩过的)
1. **动量崩溃**：追半年涨幅最猛的票，60天后均值回归暴跌。v1 动量35%权重 → 回测超额 −5%。IC实测动量≈0时直接弃
2. **价值陷阱**：震荡/熊市"越便宜越跌"，低PB的IC可为负（本轮 −0.19）。不可盲信低估值
3. **小样本IC**：仅1年数据+4个回测时点，IC统计不稳。大盘因子 +0.31 可能是牛市偏样本，换风格翻转 → 须定期(每月)重估
4. **前视偏差**：回测用"当前快照PE/PB/市值"近似历史真值 → 高估表现。升级=拉F10历史估值
5. **单一持有期**：只测60日不够，需多持有期稳健性检验
6. **诚实报告**：回测负/跑输必须明示数字，不美化。用户要"看数据说话"

## 实证演进（本会话真实数字）
| 版本 | 权重假设 | 回测(4滚动点/持有60日) | 结论 |
|---|---|---|---|
| v1 | 价值25+动量35+质量20+规模20 | 策略 −7.83% vs 基准 −2.78%，超额 **−5.05%**，胜率27% | ❌ 动量当主力=噪音 |
| IC评估 | — | 市值IC +0.31(100%胜) / 低PB −0.19(0%) / 换手 +0.13 / 动量≈0 | 大盘+流动性风格 |
| v2 | 市值45+换手25−波动15+短反转15 | 策略 +26.0% vs 基准 −2.6%，超额 **+28.6%**，超额胜率100% | ✅ |

## References
- `references/ic-methodology.md` — 因子IC评估 + 滚动回测 + IC加权打分代码骨架
- `references/data-sources.md` — akshare 稳定/不稳定接口清单、限速、落盘格式
