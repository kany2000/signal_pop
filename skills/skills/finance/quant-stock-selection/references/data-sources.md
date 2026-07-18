# akshare 数据源（本环境 2026-07 实测）

## 稳定可用 ✅
| 用途 | 调用 | 延迟/备注 |
|---|---|---|
| 沪深300成分+实时快照(PE/PB/市值/换手率/涨跌幅) | `ak.index_stock_cons_sina(symbol="000300")` | 2.1s，300只一行返回，含 per/pb/mktcap/turnoverratio |
| 中证500成分 | `ak.index_stock_cons_sina(symbol="000905")` | 1.2s |
| 沪深300成分(代码名) | `ak.index_stock_cons_csindex(symbol="000300")` | 0.3s，仅代码名无估值 |
| 历史日线(前复权) | `ak.stock_zh_a_daily(symbol="sh600009", adjust="qfq")` | **Sina源最稳**，返回 date/open/high/low/close/volume/amount... 可裁剪 `.tail(260)` |
| 全市场代码名 | `ak.stock_info_a_code_name()` | 5529只，~9s(17分片进度条) |

secid 前缀：沪 `sh`/`1.`，深 `sz`/`0.`。

## 不稳定 ❌（本环境）
| 调用 | 现象 | 替代 |
|---|---|---|
| `ak.stock_zh_a_spot()` (腾讯) | 70分片，>180s超时 | 用 `index_stock_cons_sina` 拿快照 |
| 东方财富 `push2.eastmoney.com/api/qt/clist/get` | 频繁 `RemoteDisconnected` / `TimeoutError` | 用新浪日线+成分接口 |
| `ak.stock_financial_analysis_indicator(symbol="600009")` | 返回空 DataFrame | F10历史估值需另找源 |

## 落盘格式 ⚠️
- **用 CSV**，不要 parquet：pandas `to_parquet` 需 pyarrow/fastparquet，本环境未装 → `ImportError`
- 大循环逐只拉（新浪限速 ~5只/秒），沪深300全历史(~260日×300只) 约 15 分钟，一次性 `to_csv` 落盘（循环中不写）
- 读取：`pd.read_csv(path, dtype={'code':str}, parse_dates=['date'])`

## 估值字段来源
`index_stock_cons_sina` 的 `mktcap`/`nmc` 单位是**元**（非万元）：亿元 = mktcap/1e8。
per=PE, pb=PB, turnoverratio=换手率(%)。实时 trade=现价, changepercent=涨跌幅(%)。
