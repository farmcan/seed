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
- `ecosystem_implication`
  - `tooling_or_platform_playbooks`: 可用于迁移到上游工具厂/卖铲子场景的公司/机制线索（如建模平台、内容工具、应用分发/协同栈）。
  - `model_company_implication`: 模型厂商侧可复用机会（训练/推理效率、用户迁移、生态位变化）的可观察推断。
  - `compute_or_hardware_signal`: 是否改变算力需求结构的机制性线索（推理成本、芯片代工、云算力扩容、边缘部署）。
  - `model_or_chip_companies_to_watch`: 基于文本证据提及或逻辑映射到的同产业链公司名单。
  - `spillover_uncertainties`: 该启发链条的证据缺口与不确定因素。
- `evidence_gaps` / `open_questions`

## 输出禁区

- 不把 analyst target price 自动转成 Seed 投资建议。
- 不在未核验来源下提升 conviction 到 high。
- 不遗漏披露冲突：若报告与财报/新闻 facts 冲突，必须保留 `status` 为 `reported` 并附 `source_conflict`。
