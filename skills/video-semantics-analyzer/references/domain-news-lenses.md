# News Domain Lenses

这些 lenses 只在 `--domain news` 时注入，用来分析新闻、政策、地缘事件、监管事件和产业事件。目标是事实汇总，不是观点输出。

## 来源参考

- GDELT DOC 2.0：借鉴开放新闻检索、跨语言覆盖、文章列表和 coverage timeline 的做法。
- Claim decomposition / RAG fact-checking：借鉴 claim -> query -> evidence -> verdict -> uncertainty 的分阶段事实处理。
- NotebookLM / source-grounded QA：借鉴围绕来源回答、保留出处和不确定性的交互形态。

## 新闻证据边界

1. Event fact：发生了什么、何时发生、谁参与、来源是什么。
2. Reported claim：某个机构、人物或媒体声称了什么，必须保留 attribution。
3. Interpretation：UP/作者或模型对事实的解释，不能混入 facts。
4. Market mechanism：事件可能影响行业的机制，只能写成可能路径和不确定性。
5. Source gap：缺少原始文件、官方声明、多源交叉验证或时间线证据。

## 分析要求

- 先汇总事实，再列 reported claims，最后才列可能影响。
- 对每条事实保留 source URL、source title、发布时间和 source count。
- 对政策、外交、监管、并购、制裁、战争、选举等事件，必须区分已发生事实、计划、传闻和评论。
- 对财经相关影响，只写行业暴露、供应链、需求、成本、监管、汇率、利率、风险偏好等机制，不写买卖建议。
- 强结论必须引用 transcript、visual notes、timeline、外部来源或 news digest。
