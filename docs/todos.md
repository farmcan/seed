# Seed TODO 入口

这是唯一的主计划入口。后续除非确实需要长期沉淀，否则不要新增文档；优先更新本文件、`docs/architecture.md` 或 `docs/research-competitors.md`。

## P0：让现有链路稳定

当前 P0 已清空。下一步优先进入 P1，把已经生成的 timeline、自动发现和 fact-check 节点接入 DAG。

## P1：加强证据 DAG

当前 P1 已清空。下一步优先进入 P2，把多条视频聚合后的 creator profile 进一步转成可人工 review 的 skill 和 checks。

## P2：创作者级知识

当前 P2 已清空。下一步优先进入 P3，把书籍/笔记等非视频来源接入同一套 semantics 和聚合流程。

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

## 已完成基础

- [x] GitHub / 本地仓库初始化。
- [x] Bilibili 和小红书下载 demo。
- [x] DashScope / Qwen ASR provider。
- [x] Qwen-VL 抽帧分析。
- [x] Codex transcript summary。
- [x] Video semantics 融合。
- [x] Creator profile 聚合。
- [x] Video DAG graph artifact。
- [x] 单文件 HTML 无限画布，支持导入 DAG JSON、预览视频/音频/截图，支持简版和按节点展开。
- [x] 创作者视频列表批量入库：`seed ingest-creator-videos` 支持选择前 N 条、跳过已入库 URL，并复用现有下载适配器。
- [x] 长视频 ASR 分段：`seed transcribe-media` 默认在音频超过 provider 上传限制时自动切片、逐片转写、合并 transcript，并记录 `asr_chunks` 元数据。
- [x] Timeline artifact：`seed build-timeline` 生成 `library/timelines/*.timeline.json`，包含 transcript chunk、关键帧、内容结构、广告候选和不确定性。
- [x] 下载可靠性记录：source record 会保存 `download_provider`、`fallback_used` 和 `download_notes`；下载失败时提示平台 cookies 配置。
- [x] DAG 自动发现：`seed build-video-dag --title "..."` 会自动找齐本地 raw、audio、transcript、frames、visual notes、semantics 和 timeline。
- [x] DAG timeline 展示：video DAG 会读取 timeline artifact，并生成 timeline event 子节点。
- [x] Fact-check claim 节点：`seed extract-claims` 从 `video-semantics.md` 拆出 `library/claims/*.claims.json`，DAG 会展示 claim 子节点，默认状态是 `unverified`。
- [x] DAG 画布体验：`seed serve-video-dag` 提供本地 server 打开 graph；HTML 画布支持节点搜索/过滤、边标签，以及节点卡片内媒体预览。
- [x] 视频成本报告：`seed analyze-frames` 会按视频写入 `library/costs/*.cost.json`，记录 Qwen-VL tokens、估算费用、pricing source 和 Codex 预留项；`seed build-video-dag` 会把成本节点接入画布。
- [x] Agent 资产生成：`seed generate-agent-assets` 从 creator profile 生成候选 `SKILL.md`、pre-check 和 post-task reflection checklist，默认需要人工 review。
- [x] Reflection log：`seed record-reflection` 记录 Agent 使用 creator 方法后的 outcome、worked、failed 和 revise 项。
- [x] Creator profile 最小样本约束：`seed aggregate-owner` 默认要求同一 owner 至少 3 条 video semantics；少量样本必须显式 `--min-videos` 降级。
- [x] Reflection 修订建议：`seed suggest-revisions` 基于 reflection log 生成 revision suggestions 草稿，不自动覆盖原资产。
