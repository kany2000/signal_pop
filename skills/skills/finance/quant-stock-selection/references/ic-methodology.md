# 因子IC评估 + 滚动回测 代码骨架

## 因子IC (信息系数)
IC = 某时点因子值与"之后持有N日真实收益"的 Spearman 秩相关。
- IC>0 因子正向有效；IC<0 反向（如低PB在价值陷阱期）；IC≈0 纯噪音（如动量）。
- 在多个历史建仓点滚动测，取均值IC与"IC胜率"(IC>0的时点占比)。
- 权重按 |均值IC| 设定方向+幅度，不拍脑袋。

```python
import pandas as pd, numpy as np
from scipy.stats import spearmanr

def factors_at(asof, snap, hist):
    h = hist[hist['date'] <= asof]
    rows = []
    for sym, g in h.groupby('symbol'):
        g = g.sort_values('date'); c = g['close'].values
        if len(c) < 130: continue
        rows.append(dict(code=g['code'].iloc[0], symbol=sym, px=c[-1],
            ma120=c[-120:].mean(),
            r_6m=c[-1]/c[-120]-1, r_3m=c[-1]/c[-60]-1, r_1m=c[-1]/c[-20]-1,
            dvol=pd.Series(c).pct_change().tail(60).std(),
            rev_1m=-(c[-1]/c[-20]-1)))
    if not rows: return pd.DataFrame()
    f = pd.DataFrame(rows).merge(snap[['code','per','pb','mktcap','turnoverratio']], on='code', how='left')
    f['ep'] = 1/f['per'].replace(0, np.nan)
    f['bp'] = 1/f['pb'].replace(0, np.nan)
    f['logmktcap'] = np.log(f['mktcap'].clip(lower=1))
    return f

def fwd_ret(asof, hold, hist):
    fut = hist[hist['date'] > asof]
    d = sorted(fut['date'].unique())
    if len(d) < hold: return {}
    end = d[hold-1]; fut = fut[fut['date'] <= end]
    r = {}
    for sym, g in fut.groupby('symbol'):
        g = g.sort_values('date')
        if len(g) >= 2: r[sym] = g['close'].iloc[-1]/g['close'].iloc[0]-1
    return r

# 滚动建仓点(每20交易日一个), 持有60日
FACTORS = ['ep','bp','r_6m','r_3m','r_1m','dvol','logmktcap','turnoverratio']
ic_acc = {k: [] for k in FACTORS}
dates = sorted(hist['date'].unique())
for i in range(130, len(dates)-60, 20):
    asof = pd.Timestamp(dates[i])
    f = factors_at(asof, snap, hist); r = fwd_ret(asof, 60, hist)
    f['fwd'] = f['symbol'].map(r); f = f.dropna(subset=['fwd'])
    if len(f) < 50: continue
    for k in FACTORS:
        v = f[[k,'fwd']].dropna()
        if len(v) > 30:
            ic,_ = spearmanr(v[k], v['fwd']); ic_acc[k].append(ic)
# 打印 均值IC / IC胜率 / 方向
```

## IC加权打分 + 硬过滤
```python
def z(s):
    s = pd.to_numeric(s, errors='coerce'); sd = s.std()
    return (s-s.mean())/sd if sd and sd>0 else s*0

# 硬过滤: 淘汰下跌趋势(上海机场式)
f['pass'] = (f['r_6m'] > 0) & (f['px'] > f['ma120'])
# v2权重(按IC符号+幅度): 市值45 + 换手25 - 波动15 + 短反转15
f['score'] = (0.45*z(f['logmktcap']) + 0.25*z(f['turnoverratio'])
              -0.15*z(f['dvol']) + 0.15*z(f['rev_1m']))
picks = f[f['pass']].sort_values('score', ascending=False).head(15)
```

## 滚动回测(多建仓点平均)
同 fwd_ret 前推逻辑，对每个建仓点算 策略均值收益 / 基准(全样本等权)均值 / 超额alpha / 胜率。
正例: 本会话 v2 在4个时点 策略+26.0% vs 基准−2.6%，超额+28.6%，超额胜率100%。
反例: v1 动量35% → 超额−5.05%(动量崩溃)。
