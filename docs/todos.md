# Seed TODO 入口

这是唯一的主计划入口。后续除非确实需要长期沉淀，否则不要新增文档；优先更新本文件、`docs/architecture.md` 或 `docs/research-competitors.md`。

## P0：让现有链路稳定

- [ ] 正式生成 timeline artifact。
  - 目标路径：`library/timelines/*.timeline.md` 或 `.json`。
  - 内容：transcript chunk、关键帧时间点、广告段、论证阶段、CTA、不确定性。
- [ ] 增强 Bilibili / 小红书下载可靠性。
  - cookies 配置更清楚。
  - 记录 fallback 是否被触发。
  - 平台易碎逻辑继续隔离在 `sources/`。

## P1：加强证据 DAG

- [ ] `build-video-dag` 支持按标题或 source id 自动发现产物。
  - 现状：需要显式传 source、transcript、frames、visual notes、semantics。
  - 目标：`seed build-video-dag --title "..."` 自动找齐本地文件。
- [ ] timeline artifact 完成后，DAG 展示真实时间段。
  - 当前：只有 timeline 占位节点。
- [ ] 抽取 fact-check claim 节点。
  - 从 `video-semantics.md` 拆出待核验声明。
  - 状态至少包括：未核验、已核验、相互矛盾。
- [ ] 改进画布体验。
  - 本地 server 模式稳定打开 graph。
  - 节点搜索、过滤、边标签。

## P2：创作者级知识

- [ ] 同一 UP 至少分析 3 条视频后再跑 `aggregate-owner`。
  - 单条视频只能作为 provisional creator signal。
- [ ] 从 creator profile 生成候选 `SKILL.md`。
  - 生成后先人工 review，不直接安装。
- [ ] 生成 pre-check 和 post-task reflection。
  - 输出到 `library/checks/`。
- [ ] 增加反思闭环。
  - 记录 agent 使用某个方法后的效果。
  - 反向修订 creator profile、skills、checks。

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
  - 重点：BiliNote、NotebookLM、tldw、Readwise、Recall、GraphRAG、tldraw、React Flow、Excalidraw。
- [ ] 调研 timeline extraction 和 fact-check prompt。
  - 不再新增零散调研文档；先把结论合并到本文件或 `docs/research-competitors.md`。

## 已完成基础

- [x] GitHub / 本地仓库初始化。
- [x] Bilibili 和小红书下载 demo。
- [x] DashScope / Qwen ASR provider。
- [x] Qwen-VL 抽帧分析。
- [x] Codex transcript summary。
- [x] Video semantics 融合。
- [x] Creator profile 聚合。
- [x] Video DAG graph artifact。
- [x] 单文件 HTML 无限画布，支持导入 DAG JSON、预览视频/音频/截图。
- [x] 创作者视频列表批量入库：`seed ingest-creator-videos` 支持选择前 N 条、跳过已入库 URL，并复用现有下载适配器。
- [x] 长视频 ASR 分段：`seed transcribe-media` 默认在音频超过 provider 上传限制时自动切片、逐片转写、合并 transcript，并记录 `asr_chunks` 元数据。
