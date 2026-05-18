---
name: equity-research-report-analyzer
description: Parse sell-side/研究机构研报 into structured investment research claims and evidence for cross-check workflows.
---

# Equity Research Report Analyzer

Use this skill when reading analyst reports, broker research PDFs/notes, or研究策略稿。

## Core rules

- 把“作者观点”与“可核验事实”分离。
- 先提取报告事实层：覆盖范围、假设、指标、时间线、基准、对照组。
- 建立可追溯引用：`source_sections`、页码/段落、表格/图表编号、版本号。
- 将目标价、评级、区间、目标触发条件放入 `conviction_signals`，并标记不确定性。
- 对每条研究结论记录反向风险、反例场景和可验证失效条件。

## 输出结构建议

- `report_meta`
  - `issuer`, `ticker`, `report_date`, `period`, `as_of_date`, `rating`, `target_price_range`
- `research_claims`
  - `claim`, `evidence_refs`, `support`, `uncertainty`, `time_horizon`, `exit_or_invalidation`
- `sector_and_macro_thesis`
  - 行业机制链条、主题假设、政策预期、估值框架。
- `valuation_logic`
  - `primary_method`, `inputs`, `sensitivity_points`, `upside_downside_mechanism`。
- `catalysts`
  - `upside`, `downside`, `timing`, `monitoring_metric`。
- `risk_control`
  - `model_risk`, `forecast_risk`, `governance_risk`, `coverage_risk`。
- `evidence_gaps` / `open_questions`

## 输出禁区

- 不把 analyst target price 自动转成 Seed 投资建议。
- 不在未核验来源下提升 conviction 到 high。
- 不遗漏披露冲突：若报告与财报/新闻 facts 冲突，必须保留 `status` 为 `reported` 并附 `source_conflict`。
