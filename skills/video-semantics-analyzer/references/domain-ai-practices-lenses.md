# AI Practices Domain Lenses

这些 lenses 只在 `--domain ai-practices` 时注入，用来分析 AI 时代的创作者、研究者、工程师和产品人的方法论。目标不是追热点新闻，而是把“他们如何使用 AI、如何判断 AI 时代、建议训练什么能力、哪些实践能反补个人和 Seed 项目”拆成可追溯信号。

## 来源参考

- Anthropic Building Effective Agents：借鉴“简单、可组合、透明、可测试”的 agent/workflow 设计原则。
- OpenAI Codex 文档与安全实践：借鉴 coding agent 的任务边界、工作区控制、日志、review 和安全部署视角。
- Simon Willison 的 Using LLMs 系列：借鉴公开记录真实 LLM 使用方式、失败经验、工具链和 eval/验证习惯。
- Ethan Mollick 等 AI work/learning 研究者：借鉴把 AI 当作日常认知与工作协作者，而不是只把它当搜索框或聊天框。

## 证据边界

1. Practice event：人物明确展示或描述了一个 AI 使用流程，例如写代码、研究、读论文、生成数据、自动化、review、debug、学习或产品探索。
2. Belief event：人物对 AI 时代、能力迁移、行业变化、组织工作方式、学习路径或风险边界的观点。
3. Capability signal：人物认为未来更重要或更需要训练的能力，例如问题定义、规格书、系统设计、验证/eval、自动化、产品判断、研究能力、代码阅读、审美和沟通。
4. Tooling pattern：具体工具、agent、脚本、工作区、prompt/spec、eval harness、检索或自动化编排方式。
5. Application candidate：可以反补到个人工作或 Seed 项目的实验建议，必须保留来源证据、投入、风险和第一步实验。
6. Evidence gap：人物只是泛泛谈论、缺少真实工作流、缺少失败案例、缺少可验证成果或无法定位证据时必须记录缺口。

## 分析要求

- 先抽取真实做法，再抽象方法论；不要把口号直接写成能力建议。
- 区分“这个人实际怎么用 AI”和“这个人认为别人应该怎么做”。
- 对工具和模型保持可替换描述：记录 tool/pattern/use case，不把某个当前产品当作永久结论。
- 每条 practice、belief、capability 和 application candidate 都要保留 transcript、visual、timeline 或 keyframe 证据引用。
- 对个人反补建议必须写成小实验，避免空泛价值观；对 Seed 项目反补建议必须指向 pipeline、artifact、DAG、CLI、skill/check 或评估方式。
- 发现互相冲突的方法论时保留冲突，不要强行综合。
- 不确定时写 `uncertainty` 或 `evidence_gaps`，不要用模型常识补齐。
