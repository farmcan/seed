# 架构

`seed` 的主流程分为八层：

1. 来源采集：保存 URL、平台、UP/作者、发布时间、素材路径和元数据。
2. 媒体语言抽取：把视频拆成文字语言和视觉语言，分别生成 transcript 与 visual notes。
3. 视频语义分析：融合口播、字幕、画面和屏幕文字，形成单条视频的稳定语义资产。
4. 创作者聚合：按 UP/作者聚合多条视频语义，提炼创作者级表达风格、结构模板和方法论。
5. 方法论蒸馏：从聚合结果中提炼方法论、决策规则、反例和检查问题。
6. Agent 资产：输出 `SKILL.md`、checklist 和 prompt context，供 Agent 在任务前后使用。
7. 成本计量：按单条视频记录 Qwen-VL token 用量、估算费用和后续 Codex 费用预留位。
8. 反思闭环：记录 Agent 使用方法论后的结果，反向修订 skills 和 checks。

```text
URL / book / note
  -> raw asset
  -> transcript + visual notes
  -> cost report + cost ledger
  -> video semantics
  -> video DAG graph
  -> creator profile
  -> methodology / checks
  -> skill + pre-check + reflection log
```

平台下载适配器只负责采集和记录。内容理解、方法论提炼和 Agent 使用是独立层，避免把平台耦合扩散到整个系统。

## 当前主入口

现阶段已经具备单步能力，但真正的产品入口应该收敛成两个 pipeline：

```text
seed run-video-pipeline <url-or-media>
  -> 单条视频完整分析
  -> video semantics + timeline + claims + cost ledger + video DAG HTML

seed run-creator-pipeline --platform <platform> <owner>
  -> 创作者视频列表
  -> 多条视频 pipeline + budget gate
  -> creator profile + creator DAG + agent assets
```

这两个命令已经是当前优先入口；其他 CLI 视为可组合 step 或调试入口。新增功能如果不能进入 pipeline、不能生成稳定 artifact、不能被 DAG 或 creator aggregation 消费，就不应作为主功能推进。

## 功能模块总览

| 模块 | CLI | 主要代码 | 主要产物 |
| --- | --- | --- | --- |
| 来源采集 | `seed ingest-url` | `src/seed/sources/`, `src/seed/library.py` | `library/raw/*`, `library/notes/*.source.yaml` |
| 创作者视频列表 | `seed fetch-creator-videos` | `src/seed/sources/creator_videos.py`, `src/seed/library.py` | `library/notes/*.creator-videos.yaml` |
| 创作者批量入库 | `seed ingest-creator-videos` | `src/seed/creator_ingest.py`, `src/seed/sources/yt_dlp_adapter.py` | `library/raw/*`, `library/notes/*.source.yaml` |
| 视频 pipeline | `seed run-video-pipeline` | `src/seed/pipeline.py` | pipeline manifest、单条视频全量产物、cost ledger |
| 创作者 pipeline | `seed run-creator-pipeline` | `src/seed/creator_pipeline.py` | 多视频 manifest、creator profile、creator DAG、creator cost ledger |
| ASR 转写 | `seed transcribe-media` | `src/seed/media.py`, `src/seed/asr/`, `src/seed/transcripts.py` | `library/raw/*.asr.mp3`, `library/raw/*.asr.chunks/*`, `library/transcripts/*.transcript.md` |
| 视觉语言 | `seed extract-frames`, `seed analyze-frames` | `src/seed/vision/` | `library/frames/*`, `library/notes/*.visual.md` |
| 成本计量 | `seed analyze-frames`, `seed build-cost-ledger`, `seed build-video-dag` | `src/seed/costs.py`, `src/seed/graphs/video_dag.py` | `library/costs/*.cost.json`, `library/costs/*.ledger.json`, DAG cost 节点 |
| 书籍/笔记 | `seed import-book-note`, `seed analyze-book-note`, `seed aggregate-topic` | `src/seed/books.py` | `library/notes/*.book-note.md`, `library/semantics/*.book-semantics.md`, `library/distilled/*.topic-profile.md` |
| 快速总结 | `seed summarize-transcript` | `src/seed/summarizers/`, `src/seed/skill_refs.py`, `src/seed/semantics/evidence.py` | `library/notes/*.summary.md` |
| 视频语义 | `seed analyze-video-semantics` | `src/seed/semantics/analyzer.py`, `src/seed/skill_refs.py`, `src/seed/semantics/evidence.py` | `library/semantics/*.video-semantics.md` |
| 时间线 | `seed build-timeline` | `src/seed/timeline.py` | `library/timelines/*.timeline.json` |
| 事实核验队列 | `seed extract-claims` | `src/seed/factcheck.py` | `library/claims/*.claims.json` |
| 事实核验 | `seed verify-claims` | `src/seed/claim_verification.py` | `library/claims/*.verified.json` |
| DAG 图谱 | `seed build-video-dag`, `seed serve-video-dag`, `seed export-video-dag-html`, `seed export-video-dag-cytoscape-html` | `src/seed/graphs/video_dag.py`, `src/seed/dag_server.py`, `src/seed/dag_export.py`, `tools/video-dag-canvas.html`, `tools/video-dag-cytoscape.html` | `library/graphs/*.video-dag.json`, `library/graphs/*.video-dag.html`, `*.video-dag-cytoscape.html` |
| Creator DAG | `seed build-creator-dag` | `src/seed/graphs/creator_dag.py` | `library/graphs/*.creator-dag.json`, `library/graphs/*.creator-dag.html` |
| 创作者聚合 | `seed aggregate-owner`, `seed validate-creator-profile` | `src/seed/semantics/aggregator.py`, `src/seed/semantics/validation.py` | `library/distilled/*.creator-profile.md`, `*.creator-profile.validation.json` |
| Agent 资产生成 | `seed generate-agent-assets`, `seed record-reflection`, `seed suggest-revisions` | `src/seed/agent_assets.py`, `src/seed/reflections.py` | `library/skills/*/SKILL.md`, `library/checks/*.md`, `library/reflections/*` |

当前视频 DAG 会展示本地视频、音频、关键帧截图、transcript、visual notes、cost ledger、timeline event、semantic 子节点、creator signals、fact-check queue 和 agent assets。旧版 DOM/ELK 画布保留为可编辑原型；Cytoscape 画布是性能优先实验入口，主画布只渲染轻量图谱，媒体只在右侧详情打开后加载。

## 模块边界

- `sources/`：平台采集适配器。只关心 URL、授权、下载、metadata，不做内容理解；下载结果需要记录 provider、fallback 和 cookies 相关诊断。
- `sources/creator_videos.py`：按平台和创作者名称发现视频列表。Bilibili 优先复用 `yt-dlp` 的 UP 空间 extractor，并保留 WBI API fallback；小红书先输出搜索候选，后续再替换成稳定登录态 provider。
- `creator_ingest.py`：读取 `*.creator-videos.yaml`，按起始位置和数量选择视频，跳过已入库 URL，并复用现有下载适配器与 source record 写入。
- `pipeline.py`：负责把现有单步命令背后的业务函数串成单条视频 pipeline，写入 run manifest，并支持断点续跑。
- `creator_pipeline.py`：负责创作者级批量任务、失败继续、成本预算门槛和 creator DAG 入口；`--max-estimated-cost` 到达后停止后续视频，并在 manifest 写入 `budget_exceeded`。
- `asr/` 和 `media.py`：音频抽取、超限音频分片和线上 ASR provider。只产出 transcript；长音频 transcript 会在 frontmatter 记录 `asr_chunks`。
- `vision/`：抽帧、Qwen-VL 调用和 visual notes。只描述画面证据，不负责最终方法论；Qwen-VL provider 需要返回 token usage，供成本模块记录。
- `costs.py`：统一写入单条视频成本报告和 pipeline cost ledger。默认记录 Qwen-VL token 用量、单价来源、估算金额，并为 ASR、Codex、搜索/核验保留成本项；实际价格可通过环境变量覆盖。
- `skill_refs.py`：读取共享 video analysis lenses。prompt 构建器只引用这个入口，避免各模块复制 lens 文本。
- `semantics/evidence.py`：从 transcript chunk、visual notes 和 keyframe metadata 生成 `T*`、`V*`、`F*` 证据锚点，供总结、视频语义和创作者聚合引用。
- `summarizers/`：单条 transcript 的轻量总结，适合作为人工快速预览；prompt 必须注入共享 lenses 和证据锚点。
- `semantics/analyzer.py`：单条视频语义融合，输入 transcript 和 visual notes，输出 `library/semantics/*.video-semantics.md`；强结论要引用 transcript、visual notes 或 keyframe 证据 ID。
- `timeline.py`：从 transcript chunk、关键帧 manifest、video semantics 和 visual notes 生成确定性 timeline JSON；抽不到时间点时保留 `start_seconds: null`。
- `factcheck.py`：从 video semantics 的 main claims 和 open questions 中拆出待核验 claim，默认状态是 `unverified`。
- `claim_verification.py`：只负责外部证据检索、来源记录和 claim 状态更新，不负责生成新的视频语义；当前版本保守输出 `unclear/unverified`，后续再接自动支持/反驳判断。
- `semantics/aggregator.py`：按 owner 聚合多条视频语义，输出 `library/distilled/*.creator-profile.md`；prompt 复用共享 lenses，跨视频结论需要能回到具体视频语义和证据引用。
- `semantics/validation.py`：对 creator profile 做输出后证据校验，发现缺少视频、timestamp、keyframe、transcript chunk 或 provisional 标记的强结论时写入 warning report，不自动改写原文。
- `agent_assets.py`：从 creator profile 生成待人工 review 的候选 `SKILL.md`、pre-check 和 post-task reflection checklist。
- `reflections.py`：记录 Agent 使用某个 creator 方法后的结果、有效点、失败点和需要修订的地方。
- `semantics/aggregator.py`：默认要求同一 owner 至少 3 条 video semantics 才生成 creator profile；单条或少量视频需要显式 `--min-videos` 降级为 provisional。
- `graphs/video_dag.py`：把本地分析产物组装成画布可读 DAG JSON，输出 `library/graphs/*.video-dag.json`；支持按标题自动发现 raw、audio、transcript、frames、visual notes、cost ledger、semantics 和 timeline。
- `graphs/creator_dag.py`：把同一 UP/作者的多条 video semantics、creator profile、profile validation、cost ledger 和 agent assets 组装成 creator DAG。
- `dag_server.py`：用本地 HTTP server 打开 DAG HTML 和 graph JSON，避免 `file://` 下浏览器策略影响素材加载。
- `dag_export.py`：把 graph JSON 嵌入独立 HTML，适合直接打开和分享本地快照，不要求 server 一直运行；支持旧版 DOM/ELK 模板和新的 Cytoscape 性能优先模板。
- `agents/codex.py`：统一管理 `codex exec` 命令、dry-run、输出文件写入。内容分析模块不得直接调用 `subprocess` 跑 Codex。
- `markdown.py`：统一读取 Markdown frontmatter、正文和 metadata 字段，避免不同 artifact 各写一套解析逻辑。
- `cli.py`：只做参数接线、轻量校验和用户输出。业务逻辑应留在对应模块。

## Skills 边界

- `skills/video-semantics-analyzer/references/video-analysis-lenses.md`：视频分析共享 lens 库，吸收 Fabric、BiliNote、tldw、短视频结构分析等参考，但不复制外部 prompt。
- `skills/video-note-summarizer/SKILL.md`：面向 transcript-first 的快速笔记，复用共享 lenses，输出给人看的 Markdown。
- `skills/video-semantics-analyzer/SKILL.md`：面向长期聚合的单条视频语义，严格区分 verbal evidence、visual evidence、timeline evidence 和 inference。
- `skills/creator-profile-aggregator/SKILL.md`：面向跨视频聚合，强结论需要重复证据；单视频信号必须标记 provisional。

prompt 构建时会自动注入：

- `<analysis_lenses>`：共享 lens 库，来自 `video-analysis-lenses.md`。
- `<evidence_anchors>`：当前视频可引用的 transcript、visual notes 和 keyframe ID，例如 `[T1]`、`[V1]`、`[F3]`。

## 产物边界

- `library/raw/`：本地私有原始素材。
- `library/raw/*.asr.chunks/`：长音频 ASR 分片，供 provider 逐片转写。
- `library/transcripts/`：文字语言，来自 ASR 或人工整理。
- `library/frames/`：抽样关键帧。
- `library/notes/*.visual.md`：视觉语言，来自 VL 模型。
- `library/costs/*.cost.json`：单条视频成本报告，包含 Qwen-VL token 用量、单价、估算金额、pricing source 和 Codex 费用预留项。
- `library/costs/*.ledger.json`：pipeline 级成本账本，汇总单条视频或创作者批量任务的 Qwen-VL 明细，并保留 ASR、Codex、搜索/核验的 reserved 项；creator pipeline 的预算门槛读取这个 artifact。
- `library/notes/*.source.yaml`：单条来源记录，包含原始 URL、下载路径、metadata 路径、下载 provider、fallback 状态和下载诊断。
- `library/notes/*.summary.md`：快速摘要，不作为长期聚合主数据。
- `library/notes/*.creator-videos.yaml`：创作者视频列表，作为后续批量下载、批量分析和 UP 级聚合的入口。
- `library/notes/*.book-note.md`：手动导入的书籍/笔记。
- `library/runs/`：pipeline run manifest，记录 step 状态、输入输出、错误、provider/model 和耗时。
- `library/semantics/*.video-semantics.md`：单条视频语义，是后续聚合的主数据。
- `library/semantics/*.book-semantics.md`：书籍/笔记语义，默认没有 visual language。
- `library/timelines/*.timeline.json`：视频时间线事件，包含 transcript chunk、keyframe、内容结构、广告候选和不确定性。
- `library/claims/*.claims.json`：待核验 claim 队列，状态至少从 `unverified` 开始。
- `library/claims/*.verified.json`：外部核验后的 claim 状态、来源和证据；当前自动判断仍保持保守。
- `library/graphs/*.video-dag.json`：视频分析链路的可视化图谱，可由 `tools/video-dag-canvas.html` 直接展示。
- `library/graphs/*.video-dag.html`：嵌入 graph JSON 的静态画布快照，本地打开即可查看；媒体文件仍按相对路径读取 `library/`。
- `library/graphs/*.video-dag-cytoscape.html`：Cytoscape 图谱快照，优先解决卡顿问题；默认简版显示，右侧详情默认关闭。
- `library/graphs/*.creator-dag.json` 和 `*.creator-dag.html`：UP/作者级画布。
- `library/distilled/*.topic-profile.md`：跨书籍/笔记/视频的主题聚合草稿。
- `library/distilled/*.creator-profile.md`：创作者级聚合画像。
- `library/distilled/*.creator-profile.validation.json`：creator profile 输出后证据校验报告，只提示缺口，不自动改写 profile。
- `library/skills/` 和 `library/checks/`：从 creator profile 生成、待人工 review 的 Agent 可加载资产。
- `library/reflections/*.reflection.jsonl`：Agent 使用方法论后的复盘记录，用于后续修订 creator profile、skills 和 checks。
- `library/reflections/*.revision-suggestions.md`：基于 reflection log 的修订建议草稿，不自动覆盖原资产。
