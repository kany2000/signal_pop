# 东方财富 A股数据 API 参考

> 基于 002364 中恒电气 研究会话（2026-05-22）整理的实操 API 清单。

## 1. 实时行情 / 行情快照

```
GET https://push2.eastmoney.com/api/qt/stock/get
```

| Query Param | 值 | 说明 |
|---|---|---|
| `secid` | `0.{code}`（深）或 `1.{code}`（沪） | 市场代码 + 股票代码 |
| `fields` | `f43,f44,f45,f46,f47,f48,f57,f58,f60,f107,f116,f117...` | 字段 ID 列表 |

**常用字段映射（f-* 编号 → 含义）：**

| 字段 | 含义 | 示例 |
|---|---|---|
| f43 | 最新价（×100，即52.05表示5.205） | f43=5205 → 5.205元 |
| f44 | 最高价 | |
| f45 | 最低价 | |
| f46 | 今开 | |
| f47 | 成交量（手） | |
| f48 | 成交额（元） | |
| f57 | 股票代码 | "002364" |
| f58 | 股票名称 | "中恒电气" |
| f60 | 昨收 | |
| f107 | 涨跌额 | |
| f116 | 总市值 | 29333556168.0 |
| f117 | 流通市值 | 29049300708.0 |
| f152 | 涨跌停标记 | |
| f170 | 市盈率(PE) | |
| f173 | 是否亏损 | |
| f174 | 换手率 | |
| f175 | 量比 | |
| f176 | 振幅 | |
| f177 | 主力净流入（近5日JSON数组） | |
| f184 | 营收同比(%) | 7.79 |
| f185 | 净利润同比(%) | 22.89 |
| f189 | 上市天数 | |
| f190 | ROE(%) | |
| f191~f199 | 分项净买入 | |

**Headers 必须带 Referer:**
```
Referer: https://quote.eastmoney.com/
User-Agent: Mozilla/5.0 ...
```

---

## 2. F10 财务摘要（近8期）

```
GET https://emweb.securities.eastmoney.com/PC_HSF10/NewFinanceAnalysis/ZYZBAjaxNew
```

| Param | 值 |
|---|---|
| `type` | 0 |
| `code` | `sz{code}` 或 `sh{code}` |

**返回关键字段：**

| 字段 | 含义 |
|---|---|
| `TOTALOPERATEREVE` | 营业收入 |
| `PARENTNETPROFIT` | 归母净利润 |
| `KCFJCXSYJLR` | 扣非净利润 |
| `EPSJB` | 基本EPS |
| `BPS` | 每股净资产 |
| `ROEJQ` | 加权ROE |
| `ROIC` | ROIC |
| `XSMLL` | 销售毛利率(%) |
| `XSJLL` | 销售净利率(%) |
| `ZCFZL` | 资产负债率(%) |
| `LD` | 流动比率 |
| `SD` | 速动比率 |
| `JYXJLYYSR` | 经营现金流/营收 |
| `TOTALOPERATEREVETZ` | 营收同比(%) |
| `PARENTNETPROFITTZ` | 净利润同比(%) |
| `KCFJCXSYJLRTZ` | 扣非净利润同比(%) |
| `DJD_TOI_QOQ` | 营收环比(%) |
| `DJD_DPNP_QOQ` | 净利润环比(%) |

---

## 3. F10 公司概况

```
GET https://emweb.securities.eastmoney.com/PC_HSF10/CompanySurvey/PageAjax?code=SZ{code}
```

返回字段：`jbzl`（基本信息）、`fxxg`（发行相关）

**jbzl 关键字段：**
| 字段 | 含义 |
|---|---|
| `ORG_NAME` | 公司全称 |
| `SECURITY_TYPE` | 股票类型（深交所主板A股等） |
| `EM2016` | 行业细分（东财分类） |
| `INDUSTRYCSRC1` | 证监会行业分类 |
| `ORG_PROFILE` | 公司简介（很长，中文） |
| `BUSINESS_SCOPE` | 经营范围 |
| `PRESIDENT` | 总裁 |
| `LEGAL_PERSON` | 法人代表 |
| `CHAIRMAN` | 董事长 |
| `REG_CAPITAL` | 注册资本（万元） |
| `EMP_NUM` | 员工人数 |
| `ORG_WEB` | 官网 |

---

## 4. 股东结构

```
GET https://emweb.securities.eastmoney.com/PC_HSF10/ShareholderResearch/PageAjax?code=SZ{code}
```

返回 key：`sdgd`（前十大股东）、`sdltgd`（前十大流通股东）、`ltgf`（流通股份）、`gdrs`（股东人数）、`jjcg`（基金持仓）、`jgcc`（机构持仓）

**sdgd 关键字段：**
| 字段 | 含义 |
|---|---|
| `HOLDER_RANK` | 排名 |
| `HOLDER_NAME` | 股东名称 |
| `HOLD_NUM` | 持股数量 |
| `HOLD_NUM_RATIO` | 持股比例(%) |
| `HOLD_NUM_CHANGE` | 持股变化（不变/增/减） |

**gdrs 关键字段：**
| 字段 | 含义 |
|---|---|
| `HOLDER_TOTAL_NUM` | 股东总户数 |
| `HOLD_FOCUS` | 持股集中度（非常分散/集中等） |

---

## 5. 已知踩坑

- `push2.eastmoney.com` 实时价格 f43 是 ×100 格式（5205 = 5.205元）
- `datacenter-web.eastmoney.com` 的 RPT 报表名称容易变更（如 `RPT_F10_FINANCE_GSZB` 已失效），直接用 F10 AJAX 接口更稳定
- `emweb.securities.eastmoney.com` 接口 code 参数必须带 `SZ` 或 `SH` 前缀
- 深交所股票 secid 前缀是 `0.`，沪交所是 `1.`
- `ShareholderResearch` 返回的 `jjcg` 包含基金持仓，可估算机构筹码集中度
- 公告接口 `np-anotice-stock.eastmoney.com` 对部分股票分类参数要求严格，可用 `ann_type=CXSZA%2CSZSA` 或改用 F10 页面 AJAX

---

## 6. 研究流程（推荐顺序）

1. **行情快照** → push2.eastmoney.com（实时价格、涨跌幅、市值）
2. **财务摘要** → emweb F10/NewFinanceAnalysis（8期财务数据，营收/净利/ROE/现金流）
3. **公司概况** → emweb F10/CompanySurvey（主营业务、客户、行业、简介）
4. **股东结构** → emweb F10/ShareholderResearch（控股东、机构持仓、股东户数趋势）
5. **近期公告** → eastmoney 公告搜索（看有无重大事项）

**财务分析时优先关注：** 营收同比、净利润同比、扣非净利润、毛利率趋势、资产负债率、经营现金流净额
