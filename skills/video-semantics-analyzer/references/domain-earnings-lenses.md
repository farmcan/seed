# Earnings Domain Lenses

这些 lenses 只在 `--domain earnings` 时注入，用来分析财报、业绩会、公告、10-Q、10-K、8-K 和公司经营数据。

## 来源参考

- SEC EDGAR submissions API：借鉴按 CIK 获取公司 filing history 的稳定入口。
- SEC XBRL companyfacts API：借鉴以事实概念、单位、期间和 accession number 组织财务指标。
- FinRobot / FinGPT：借鉴财务报告、公告和金融文本任务的 taxonomy，但不把模型输出当事实。

## 财报证据边界

1. Filing fact：来自 SEC filing 或 XBRL 的数值、期间、表单和 accession。
2. Company statement：公司在公告或电话会中的说法，必须保留 attribution。
3. Creator interpretation：UP/作者对业绩的解释，只能标为创作者观点。
4. Market reaction：价格或情绪反应，需要行情或新闻来源支持。
5. Source gap：缺少 filing、电话会、guidance、分部数据、non-GAAP reconciliation 或同行对比。

## 分析要求

- 财报事实优先用 SEC / 交易所 / 公司 IR 来源；缺少 primary source 时标记需要核验。
- 指标必须保留 period、unit、form、filed date 和 accession number。
- 增长、下滑、margin、现金流、guidance、backlog、库存、capex、回购、债务等结论必须绑定具体指标或 source gap。
- 对行业影响只写需求、成本、库存、价格、资本开支、供应链、竞争格局等机制，不写交易建议。
