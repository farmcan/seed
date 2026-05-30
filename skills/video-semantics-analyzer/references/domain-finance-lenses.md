# Finance Domain Lenses

这些 lenses 只在 `--domain finance` 时注入，用来分析财经、投资、交易、宏观和产业判断类视频。它们是领域约束，不是投资建议。

## 来源参考

- VideoConviction / finfluencer recommendation extraction：借鉴把视频中的 ticker、action、horizon、conviction 和证据片段拆成结构化记录的做法。
- FinGPT / FinRobot：借鉴金融文本、新闻、公告和分析报告的多任务处理思路，但不把模型结论当事实。
- FinBERT：借鉴金融情绪与语气识别视角，用来区分 bullish、bearish、neutral 和不确定表达。
- FinRL：借鉴策略需要环境、状态、行动、风险和回测约束的表达方式；视频观点不能直接等同可交易策略。

## 金融证据边界

1. Creator claim：UP/作者说了什么，只能标为创作者观点。
2. Market fact：价格、财报、政策、宏观数据、公告等，需要外部来源核验。
3. Recommendation signal：买、卖、持有、观察、规避、加仓、减仓等动作；必须绑定标的、方向、时间窗口和证据引用。
4. Methodology signal：反复使用的交易/投资框架，例如估值、催化剂、趋势、风险收益比、仓位、止损、宏观流动性。
5. Risk and uncertainty：视频没有覆盖的前提、反例、仓位风险、幸存者偏差、利益冲突和时效性。

## 单条财经视频分析

- Instruments：识别股票、指数、ETF、行业、商品、外汇、加密资产和宏观变量；没有明确 ticker 时保留中文名称和不确定性。
- Action map：提取 buy/sell/hold/watch/avoid/add/reduce/unknown，不要把情绪形容词误当交易动作。
- Direction map：bullish/bearish/neutral/mixed/unknown，并记录支撑理由。
- Horizon map：日内、短线、波段、中长线、长期配置或未知。
- Conviction map：高/中/低/未知，必须基于视频措辞、证据密度和风险讨论推断。
- Thesis map：核心 thesis、催化剂、估值锚、宏观前提、产业逻辑、技术面信号、风险失效点。
- Risk controls：仓位、止损、分批、观察条件、反例和不能做的场景。
- Disclosure and conflict：广告、课程、社群、持仓披露、利益冲突和免责声明。

## 跨视频/UP 级财经蒸馏

- Recurring market lens：UP 是否长期偏宏观、产业、财报、技术分析、情绪面、资金面或事件驱动。
- Trade construction：如何从观点变成交易：入场条件、确认信号、仓位、止损、退出、复盘。
- Reliability pattern：哪些观点有后验验证，哪些只停留在故事或情绪。
- Blind spots：反复忽略的风险，例如估值、流动性、政策、个股基本面、杠杆或时间窗口。
- Audience fit：更像教育、新闻解读、交易信号、卖课/导流、还是长期投资框架。

## 每日/窗口化财经简报

面向“今天这些财经 UP 都说了什么”的产品入口时，输出必须能被聚合成一份多创作者简报，而不是只做单视频总结：

- Creator chapter：每个 UP/作者单独成章，先给 3-5 条核心观点，再列标的、动作、方向、时间窗口、证据引用和风险。
- Today delta：突出本窗口内新增或明显强化/弱化的主题，例如新提到的标的、从看多转谨慎、从宏观切到财报、风险披露变多。
- Consensus/conflict：跨 UP 聚合同一标的或主题时，要区分一致看多、一致看空、分歧、只有单人提及和证据不足。
- Methodology extraction：每个 UP 至少尝试抽取可复用方法论信号，例如估值锚、催化剂框架、技术面触发、仓位纪律、风险失效条件；没有就写缺口。
- Evidence quality：日报中的每条强结论都要能回到 `viewpoint_events.evidence_refs`、视频标题、发布时间或外部 facts；证据不足时宁可写“需要补样本/补来源”。
- User value：简报服务于“少看很多视频也知道谁在说什么、哪里有分歧、下一步该核验什么”，不能变成 Seed 自己的买卖建议。

## 输出约束

- 所有推荐、方向和方法论都要写成“创作者声称/暗示”，不要输出 Seed 自己的投资建议。
- 强结论必须引用 transcript、visual notes、timestamp、finance signals 或外部核验来源。
- 如果近期 10 天 Top UP 汇总没有完整样本，不要猜“大家都推荐了什么”；先输出采集缺口和下一步需要抓取的视频列表。
- 交易相关 artifact 必须保留日期、视频发布时间、证据引用和不确定性，因为金融观点会快速过期。
