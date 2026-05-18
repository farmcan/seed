---
name: financial-statement-reviewer
description: Convert company filings or quarterly statements into evidence-grounded financial statements summary for Seed.
---

# Financial Statement Reviewer

Use this skill when processing official filings, quarterly reports, annual reports, or audited statement excerpts.

## Core rules

- 以事实为主：先产出数字和结构，再给观点。
- 只对已明确披露的范围写结论；缺失字段一律写 `null` 或 `unknown`。
- 财报数据仅作为“被报道事实”记账；不要把趋势结论写成投资建议。
- 保留会计口径（unit/period/category/GAAP/Non-GAAP/normalized）和时间区间。
- 若可追溯到 SEC/XBRL/EDGAR filing，优先保留 filing URL、accession、period、unit、form。
- 当指标口径不统一时要显式写 `source_gaps` 与 `measurement_conflict`。

## 输入约束

- 文本必须来自可核验来源（SEC filing、公司 IR、年度报告、季度更新、审计报告）。
- 允许混入财报图表摘要、经营回顾、利润表/现金流文字段。
- 对照 `B` 类型的长期方法论时，需保留可复用规则与适用边界，而不是原封装结论。

## 输出优先级

- 公司与期间元数据：`company`, `fiscal_period`, `period`, `currency`, `unit`, `report_type`, `publish_date`。
- 语义分层：`income_statement`, `balance_sheet`, `cash_flow`, `segment_data`（如有）。
- 指标快照：`revenue`, `gross_profit`, `gross_margin`, `operating_income`, `net_income`, `cash_flow_from_operations`, `free_cash_flow`, `cash_and_equivalents`, `total_assets`, `total_liabilities`, `equity`。
- 每个指标附带 `source_refs` 与 `period`。
- 驱动因素：`drivers` 与 `one_off_items` 分开。
- 质量控制：`evidence_gaps`, `inconsistencies`, `open_questions`。

## 禁止事项

- 不输出“必涨/必跌”类交易判断。
- 不把未披露的“目标价/估值区间”当作财报结论。
- 不把“季度增速好/坏”仅写成口号；必须给分子分母口径和同比环比对比。
