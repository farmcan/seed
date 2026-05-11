# Seed TODO 入口

这是唯一的主计划入口。后续除非确实需要长期沉淀，否则不要新增文档；优先更新本文件、`docs/architecture.md` 或 `docs/research-competitors.md`。

## P0：让现有链路稳定

- [x] 增加 `seed run-video-pipeline`。
  - 输入 URL 或本地视频，串起下载/记录、ASR、抽帧、Qwen-VL、成本记录、video semantics、timeline、claims、DAG JSON 和静态 HTML。
  - 每一步要支持跳过已存在产物，失败后可以从中间步骤续跑。
  - 输出最后的主入口路径：`*.video-dag.html`、`*.video-semantics.md`、`*.cost.json`、`*.ledger.json`。
- [x] 增加 pipeline run manifest。
  - 记录每个 step 的输入、输出、开始/结束时间、状态、错误和 provider/model。
  - 后续 creator 批量处理和成本汇总都从 manifest 读状态。
- [x] 把 `seed build-video-dag` 的输出提示改成静态 HTML 优先。
  - 用户要看的默认是 `seed export-video-dag-html` 产物，不应依赖本地 server 是否还开着。

## P1：加强证据 DAG

- [x] 视频分析 prompt 证据锚点。
  - `summarize-transcript`、`analyze-video-semantics` 和 `aggregate-owner` 会注入共享 `video-analysis-lenses.md`。
  - 单条视频 prompt 会从 transcript chunk、visual notes 和 keyframe metadata 生成 `[T*]`、`[V*]`、`[F*]` 证据 ID。
- [x] 增加 `seed verify-claims` 的最小可用闭环。
  - 输入 `library/claims/*.claims.json`，输出带来源、证据摘录、URL、状态和不确定性的核验结果。
  - 当前版本只记录 evidence source，自动判断保持保守：有来源为 `unclear`，无来源为 `unverified`。
- [ ] 增强 `seed verify-claims` 的自动判断。
  - 状态至少支持 `supported`、`contradicted`、`unclear`、`unverified`。
  - 没有外部证据时不得把 claim 标成 verified。
  - 调研结论：按 claim decomposition、query planning、evidence retrieval、evidence synthesis、verdict prediction 分阶段实现，并保存每阶段 artifact。
- [x] 把 fact-check 结果接入 DAG。
  - claim 节点展示核验状态、来源数量、证据链接和风险等级。
- [x] 做 pipeline 级 cost ledger。
  - 单条视频成本不只记录 Qwen-VL，还要预留并逐步接入 ASR、Codex、搜索/核验等步骤。
  - DAG 成本节点展示分项和总计。
  - 调研结论：Qwen-VL 价格会随 deployment/region 变化，成本 artifact 必须保存 pricing source、deployment 和计价快照。
- [x] 让 DAG 静态 HTML 离线可用。
  - `elkjs` 已 vendor 到 `tools/vendor/`，静态导出默认使用本地脚本。

## P2：创作者级知识

- [x] 增加 `seed run-creator-pipeline` 第一版。
  - 输入平台 + UP/作者名称，自动获取视频列表、批量入库、批量跑视频 pipeline。
  - 已支持 limit、start-index、失败继续、跳过已完成和成本预算上限。
- [x] 为 `seed run-creator-pipeline` 增加成本预算上限。
  - 建议先做本地 budget gate：开始处理下一条视频前读取已有 cost ledger，超过预算则停止并写入 run manifest。
- [x] 增加 `seed build-creator-dag`。
  - 按 UP/作者展示多条视频、每条状态、共性方法论、代表证据、反例、成本和 reflection 入口。
- [x] 强化 creator profile 的证据引用。
  - 当前 prompt 已注入共享 lenses；下一步要在输出后做结构校验，要求每个创作者级结论回溯到具体视频、timestamp/keyframe/transcript chunk 或 semantic section。
- [ ] Agent 资产 review 流程。
  - 从 creator profile 生成的 skill/check 需要人工确认状态，例如 `draft`、`reviewed`、`installed`。

## P3：书籍和非视频来源

- [x] 增加手动书籍/笔记导入。
  - 保留作者、章节、页码/位置、引用边界。
- [x] 增加 book semantics artifact。
  - 类似 video semantics，但默认没有 visual language。
- [x] 支持按作者/主题聚合。
  - 复用 creator aggregation 的思路，但不绑定视频平台。

## P4：继续调研

- [x] 继续调研类似产品和视觉笔记工具。
  - 入口：`docs/research-competitors.md`
  - 已补充：NotebookLM 只导入 YouTube transcript 的限制、Readwise time-synced transcript 体验、tldw API-first 媒体研究形态、React Flow/ELK 布局取舍。
- [x] 调研 timeline extraction 和 fact-check prompt。
  - 不再新增零散调研文档；先把结论合并到本文件或 `docs/research-competitors.md`。
  - 已补充：fact-check 下一步按 claim、query、evidence、verdict、uncertainty 分阶段落 artifact。
- [x] 定期核验 Qwen-VL 单价。
  - 当前成本估算默认引用阿里云百炼价格页，实际账单以服务商后台为准。
  - 2026-05-11 核验：阿里云百炼官方价格页最后更新时间为 2026-04-01；`qwen-vl-max` 在不同部署区价格不同，后续成本记录必须带 deployment/region。
- [x] 调研 pipeline orchestration 的轻量实现。
  - 先看是否需要 Prefect/Dagster/Temporal 这类外部依赖；短期倾向本地 manifest + step runner。
  - 结论：暂不引入重型编排；先实现 cost ledger、budget gate、resume semantics 和 evidence validation。

## P5：下一轮实现建议

- [x] 实现 pipeline 级 cost ledger。
  - 汇总 Qwen-VL、ASR、Codex 预留、搜索/核验成本。
  - 输入来自现有 `library/costs/*.cost.json` 和 pipeline manifest。
  - 输出 `library/costs/*.ledger.json`，并接入 video DAG / creator DAG。
- [x] 实现 creator pipeline budget gate。
  - 在处理每条视频前读取 ledger 或已知单条 cost。
  - 超出预算时停止后续视频，manifest 记录 `budget_exceeded`。
- [ ] 实现 claim verification 分阶段 artifact。
  - claim -> query plan -> evidence snippets -> source score -> verdict -> uncertainty。
  - 没有足够来源时只能输出 `unclear` 或 `unverified`。
- [x] 实现 creator profile evidence validator。
  - 检查 creator profile 中强结论是否含视频、timestamp/keyframe/transcript chunk 或 semantic section 引用。
  - 不自动改写 profile，先输出 validation report。
- [ ] 增强 DAG 媒体联动。
  - 从 timeline event、transcript chunk 或 keyframe 节点跳转到视频/音频对应位置。
  - 借鉴 Readwise 的 time-synced transcript，而不是只展示静态节点。
- [ ] 评估 Cytoscape DAG 是否替代默认 DOM/ELK 画布。
  - 如果当前样本和后续大图都明显更顺，把 `export-video-dag-html` 默认模板切到 Cytoscape。
  - 旧 DOM/ELK 画布保留为可编辑 fallback。

## 已完成基础

- [x] GitHub / 本地仓库初始化。
- [x] Bilibili 和小红书下载 demo。
- [x] DashScope / Qwen ASR provider。
- [x] Qwen-VL 抽帧分析。
- [x] Codex transcript summary。
- [x] Video semantics 融合。
- [x] Creator profile 聚合。
- [x] Video DAG graph artifact。
- [x] 单文件 HTML 无限画布，支持导入 DAG JSON、预览视频/音频/截图，支持简版、按节点展开和基于 `elkjs` 的自动分层布局。
- [x] 创作者视频列表批量入库：`seed ingest-creator-videos` 支持选择前 N 条、跳过已入库 URL，并复用现有下载适配器。
- [x] 长视频 ASR 分段：`seed transcribe-media` 默认在音频超过 provider 上传限制时自动切片、逐片转写、合并 transcript，并记录 `asr_chunks` 元数据。
- [x] Timeline artifact：`seed build-timeline` 生成 `library/timelines/*.timeline.json`，包含 transcript chunk、关键帧、内容结构、广告候选和不确定性。
- [x] 下载可靠性记录：source record 会保存 `download_provider`、`fallback_used` 和 `download_notes`；下载失败时提示平台 cookies 配置。
- [x] DAG 自动发现：`seed build-video-dag --title "..."` 会自动找齐本地 raw、audio、transcript、frames、visual notes、semantics 和 timeline。
- [x] DAG timeline 展示：video DAG 会读取 timeline artifact，并生成 timeline event 子节点。
- [x] Fact-check claim 节点：`seed extract-claims` 从 `video-semantics.md` 拆出 `library/claims/*.claims.json`，DAG 会展示 claim 子节点，默认状态是 `unverified`。
- [x] DAG 画布体验：`seed serve-video-dag` 提供本地 server 打开 graph；HTML 画布支持节点搜索/过滤、边标签，以及节点卡片内媒体预览。
- [x] DAG 静态导出：`seed export-video-dag-html` 会把 graph JSON 嵌进 HTML，默认全展开，避免关闭本地 server 后无法查看。
- [x] Cytoscape DAG 实验入口：`seed export-video-dag-cytoscape-html` 会生成性能优先的图谱快照，主画布只渲染轻量节点，媒体在右侧详情按需加载。
- [x] 视频成本报告：`seed analyze-frames` 会按视频写入 `library/costs/*.cost.json`，记录 Qwen-VL tokens、估算费用、pricing source 和 Codex 预留项；`seed build-video-dag` 会把成本节点接入画布。
- [x] Pipeline 成本账本：`seed build-cost-ledger` 和 `run-video-pipeline` 会写入 `library/costs/*.ledger.json`，汇总 Qwen-VL 并预留 ASR、Codex、搜索/核验费用。
- [x] 创作者预算门槛：`seed run-creator-pipeline --max-estimated-cost ...` 在预算达到后停止后续视频，并把 `budget_exceeded` 写入 manifest。
- [x] Creator profile 证据校验：`seed validate-creator-profile` 和 `aggregate-owner` 会输出 `*.creator-profile.validation.json`。
- [x] Agent 资产生成：`seed generate-agent-assets` 从 creator profile 生成候选 `SKILL.md`、pre-check 和 post-task reflection checklist，默认需要人工 review。
- [x] Reflection log：`seed record-reflection` 记录 Agent 使用 creator 方法后的 outcome、worked、failed 和 revise 项。
- [x] Creator profile 最小样本约束：`seed aggregate-owner` 默认要求同一 owner 至少 3 条 video semantics；少量样本必须显式 `--min-videos` 降级。
- [x] Reflection 修订建议：`seed suggest-revisions` 基于 reflection log 生成 revision suggestions 草稿，不自动覆盖原资产。
- [x] 单条视频 pipeline：`seed run-video-pipeline` 串起现有分析步骤并写入 `library/runs/*.video-pipeline.yaml`。
- [x] 创作者 pipeline 第一版：`seed run-creator-pipeline` 可以获取视频列表、批量入库并逐条运行视频 pipeline。
- [x] Creator DAG 第一版：`seed build-creator-dag` 生成 UP/作者级 DAG JSON 和静态 HTML。
- [x] 书籍/笔记入口：`seed import-book-note`、`seed analyze-book-note`、`seed aggregate-topic` 支持非视频来源的基础语义产物。
- [x] Canvas 布局离线化：`tools/vendor/elk.bundled.js` 固定 `elkjs`，导出 HTML 不再依赖 CDN。
- [x] Cytoscape 图谱渲染实验：`tools/vendor/cytoscape.min.js` 固定 `cytoscape@3.29.2`，用于验证图谱引擎是否比 DOM card canvas 更顺。
- [x] 视频分析 lenses：`skills/video-semantics-analyzer/references/video-analysis-lenses.md` 收敛 Fabric、BiliNote、tldw、短视频结构等参考框架。
- [x] 视频分析证据锚点：prompt 构建统一注入共享 lenses 和 `[T*]`、`[V*]`、`[F*]` 证据引用要求，避免纯主观总结。
