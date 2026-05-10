# Seed TODO 入口

这是唯一的主计划入口。后续除非确实需要长期沉淀，否则不要新增文档；优先更新本文件、`docs/architecture.md` 或 `docs/research-competitors.md`。

## P0：让现有链路稳定

- [ ] 增加 `seed run-video-pipeline`。
  - 输入 URL 或本地视频，串起下载/记录、ASR、抽帧、Qwen-VL、成本记录、video semantics、timeline、claims、DAG JSON 和静态 HTML。
  - 每一步要支持跳过已存在产物，失败后可以从中间步骤续跑。
  - 输出最后的主入口路径：`*.video-dag.html`、`*.video-semantics.md`、`*.cost.json`。
- [ ] 增加 pipeline run manifest。
  - 记录每个 step 的输入、输出、开始/结束时间、状态、错误和 provider/model。
  - 后续 creator 批量处理和成本汇总都从 manifest 读状态。
- [ ] 把 `seed build-video-dag` 的输出提示改成静态 HTML 优先。
  - 用户要看的默认是 `seed export-video-dag-html` 产物，不应依赖本地 server 是否还开着。

## P1：加强证据 DAG

- [ ] 增加 `seed verify-claims`。
  - 输入 `library/claims/*.claims.json`，输出带来源、证据摘录、URL、状态和不确定性的核验结果。
  - 状态至少包括 `supported`、`contradicted`、`unclear`、`unverified`。
  - 没有外部证据时不得把 claim 标成 verified。
- [ ] 把 fact-check 结果接入 DAG。
  - claim 节点展示核验状态、来源数量、证据链接和风险等级。
- [ ] 做 pipeline 级 cost ledger。
  - 单条视频成本不只记录 Qwen-VL，还要预留并逐步接入 ASR、Codex、搜索/核验等步骤。
  - DAG 成本节点展示分项和总计。
- [ ] 让 DAG 静态 HTML 离线可用。
  - 当前 `elkjs` 通过 CDN 加载；需要把稳定版本 vendor 到 `tools/vendor/`，静态导出默认使用本地脚本。

## P2：创作者级知识

- [ ] 增加 `seed run-creator-pipeline`。
  - 输入平台 + UP/作者名称，自动获取视频列表、批量入库、批量跑视频 pipeline。
  - 支持 limit、start-index、失败继续、跳过已完成、成本预算上限。
- [ ] 增加 `seed build-creator-dag`。
  - 按 UP/作者展示多条视频、每条状态、共性方法论、代表证据、反例、成本和 reflection 入口。
- [ ] 强化 creator profile 的证据引用。
  - 每个创作者级结论需要能回溯到具体视频、timestamp/keyframe/transcript chunk 或 semantic section。
- [ ] Agent 资产 review 流程。
  - 从 creator profile 生成的 skill/check 需要人工确认状态，例如 `draft`、`reviewed`、`installed`。

## P3：书籍和非视频来源

- [ ] 增加手动书籍/笔记导入。
  - 保留作者、章节、页码/位置、引用边界。
- [ ] 增加 book semantics artifact。
  - 类似 video semantics，但默认没有 visual language。
- [ ] 支持按作者/主题聚合。
  - 复用 creator aggregation 的思路，但不绑定视频平台。

## P4：继续调研

- [ ] 继续调研类似产品和视觉笔记工具。
  - 入口：`docs/research-competitors.md`
  - 重点：BiliNote、NotebookLM、tldw、Readwise、Recall、GraphRAG、tldraw、React Flow、ELK、Excalidraw。
- [ ] 调研 timeline extraction 和 fact-check prompt。
  - 不再新增零散调研文档；先把结论合并到本文件或 `docs/research-competitors.md`。
- [ ] 定期核验 Qwen-VL 单价。
  - 当前成本估算默认引用阿里云百炼价格页，实际账单以服务商后台为准。
- [ ] 调研 pipeline orchestration 的轻量实现。
  - 先看是否需要 Prefect/Dagster/Temporal 这类外部依赖；短期倾向本地 manifest + step runner。

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
- [x] 视频成本报告：`seed analyze-frames` 会按视频写入 `library/costs/*.cost.json`，记录 Qwen-VL tokens、估算费用、pricing source 和 Codex 预留项；`seed build-video-dag` 会把成本节点接入画布。
- [x] Agent 资产生成：`seed generate-agent-assets` 从 creator profile 生成候选 `SKILL.md`、pre-check 和 post-task reflection checklist，默认需要人工 review。
- [x] Reflection log：`seed record-reflection` 记录 Agent 使用 creator 方法后的 outcome、worked、failed 和 revise 项。
- [x] Creator profile 最小样本约束：`seed aggregate-owner` 默认要求同一 owner 至少 3 条 video semantics；少量样本必须显式 `--min-videos` 降级。
- [x] Reflection 修订建议：`seed suggest-revisions` 基于 reflection log 生成 revision suggestions 草稿，不自动覆盖原资产。
