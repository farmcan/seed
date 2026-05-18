---
name: finance-outlook-analyzer
description: 结构化归纳财经观点草案为“观点-情景-风险收益”报告输入，保留可验证事实边界并输出第一性视角与行业传导。
---

# 财经观点前瞻（Finance Outlook）分析 Skill

用于将财报/观点 digest 转为可复用的前瞻框架。输入可来自

- `*.finance-digest.*.json`
- `*.finance-digest.news-context.json`
- `*.finance-digest.priced.json`
- `equity-research` 的 `first_principles` / `peer_context`（可选）

## 核心目标

1. 把 Creator 观点事件（`viewpoint_events`）转成可追溯的风险收益图景，而不是直接给交易建议。  
2. 输出“上行空间 / 下行空间 / 风险收益比 / 风险边界 / 验证缺口 / 关键情景”。  
3. 将第一性视角（商业模式与竞争结构）与市场机制（AI 生产、AI Coding、算力链路）统一进报告骨架。  
4. 强制保留时间、来源与不确定性，避免模型自我延展。

## 输入要求

- `viewpoint_events`：每条事件应至少包含 `event_id, instrument, action, direction, conviction, event_outcomes`。
- `peer_context`：同业/标的上下文（可为空）。
- `first_principles`：商业本质字段（可为空）：
  - `business_model, revenue_logic, core_differentiators, competitors`
  - `competitive_pressure, customer_dependency, single_customer_risk`
  - `aicoding_or_automation_risk, overseas_revenue_ratio, internationalization_progress`
  - `ecosystem_implications`
- `methodology_signals` / `open_questions` / `source_gaps`：用于后续复核和持续学习。

## 输出结构（草案）

- `meta`
  - `generated_at, owner, platform, window, source_digest_path, not_investment_advice`
- `totals`
  - `events, priced_events, news_context_events, assets, software_assets, aigc_assets, overall_upside, overall_downside, overall_risk_reward, direction_bias`
- `asset_rollups`（按标的聚合）
  - `event_count, action_distribution, direction_distribution`
  - `risk_reward_ratio, confidence, evidence_ratio, downside_pressure, upside_support`
  - `latest_return, upside, downside, max_drawdown`
  - `target_prices: {upside_pct, upside_target, downside_pct, downside_target}`
  - `price_context: {status, published_close, latest_close, published_price_date, latest_price_date, ...}`
  - `top_risks, software_terms, aigc_terms, is_software_sector`
- `overall_price_targets`
  - `asset, latest_close, latest_price_date, published_close, published_price_date`
  - `overall_upside_target, overall_downside_target, overall_upside, overall_downside`
- `first_principles`
  - 透传核心字段 + `first_principles_uncertainties`
- `risk_reward_profile`
  - `macro_signals, industry_outlook, aicoding_signals, news_context_signals`
- `validation`
  - `source_gaps, open_questions, risk_flags`

## 强制规则

- 不输出投资建议，不输出“买入/卖出”交易执行结论。
- 缺少 `price_context` 或 `ticker` 时，标注 `insufficient_price_context` / `missing_ticker`，不要猜价格。  
- 对高不确定字段标注 `evidence` 与 `uncertainty`，不得把 `AI Coding` 当作自动“利空/利多”结论。  
- 允许输出 `AI Coding` 风险观察点，但必须给“可核验判定指标”（例如人均毛利、交付效率、续费率变化）。  
- 每条场景必须可回溯到事件集合中的来源项（`event_id`, `evidence_refs`, `risk_flags` 或 `news_context`）。

## 报告映射建议（供 report renderer）

- `结论先说`：`overall_orientation`, `overall_upside/downside`, `overall_risk_reward`。
- `商业本质（第一性）`：`first_principles` 的四象限（模式-能力-竞争-风险）。  
- `标的级风险收益表`：`asset_rollups` + `target_prices + price_context`。  
- `场景口径`：`priced` 事件 + 事件 horizon 极值映射到 `latest_close`。
- `AI Coding 结构性变量`：仅作为结构性风险观察，不当作模型结论。

## 复核清单（输出后）

- 价格链路是否完整（`status: priced` / `missing_*`）  
- 同业对照是否齐备（peer/ticker映射是否闭环）  
- 时间与事实是否齐套（发布日、覆盖窗、事件粒度、证据引用）  
- 下行触发机制是否写明（不是只写结果）

