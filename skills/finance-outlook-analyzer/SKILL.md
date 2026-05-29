---
name: finance-outlook-analyzer
description: 结构化归纳财经观点草案为“观点-情景-风险收益”报告输入，保留可验证事实边界并输出第一性视角与行业传导。
---

# 财经观点前瞻（Finance Outlook）分析 Skill

用于将财报/观点 digest 转为可复用的前瞻框架。该 skill 的关键原则是：**未来上行/下行空间必须来自真实市场锚点与可引用来源，不能由模型随手估计，也不能把事件后验涨跌直接当目标价**。输入可来自

- `*.finance-digest.*.json`
- `*.finance-digest.news-context.json`
- `*.finance-digest.priced.json`
- `equity-research` 的 `first_principles` / `peer_context`（可选）

## 核心目标

1. 把 Creator 观点事件（`viewpoint_events`）转成可追溯的风险收益图景，而不是直接给交易建议。  
2. 输出“上行空间 / 下行空间 / 风险收益比 / 风险边界 / 验证缺口 / 关键情景”。  
3. 将第一性视角（商业模式与竞争结构）与市场机制（AI 生产、AI Coding、算力链路）统一进报告骨架。  
4. 强制保留时间、来源与不确定性，避免模型自我延展。
5. 显示方法论来源与自检：报告必须说明借鉴的成熟研报/产品框架、目标价分歧和数据覆盖度。
6. 面向普通用户解释报告价值：它帮用户少搜资料、看清赔率与分歧、形成复核清单；不替用户下单。
7. 公司识别要像正式报告：如果有官方或可授权来源，补充 logo、产品图、核心产品名和来源链接；没有来源时宁可写缺口，不随手抓无来源图片。

## 无上下文交付流程

当用户只给一个公司、ticker 或“帮我做股价/业务/竞争/未来走势分析”时，即使没有任何上下文，也按下面顺序交付。目标是让另一个 AI agent 只读本 skill 就能复现完整产物：

1. 先读本仓库 `agents.md`、`docs/architecture.md`、`docs/todos.md` 和本 skill，确认财经 lint、非投资建议、primary source 优先和 `library/` 私有产物规则。
2. 做市场与业务调研，必须把 facts、reported claims、analyst view、interpretation 和 source gaps 分开。
3. 写入结构化 digest：
   - `library/distilled/<slug>.finance-digest.news-context.json`
   - 必须包含 `peer_context`、`first_principles`、`viewpoint_events`、`market_context`、`market_scenarios`、`open_questions`、`source_gaps`、`methodology_signals`。
4. 跑现有报告命令：
   - `.venv/bin/seed build-finance-outlook-report library/distilled/<slug>.finance-digest.news-context.json`
   - 生成 `library/distilled/<slug>.finance-outlook.json` 和 `library/reports/<slug>.finance-outlook-report.html`。
5. 如果用户关心“主营业务、收入来自谁、市场多大、竞争多大、未来走势”，再额外写：
   - `library/reports/<slug>.business-analysis.md`
   - `library/reports/<slug>.business-analysis.html`
   - HTML 顶部必须链接对应 `finance-outlook-report.html`，避免用户在两个报告之间迷路。
6. 最小验证：
   - 用 `rg` 确认 HTML 中出现当前价、非投资建议、关键时间节点、目标价/情景和来源链接。
   - 如果只改 `library/` 产物，不默认跑全量 pytest；如果改代码或 renderer，再跑 `.venv/bin/ruff check .` 和对应定向测试。
7. 汇报时给用户本地 HTML/JSON/Markdown 绝对路径，并用一句话说明数据口径与限制。

`library/` 产物默认不提交。只有用户明确要求归档样例，才讨论是否提交脱敏 demo；否则 commit 只包含 skill、代码或文档改动。

## 用户价值层

报告必须先回答普通用户的真实需求，而不是只堆专业字段：

- 我现在看这只股票，最该先知道什么？
- 上行/下行空间从哪来，靠不靠谱？
- 下一次验证点是什么，什么时候可能重新定价？
- 最大坑在哪里，哪些信息会推翻当前判断？
- 我能不能把这份报告分享给别人，让对方快速理解？

建议在 HTML 顶部输出 `user_value`：

- `headline`：一句话说明报告用途，例如“帮你判断是否值得继续研究，而不是替你下单”。
- `cards[]`：30 秒判断、来源数量、下一验证点、目标价分歧。
- `audience[]`：普通用户、内容创作者、投研助理/Agent。
- `user_jobs[]`：省检索时间、降低误判、形成跟踪清单、便于分享。
- `limitations[]`：不提供买卖指令、不把目标价当确定预测、不替代主源/终端/个人风险判断。

竞品启发：

- TipRanks 用“make smarter, data-driven investment decisions”吸引普通用户，核心是把机构工具平民化。
- Seeking Alpha 用 Quant Rating / Factor Grades 让用户快速筛选或排除股票，价值是“instant characterization”和研究入口。
- Simply Wall St 用视觉摘要和 narrative update 降低复杂财务数据理解门槛。
- Finimize 类产品强调几分钟理解要点，适合移动端和普通用户持续学习。

## 成熟研报方法论映射

每次生成前瞻报告时，至少把下面方法论映射进输出结构，而不是只在聊天里解释：

- CFA equity valuation：理解业务、预测经营、选择估值模型、转成估值/情景，并让事实、观点和关键假设可被读者质疑。
- Morningstar moat / fair value / uncertainty：商业本质、护城河、盈利持续性、估值和不确定性必须一起看。
- TIKR / Koyfin estimates workflow：历史实际值和未来一致预期并排；保留 analyst count、平均/中位、目标价高低、估值倍数和趋势。
- Quartr first-party IR workflow：财报、电话会、PPT、公告和 transcript 优先结构化，关键数字要能回到一手材料或清晰的二级来源。
- FinRobot equity report pipeline：数据抓取 -> 财务预测/估值/同业比较 -> 多模块分析 -> HTML/PDF 报告；Seed 暂做轻量版，但模块边界要类似。
- SEC analyst-report caution：分析师目标价是外部观点，不是保证；必须提示不要只依赖评级，要核验公司披露、风险和利益冲突。

## 必做检索流程

生成单个上市公司前瞻报告前，先完成以下检索并写入 `market_context`：

1. 行情定位：当前价、价格日期、今日涨跌、近一周、近一月、近一年、52 周最高/最低、成交量、市值、PE/forward PE（可得则写）。
2. 目标价与估值：至少一个分析师目标价聚合源，记录平均/中位/最高/最低目标价、样本数、评级分布和来源日期。
3. 财报主源：公司 IR、交易所公告、年报/季报/业绩 PPT，记录收入、利润、分部毛利、现金、管理层指引和下一次财报日期。
4. 近期新闻事实：过去 1-3 个月内与股价相关的产品、订单、监管、成本、回购、融资、事故、安全、竞争动作。
5. 政策与行业：对公司收入/利润有直接传导的国家政策、补贴、关税、监管、行业价格战或供给变化。
6. 同业对照：至少 3 个同业或替代品，说明比较口径，例如估值、毛利、增速、产品周期、海外化。
7. 一致预期分歧：计算目标价平均/中位/高/低相对当前价的收益、目标价跨度、平均/中位差和样本数；分歧高时必须降权平均目标价。
8. 公司与产品识别：公司官网/IR/品牌素材页/产品页中的 logo、核心产品图、产品名、业务线图片；每张图片必须记录 `source_url/source_title/usage_note`，不得把搜索结果缩略图当来源。
9. 数据覆盖度：自检行情锚点、历史价格、目标价/一致预期、财报主源、催化事件、商业本质/竞争、公司视觉资产是否齐全；缺失写 `source_gaps`。

## 业务分析补充报告

当用户追问“主营业务 / 营收来自谁 / 市场有多大 / 竞争怎么样 / 后续走势”时，必须补一份可阅读业务分析报告，而不是只在聊天里解释。报告至少包含：

- `主营业务到底是什么`：用公司披露的分部收入、同比、占比和产品线说明，不把旧印象当事实。
- `营收主要来自谁`：区分客户类型、付费用户、广告主、企业/商家、区域和是否披露大客户集中度；未披露就写未披露。
- `市场有多大`：至少拆成直接市场、上游需求池、相邻 AI/软件市场三层；每个规模数字必须有来源和日期。
- `竞争有多大`：按同业、替代品、平台生态、基础模型/通用助手分层；写出“压迫哪个业务线”。
- `AI 创作工具竞争现状`：对 AIGC/内容生产/设计/视频工具公司必须单列当前竞品状态，至少覆盖 Adobe、Canva、CapCut、基础模型/通用助手，并按公司实际业务补 Picsart、Photoroom、B612、Snow、BeautyPlus、Runway、Kling、Veo、Sora、OpenAI Images、Gemini/Flow 等相关项。
- `未来股价可能的几种走势`：情景表必须绑定当前价、目标价/支撑位、触发条件、要验证的经营指标；不要给买卖指令。
- `接下来最该盯的指标`：把后续复核转成清单，例如订阅用户、ARR、AI credits 收入/成本、毛利率、海外 ARPU、产品线占比、竞争发布。
- `来源`：所有关键数字和竞品状态列出 URL；来源不足写 source gaps。

业务分析 HTML 不要求复杂前端，但要可读、可分享、能打开；表格要保留，顶部要写非投资建议，并链接 finance outlook HTML。

优先来源顺序：

- primary source：公司 IR、交易所、SEC/EDGAR、政府/监管部门、交易所行情。
- structured market source：StockAnalysis、Yahoo Finance、Investing、TipRanks、ValueInvesting.io 等，只能作为行情/目标价聚合参考。
- media/research：Reuters、Bloomberg、WSJ、CNBC、Cailian/Caixin、券商研报；必须标注是 reported claim 或 analyst view。

每个数字必须保留 `source_refs`，包含 `title, url, accessed_at, note`。找不到来源就写 `source_gaps`，不要补一个看起来顺的数字。

## 检索增强策略

如果普通搜索结果不足，不要停在“没找到”。按下面顺序扩大检索面，并把失败也写入 `source_gaps`：

1. 先做查询矩阵，而不是单 query：
   - 中文名 / 英文名 / ticker / 股票代码四套关键词都搜。
   - 组合字段：`目标价`、`price target`、`研报`、`research report`、`业绩`、`annual results`、`operating update`、`gross margin`、`AI`、`policy`、`subsidy`。
   - 时间词：当前年份、最近季度、`Q1/Q2/H1/FY`、公告日、财报日。
   - 站点词：`site:ir.<company>`、`site:hkexnews.hk`、`site:pdf.dfcfw.com`、`site:finance.sina.com.cn`、`site:investing.com`、`site:stockanalysis.com`。
2. 分层抓取来源：
   - `primary`：公司 IR、HKEXnews/SEC/交易所、政府政策原文。
   - `structured`：StockAnalysis、ValueInvesting、FMP、Yahoo Finance、Investing、TipRanks。
   - `research/media`：券商 PDF、Reuters/Bloomberg/WSJ、Sina/智通/财联社等转载研报。
3. 做交叉验证：
   - 行情至少 1 个价格源 + 1 个历史 OHLC 源。
   - 目标价至少 1 个聚合源；如果有券商报告，要把券商、日期、评级、目标价、估值方法、核心假设分开写。
   - 财务数字优先用公司公告或交易所披露；二级来源只能补充，必须标 `reported claim`。
4. 检索工具不足时的增强选项：
   - Brave Search API：独立 web index，适合网页/新闻广覆盖和 agentic search。
   - Exa：适合 company / news / research paper / financial report category search、highlights 和 deep structured search。
   - Tavily：适合带日期范围、domain include/exclude、raw markdown/text content 的研究型检索。
   - FMP：适合 analyst estimates、price target、financial statements、earnings transcripts 等结构化 API。
   - SEC EDGAR / HKEXnews：作为美股/港股主源，不能被二级网页替代。
5. 输出 `search_plan` / `search_log`：
   - 记录每轮 query、检索时间、include/exclude domain、候选 URL、采用/拒绝原因。
   - 每个关键 metric 需要 `metric -> source_ref_id -> accessed_at -> confidence -> limitation`。

## 推荐来源清单

后续遇到类似“某公司股价前瞻 / 风险收益 / 目标价 / K 线”的需求，优先从下面来源检索。能用 primary source 就不用二级网页；二级网页可以用于 demo、交叉验证或补齐公开数据，但必须标注限制。

### 行情与历史价格

- 交易所/官方行情：
  - 港股：HKEX 市场数据、HKEXnews 公告页。
  - 美股：Nasdaq / NYSE / company IR 的 investor data，必要时用 SEC filing 核验股本和财务。
  - A 股：上交所、深交所、北交所、巨潮资讯。
- 公开二级行情源：
  - StockAnalysis：适合快速拿当前价、52 周区间、近 1 年表现、PE、下一财报日期、历史 OHLC。
    - 示例：`https://stockanalysis.com/quote/hkg/1810/`
    - 示例：`https://stockanalysis.com/quote/hkg/1810/history/`
  - Yahoo Finance：适合价格、历史价格、财务摘要和公司概要交叉验证。
  - Investing.com / MarketScreener / TradingView：适合行情、技术区间和新闻交叉验证。
  - Stooq：适合低成本 CSV baseline；ticker 必须显式 mapping，不猜。

### 目标价与卖方预期

- ValueInvesting.io：适合拿 12 个月平均/中位/最高/最低目标价、样本数、评级分布。
  - 示例：`https://valueinvesting.io/1810.HK/estimates`
- Financial Modeling Prep：适合程序化抓 analyst estimates、price target summary、financial statements、earnings transcripts；需要 API key，客户级使用要核对授权。
- TipRanks：适合目标价、评级、分析师动作和历史新闻交叉验证。
- Investing.com / MarketScreener / Bloomberg / Reuters：可作为目标价、评级变化或券商动作的辅助来源。
- 券商研报：优先保留发布日期、券商、分析师、目标价、评级、估值方法、核心假设；没有原文时只能写 reported claim。

### 财报、公告与公司主源

- 公司 IR：年报、季报、业绩 PPT、电话会 transcript、管理层指引。
- 交易所公告：
  - 港股：HKEXnews / 公司公告。
  - A 股：巨潮资讯、上交所、深交所、北交所。
  - 美股：SEC EDGAR `10-K / 10-Q / 8-K`、companyfacts / XBRL。
- 财务镜像源只能辅助，不替代 primary source；必须标注是否 mirror。

### 新闻、行业与政策

- 新闻事实：Reuters、Bloomberg、WSJ、CNBC、财新、财联社、第一财经、公司所在行业的垂直媒体。
- 中国 EV/智能终端：CnEVPost、36Kr、晚点、汽车之家/懂车帝等可做行业事实补充，但要区分媒体报道与官方数据。
- 政策/监管：国务院、商务部、发改委、工信部、财政部、证监会、交易所、地方政府官网；政策数字优先用官方原文。

### AI / AIGC / 软件结构变量

- 模型和平台：OpenAI、Anthropic、Google、Meta、阿里云、腾讯云、字节等官方发布、定价页、模型卡和开发者文档。
- AI Coding / 软件效率：OpenAI、Anthropic、GitHub、Cursor、JetBrains、Replit 等官方数据或产品更新；二级媒体只能作为 reported claim。
- 算力与硬件传导：NVIDIA、AMD、TSMC、ASML、Broadcom、Qualcomm、MediaTek、存储厂商财报和行业数据。
- AI 创作竞争：
  - Adobe：Creative Cloud、Firefly、Photoshop/Premiere/Lightroom/Express、Firefly Services、AI assistant/agent、commercially safe models。
  - Canva：Canva AI、Visual Suite、Canva Design Model、Brand Intelligence、connectors、team collaboration、Canva Code。
  - CapCut/字节：AI video generator、auto captions、background remover、AI templates、avatars、Seedance/Dreamina、Kling/Veo/Sora 等模型接入、TikTok/短视频生态。
  - 基础模型：OpenAI Images/Sora、Google Gemini/Flow/Veo、Runway、Kling、Luma、Midjourney、Black Forest Labs 等，重点看它们是否把原本可收费的图片/视频编辑功能商品化。
  - 垂直应用：Picsart、Photoroom、Freepik、B612、Snow、BeautyPlus、Remini、Pixelcut、Cutout 等，用于判断移动影像和电商图场景是否被替代。

## 来源保存要求

每次生成公司报告时，必须把来源沉到结构化 artifact，而不是只写在聊天里：

- `market_context.source_refs[]`：每个来源记录 `title, url, accessed_at, note`。
- `market_context.price_source_note`：当前价来自哪里、价格时间、是否 delayed、是否二级行情源。
- `market_context.target_price_source_note`：目标价来自哪里、样本数、目标价期限和聚合口径。
- `market_context.data_quality_notes[]`：需要复核的限制，例如“客户级交付前用 HKEX/券商终端/付费行情源复核”。
- `market_context.saved_artifacts`：记录本地输入 JSON、输出 JSON、HTML report、source-lineage markdown 等路径。
- `market_context.next_events[]`：未来节点必须尽量写具体日期；如果只有季度/半年窗口，要写成“估计窗口 + 推断依据 + 待 IR/交易所确认”，不要只写 `2026-H1 report` 这类不可操作标签。
- `market_context.historical_events[]`：已发生节点必须包含日期、事件、类别、相关性、来源标题和来源 URL；财报、经营更新、研报目标价、重大竞品发布都可作为事件。
- `market_context.competitive_watch[]` 或业务分析报告中的竞品表：记录当前竞争动作、影响业务线、来源和不确定性。
- `company_assets` / `visual_assets`：记录 `logo`、`product_images/products`、`product_names`、`source_refs`、`usage_note`；只使用官方、公司 IR、产品页、媒体包或明确可引用的来源。
- 如有必要，额外写 `library/reports/<slug>.source-lineage.md`，用人工可读方式列出股价、历史 K 线、目标价、财报、政策和新闻来源。

### 时间节点解释规则

报告和回复都要区分节点类型：

- `trading_mechanics`：除息日、登记日、派息日、拆股、复牌等。它们可能造成短线价格或资金行为变化，但不等于主营业务变化。除息日要解释“从该日买入通常不再享有本次股息”，并在可得时估算 `dividend / current_price` 的机械影响量级。
- `earnings_validation`：年报、半年报、季度经营更新、业绩会。它们是最重要的基本面复核节点，要列出具体要验证的收入、订阅、ARR、毛利、现金流、区域/产品线指标。
- `competitive_release`：同业产品、基础模型、平台政策或价格变化。它们影响功能溢价和估值倍数，但要说明传导机制，不要直接写成确定利空。
- `analyst_view`：券商目标价、评级调整、一致预期变化。它们是外部观点，不是保证。

如果用户问“这个时间大概是什么时候”，必须先查公司 IR/交易所/可靠财报日历；如果只有第三方日历，写 `estimated` 或 `TBA` 并保留来源。

## 输入要求

- `viewpoint_events`：每条事件应至少包含 `event_id, instrument, action, direction, conviction, event_outcomes`。
- `peer_context`：同业/标的上下文（可为空）。
- `first_principles`：商业本质字段（可为空）：
  - `business_model, revenue_logic, core_differentiators, competitors`
  - `competitive_pressure, customer_dependency, single_customer_risk`
  - `aicoding_or_automation_risk, overseas_revenue_ratio, internationalization_progress`
  - `ecosystem_implications`
- `methodology_signals` / `open_questions` / `source_gaps`：用于后续复核和持续学习。
- `market_context`：真实检索后的市场锚点：
  - `ticker, currency, current_price, as_of`
  - `day_change_pct, one_week_return_pct, one_month_return_pct, one_year_return_pct`
  - `fifty_two_week_low, fifty_two_week_high, pct_from_52_week_low, pct_to_52_week_high`
  - `analyst_target_average, analyst_target_median, analyst_target_low, analyst_target_high`
  - `analyst_target_average_upside_pct, analyst_target_low_downside_pct`
  - `next_events`
    - 每条包含 `date, event, relevance, source_title/source_url`；可选 `event_type, estimated, validation_points, base/upside/downside_triggers`
  - `historical_events` / `chart_events`：过去 3 年内值得贴到 K 线上的事实事件，包括财报、产品发布/交付、重大研报评级变化、政策、宏观/战争/油价冲击、AI/模型能力节点；每条至少包含 `date`、`event/title`、`category`、`relevance`、`source_url/source_title`
  - `competitive_watch`：当前竞品或替代品状态，记录 `competitor, date/as_of, move, affected_business_line, pressure_level, source_refs, uncertainty`
  - `historical_prices`：默认至少 3 年日线 OHLC 序列，用于“历史 K 线 + 关键时间点 + 情景路径”；必须来自行情源并记录来源；不足 3 年时必须写 `historical_price_coverage` 和数据缺口，不得用短窗口冒充长期价格语境
  - `price_source_note, target_price_source_note, data_quality_notes, saved_artifacts`
  - `source_refs`
- `company_assets` / `visual_assets`：公司与产品识别资产（可为空）：
  - `logo: {title, url, alt, source_url, source_title, license_note}`
  - `product_images` / `products: [{title, url, caption, source_url, source_title, license_note}]`
  - `product_names[]`
  - `source_refs[]`
  - `usage_note`：说明图片只用于报告识别，客户级交付前要复核来源和使用权
- `market_scenarios`：未来空间的主输入。优先用真实目标价、52 周位置、估值倍数或财报敏感性构建，不要用 `event_outcomes` 代替。
- `consensus_diagnostics`：一致预期分歧诊断：
  - `target_low/average/median/high`
  - `analyst_sample_size, rating`
  - `returns.low/average/median/high`
  - `dispersion_pct, average_median_gap_pct, conflict_level`
  - `notes, source_note`
- `research_methodology`：成熟研报方法论映射和交付自检：
  - `frameworks[]: {name, borrowed_rule, how_seed_uses_it, source_url}`
  - `coverage[]: {label, score, present, total, note}`
  - `pipeline[], self_review_questions[]`
  - `overall_score, source_gaps_count, open_questions_count`

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
- `market_context`
  - 行情、目标价、52 周区间、下一个催化点、来源引用
- `company_assets`
  - logo、产品图、核心产品名、视觉来源和使用限制
- `consensus_diagnostics`
  - 目标价分歧、样本数、平均/中位差、低/均/中/高目标价的相对收益
- `research_methodology`
  - 成熟研报方法论映射、数据覆盖度、交付自检问题
- `scenarios`
  - `method: market_valuation_context` 时，基准/上行/下行来自市场锚点
  - `method` 缺失时才允许退回事件后验
- `first_principles`
  - 透传核心字段 + `first_principles_uncertainties`
- `risk_reward_profile`
  - `macro_signals, industry_outlook, aicoding_signals, news_context_signals`
- `validation`
  - `source_gaps, open_questions, risk_flags`
- `business_analysis`（可选，但用户询问业务/市场/竞争时必须输出到独立 Markdown/HTML）
  - `revenue_segments, customer_sources, market_size_layers, competition_layers, competitive_watch, stock_paths, metrics_to_watch, sources`

## 强制规则

- 不输出投资建议，不输出“买入/卖出”交易执行结论。
- 缺少 `price_context` 或 `ticker` 时，标注 `insufficient_price_context` / `missing_ticker`，不要猜价格。  
- 对高不确定字段标注 `evidence` 与 `uncertainty`，不得把 `AI Coding` 当作自动“利空/利多”结论。  
- 允许输出 `AI Coding` 风险观察点，但必须给“可核验判定指标”（例如人均毛利、交付效率、续费率变化）。  
- 允许输出 `AI 创作工具竞争` 风险观察点，但必须具体说明压迫的是哪个收入/产品线、传导机制是什么、什么指标能验证；不要只写“竞争激烈”。
- 每条场景必须可回溯到事件集合中的来源项（`event_id`, `evidence_refs`, `risk_flags` 或 `news_context`）。
- 如果有 `market_context/market_scenarios`，报告必须优先展示市场/估值口径；`event_outcomes` 只表示观点发布后的后验表现。
- 上行空间推荐口径：当前价到平均/中位目标价、52 周高点、乐观目标价或明确估值情景。
- 下行空间推荐口径：当前价到 52 周低点、低位目标价、估值压缩情景或财报失速情景。
- 风险收益比必须说明分子和分母来源，例如“平均目标价上行 / 最低目标价下行”或“52 周高点上行 / 52 周低点下行”。

## 报告映射建议（供 report renderer）

- `结论先说`：`overall_orientation`, `overall_upside/downside`, `overall_risk_reward`。
- `商业本质（第一性）`：`first_principles` 的四象限（模式-能力-竞争-风险）。  
- `公司与产品识别`：`company_assets`，展示 logo、核心产品图、产品名和来源；图片是辅助理解业务的视觉证据，不替代财报/公告事实。
- `标的级风险收益表`：`asset_rollups` + `target_prices + price_context`。  
- `市场锚点`：`market_context`，必须展示 52 周、近 1 周/月、目标价、下一财报/产品/政策事件。
- `成熟研报方法论映射`：展示 CFA、Morningstar、TIKR/Koyfin、Quartr、FinRobot、SEC 等参考框架如何落到本报告。
- `一致预期与目标价分歧`：显示低/均/中/高目标价、样本数、分歧等级和目标价跨度；分歧大时明确提示均值不可靠。
- `数据覆盖度 / 交付自检`：展示行情、历史价格、目标价、财报主源、催化、商业本质等覆盖度；只评价数据齐全度，不评价结论正确性。
- `数据口径与保存`：说明股价/目标价来源、访问时间、二级数据限制和本地 artifact 保存路径。
- `历史 K 线 + 关键时间点 + 情景路径`：如果 `market_context.historical_prices` 存在，历史 K 线必须交给成熟金融图表库渲染（当前默认 vendored TradingView Lightweight Charts），不要手写 SVG K 线；默认至少展示约 3 年日线 OHLC，并在图上显示覆盖起止日期、交易日数和 `historical_price_coverage`，不足 3 年时醒目标注数据缺口。图上事件采用 TradingView / Yahoo / Highcharts Stock 常见的 event marker / flag 形态：历史 `historical_events` 标在 K 线对应交易日，未来 `next_events` 放在同轴事件时间线；事件时间线必须用同一日期范围从历史 K 线起点延伸到未来观察窗，标出“当前 / 最后一根真实 K 线”，并把未来事件、关注点、上行/基准/下行情景触发写在时间坐标上。图下事件列表承载来源链接和影响机制。目标价采用 TradingView Price Target 类似口径，展示当前价、目标/支撑水平线，以及“当前价 -> 外部目标/支撑锚点”的情景路径；未来情景路径可按日采样以保证未来 12 个月在横轴上有可见宽度，但必须标注为“非K线”，只能说明哪些事件可能让价格向哪个锚点靠拢，不得生成伪未来每日 K 线、粗箭头或大面积扇形。
- `场景口径`：优先 `market_scenarios`；缺失时才用 `priced` 事件 + 事件 horizon 极值映射到 `latest_close`。
- `AI Coding 结构性变量`：仅作为结构性风险观察，不当作模型结论。
- `AI 创作工具竞争现状`：在业务分析报告中用表格展示竞品当前动作、对目标公司哪条业务线造成压力、是否已压缩功能溢价，以及目标公司可防守的 workflow/数据/用户/渠道/品牌要素。

## 复核清单（输出后）

- 价格链路是否完整（`status: priced` / `missing_*`）  
- 同业对照是否齐备（peer/ticker映射是否闭环）  
- 时间与事实是否齐套（发布日、覆盖窗、事件粒度、证据引用）  
- 下行触发机制是否写明（不是只写结果）
- 上/下行空间是否能追溯到真实来源，而不是模型生成数字
- 是否列出下一次财报、产品节点、政策/监管节点
- 是否列出过去 3 年内足以解释价格大波动的历史事件，并给出来源链接
- 是否显示目标价分歧，而不是只展示平均目标价
- 是否显示方法论来源和数据覆盖度
- 用户追问业务/竞争时，是否已经生成 `business-analysis.md/html`，而不是只在聊天里解释
- 未来时间节点是否都有具体日期或 estimated/TBA 说明；除息、财报、竞品发布是否分类清楚
- AI 创作工具竞争是否用了当前来源复核，并说明对业务线和估值倍数的传导
