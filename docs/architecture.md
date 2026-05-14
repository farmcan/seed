# 架构

`seed` 的主流程分为十层：

1. 来源采集：保存 URL、平台、UP/作者、发布时间、素材路径和元数据。
2. 媒体语言抽取：把视频拆成文字语言和视觉语言，分别生成 transcript 与 visual notes。
3. 短视频结构识别：对 60s 内视频生成 profile、shot boundary 和代表帧证据。
4. 视频语义分析：融合口播、字幕、画面和屏幕文字，形成单条视频的稳定语义资产。
5. 领域 lens：在不改变通用 pipeline 的前提下，为财经等方向补充领域结构、风险边界和专用 artifact。
6. 创作者聚合：按 UP/作者聚合多条视频语义，提炼创作者级表达风格、结构模板和方法论。
7. 方法论蒸馏：从聚合结果中提炼方法论、决策规则、反例和检查问题。
8. Agent 资产：输出 `SKILL.md`、checklist 和 prompt context，供 Agent 在任务前后使用。
9. 成本计量：按单条视频记录 Qwen-VL token 用量、估算费用和后续 Codex 费用预留位。
10. 反思闭环：记录 Agent 使用方法论后的结果，反向修订 skills 和 checks。

```text
URL / book / note
  -> raw asset
  -> transcript + visual notes
  -> short profile + shots + frame notes + motion relations
  -> cost report + cost ledger
  -> video semantics
  -> optional domain signals
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
  -> `--domain finance` 时额外生成 finance signals

seed run-creator-pipeline --platform <platform> <owner>
  -> 创作者视频列表
  -> 多条视频 pipeline + budget gate
  -> creator profile + creator DAG + agent assets
  -> `--domain finance` 时按财经 lens 聚合跨视频方法论
  -> `--published-after/--published-before` 可限制发布时间窗口
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
| 短视频结构 | `seed profile-short-video`, `seed detect-shots`, `seed build-frame-notes`, `seed build-motion-relations`, `seed run-video-pipeline` | `src/seed/shorts.py`, `src/seed/pipeline.py` | `library/shorts/*.short-video-profile.json`, `library/shots/*.shots.json`, `library/shots/*.motion-relations.json`, `library/frames/*.frame-notes.jsonl`, `library/frames/*.shots/*` |
| 成本计量 | `seed analyze-frames`, `seed build-cost-ledger`, `seed build-video-dag` | `src/seed/costs.py`, `src/seed/graphs/video_dag.py` | `library/costs/*.cost.json`, `library/costs/*.ledger.json`, DAG cost 节点 |
| 书籍/笔记 | `seed import-book-note`, `seed analyze-book-note`, `seed aggregate-topic` | `src/seed/books.py` | `library/notes/*.book-note.md`, `library/semantics/*.book-semantics.md`, `library/distilled/*.topic-profile.md` |
| 快速总结 | `seed summarize-transcript` | `src/seed/summarizers/`, `src/seed/skill_refs.py`, `src/seed/semantics/evidence.py` | `library/notes/*.summary.md` |
| 视频语义 | `seed analyze-video-semantics` | `src/seed/semantics/analyzer.py`, `src/seed/skill_refs.py`, `src/seed/semantics/evidence.py` | `library/semantics/*.video-semantics.md` |
| 领域信号 | `seed extract-finance-signals`, `seed run-video-pipeline --domain finance` | `src/seed/domains/finance.py`, `src/seed/skill_refs.py` | `library/semantics/*.finance-signals.json`, video DAG / creator DAG finance 节点 |
| 时间线 | `seed build-timeline` | `src/seed/timeline.py` | `library/timelines/*.timeline.json` |
| 事实核验队列 | `seed extract-claims` | `src/seed/factcheck.py` | `library/claims/*.claims.json` |
| 事实核验 | `seed verify-claims` | `src/seed/claim_verification.py` | `library/claims/*.verified.json` |
| DAG 图谱 | `seed build-video-dag`, `seed serve-video-dag`, `seed export-video-dag-html` | `src/seed/graphs/video_dag.py`, `src/seed/dag_server.py`, `src/seed/dag_export.py`, `tools/video-dag-canvas.html` | `library/graphs/*.video-dag.json`, `library/graphs/*.video-dag.html` |
| Creator DAG | `seed build-creator-dag` | `src/seed/graphs/creator_dag.py` | `library/graphs/*.creator-dag.json`, `library/graphs/*.creator-dag.html` |
| 创作者聚合 | `seed aggregate-owner`, `seed validate-creator-profile` | `src/seed/semantics/aggregator.py`, `src/seed/semantics/validation.py` | `library/distilled/*.creator-profile.md`, `*.creator-profile.validation.json` |
| Agent 资产生成 | `seed generate-agent-assets`, `seed review-agent-assets`, `seed record-reflection`, `seed suggest-revisions` | `src/seed/agent_assets.py`, `src/seed/reflections.py` | `library/skills/*/SKILL.md`, `library/checks/*.md`, `library/checks/*.agent-assets.review.json`, `library/reflections/*` |

当前视频 DAG 会展示本地视频、音频、关键帧截图、short profile、shot strip、frame evidence notes、motion relation candidates、transcript、visual notes、cost ledger、timeline event、semantic 子节点、可选 finance signals、creator signals、fact-check queue 和 agent assets。Creator DAG 以 UP/作者级 profile、方法论和 Agent 资产为主，同时每条视频节点都可展开本地视频、音频、截图 gallery、可选 finance signals 和单条 video DAG HTML 入口。带 `start_seconds` 的 timeline event、shot、frame note 和 motion relation 节点会写入 `media_anchor`，画布详情区可以把视频/音频定位到对应时间点。DOM/ELK 画布保留卡片式视觉，默认简版显示，节点媒体默认渲染，顶部 `媒体` 按钮可一键隐藏或恢复，卡片正文默认折叠，右侧详情默认关闭。

## 模块边界

- `sources/`：平台采集适配器。只关心 URL、授权、下载、metadata，不做内容理解；下载结果需要记录 provider、fallback 和 cookies 相关诊断。
- `sources/creator_videos.py`：按平台和创作者名称发现视频列表。Bilibili 支持 `--owner-id` 直接传 mid；未传时先做用户名搜索，再复用 `yt-dlp` 的 UP 空间 extractor，并保留 WBI API fallback。小红书先输出搜索候选，后续再替换成稳定登录态 provider。
- `creator_ingest.py`：读取 `*.creator-videos.yaml`，按起始位置和数量选择视频，跳过已完整入库 URL，并复用现有下载适配器与 source record 写入。已有 source record 但没有本地 `raw_path` 时，不视为下载完成，会继续补齐原始素材。
- `pipeline.py`：负责把现有单步命令背后的业务函数串成单条视频 pipeline，写入 run manifest、status JSON 和 live DAG HTML，并支持断点续跑。每个 step 记录状态、输入输出、provider/model、耗时、artifact paths 和 cost delta；CLI 可用 Rich 进度表实时展示，live DAG 只展示运行态 step graph，不混入最终内容 DAG。
- `creator_pipeline.py`：负责创作者级批量任务、发布时间窗口过滤、失败继续、成本预算门槛、creator profile 聚合、agent assets 生成和 creator DAG 导出；`--max-estimated-cost` 到达后停止后续视频，并在 manifest 写入 `budget_exceeded`，后处理步骤写入 `creator_steps`。
- `asr/` 和 `media.py`：音频抽取、超限音频分片和线上 ASR provider。只产出 transcript；长音频会同时按文件大小和 `ffprobe` 时长判断是否切片，默认超过 300 秒会分段，transcript 会在 frontmatter 记录 `asr_chunks`。
- `vision/`：抽帧、Qwen-VL 调用和 visual notes。只描述画面证据，不负责最终方法论；Qwen-VL provider 需要返回 token usage，供成本模块记录。
- `shorts.py`：短视频 profile、shot boundary baseline、shot 代表帧、frame evidence notes 和 motion relation candidates。默认用 `ffprobe` 判断 `duration <= 60s` 是否进入短视频强分析，用 `ffmpeg` scene threshold 生成本地 shot artifact；`frame_notes` 默认按 shot 代表帧生成低成本 JSONL，并预留蒙版、画中画、贴纸、字幕、人的运动关系、滤镜、变速、转场和剪辑意图字段；`motion_relations` 默认只从相邻 frame notes 生成可追溯候选并标记 `needs_pose_or_vl`，后续可把 PySceneDetect/TransNetV2、逐帧 Qwen-VL/OCR、MediaPipe/OpenPose/YOLO pose 和 OpenCV optical flow 接成 provider。
- `costs.py`：统一写入单条视频成本报告和 pipeline cost ledger。默认记录 Qwen-VL token 用量、单价来源、估算金额，并为 ASR、Codex、搜索/核验保留成本项；实际价格可通过环境变量覆盖。
- `skill_refs.py`：读取共享 video analysis lenses 和可选 domain lenses。prompt 构建器只引用这个入口，避免各模块复制 lens 文本。
- `domains/finance.py`：财经领域信号抽取。输入单条 `video-semantics.md`，输出 `*.finance-signals.json`，结构化记录标的、方向、动作、时间窗口、风险、方法论信号和证据缺口。所有推荐都必须标记为创作者观点，不是 Seed 投资建议。
- `semantics/evidence.py`：从 transcript chunk、visual notes 和 keyframe metadata 生成 `T*`、`V*`、`F*` 证据锚点，供总结、视频语义和创作者聚合引用。
- `summarizers/`：单条 transcript 的轻量总结，适合作为人工快速预览；prompt 必须注入共享 lenses 和证据锚点。
- `semantics/analyzer.py`：单条视频语义融合，输入 transcript 和 visual notes，输出 `library/semantics/*.video-semantics.md`；强结论要引用 transcript、visual notes 或 keyframe 证据 ID。
- `timeline.py`：从 transcript chunk、关键帧 manifest、video semantics 和 visual notes 生成确定性 timeline JSON；抽不到时间点时保留 `start_seconds: null`。
- `factcheck.py`：从 video semantics 的 main claims 和 open questions 中拆出待核验 claim，默认状态是 `unverified`。
- `claim_verification.py`：只负责外部证据检索、来源记录和 claim 状态更新，不负责生成新的视频语义；按 claim decomposition、query plan、evidence snippets、source score 和 verdict 分阶段写入 artifact，没有外部证据时保持 `unverified`。
- `semantics/aggregator.py`：按 owner 聚合多条视频语义，输出 `library/distilled/*.creator-profile.md`；prompt 复用共享 lenses，跨视频结论需要能回到具体视频语义和证据引用。
- `semantics/validation.py`：对 creator profile 做输出后证据校验，发现缺少视频、timestamp、keyframe、transcript chunk 或 provisional 标记的强结论时写入 warning report，不自动改写原文。
- `agent_assets.py`：从 creator profile 生成待人工 review 的候选 `SKILL.md`、pre-check、post-task reflection checklist 和 review manifest；状态流为 `draft/reviewed/installed/deprecated`。
- `reflections.py`：记录 Agent 使用某个 creator 方法后的结果、有效点、失败点和需要修订的地方。
- `semantics/aggregator.py`：默认要求同一 owner 至少 3 条 video semantics 才生成 creator profile；单条或少量视频需要显式 `--min-videos` 降级为 provisional。
- `graphs/video_dag.py`：把本地分析产物组装成画布可读 DAG JSON，输出 `library/graphs/*.video-dag.json`；支持按标题自动发现 raw、audio、transcript、frames、short profile、shots、frame notes、motion relations、visual notes、cost ledger、semantics 和 timeline；timeline event、shot、frame note 和 motion relation 有时间点时会生成视频/音频 `media_anchor`。
- `graphs/creator_dag.py`：把同一 UP/作者的多条 video semantics、creator profile、profile validation、cost ledger 和 agent assets 组装成 creator DAG；每条视频节点会按标题解析本地 raw/audio/frames/video DAG HTML，并作为可折叠媒体证据子节点接入。
- `dag_server.py`：用本地 HTTP server 打开 DAG HTML 和 graph JSON，避免 `file://` 下浏览器策略影响素材加载。
- `dag_export.py`：把 graph JSON 嵌入独立 HTML，适合直接打开和分享本地快照，不要求 server 一直运行；默认使用 DOM/ELK 卡片式画布模板。
- `agents/codex.py`：统一管理 `codex exec` 命令、dry-run、输出文件写入。内容分析模块不得直接调用 `subprocess` 跑 Codex。
- `markdown.py`：统一读取 Markdown frontmatter、正文和 metadata 字段，避免不同 artifact 各写一套解析逻辑。
- `cli.py`：只做参数接线、轻量校验和用户输出。业务逻辑应留在对应模块。

## Skills 边界

- `skills/video-semantics-analyzer/references/video-analysis-lenses.md`：视频分析共享 lens 库，吸收 Fabric、BiliNote、tldw、短视频结构分析等参考，但不复制外部 prompt。
- `skills/video-semantics-analyzer/references/domain-finance-lenses.md`：财经领域 lens，吸收 VideoConviction、AlphaCheck、FinGPT、FinBERT、FinRL 的结构启发；只在 `--domain finance` 时注入。
- `skills/video-note-summarizer/SKILL.md`：面向 transcript-first 的快速笔记，复用共享 lenses，输出给人看的 Markdown。
- `skills/video-semantics-analyzer/SKILL.md`：面向长期聚合的单条视频语义，严格区分 verbal evidence、visual evidence、timeline evidence 和 inference。
- `skills/creator-profile-aggregator/SKILL.md`：面向跨视频聚合，强结论需要重复证据；单视频信号必须标记 provisional。

prompt 构建时会自动注入：

- `<analysis_lenses>`：共享 lens 库，来自 `video-analysis-lenses.md`；指定 domain 时会追加对应领域 lens，例如 `--domain finance` 会追加 `domain-finance-lenses.md`。
- `<evidence_anchors>`：当前视频可引用的 transcript、visual notes 和 keyframe ID，例如 `[T1]`、`[V1]`、`[F3]`。

## 产物边界

- `library/raw/`：本地私有原始素材。
- `library/raw/*.asr.chunks/`：长音频 ASR 分片，供 provider 逐片转写。
- `library/shorts/*.short-video-profile.json`：短视频 profile，记录 duration、fps、分辨率、宽高比、竖屏、音轨和是否进入短视频强分析。
- `library/shots/*.shots.json`：shot boundary artifact，记录 shot start/end、duration、代表帧、transition type、detector/provider 和 threshold。
- `library/frames/*.frame-notes.jsonl`：短视频逐帧/密集帧证据索引，记录 timestamp、frame path、shot id、图像尺寸，并预留字幕、蒙版、画中画、贴纸、人的运动关系、镜头运动、转场、滤镜和待 VL/OCR 补强字段。
- `library/shots/*.motion-relations.json`：短视频人物/物体运动关系候选。默认 `schema-baseline` 只记录 frame-to-frame 候选、来源 frame、shot id、时间点和所需 provider，不声称已识别具体人物关系；后续由 pose、tracking、optical flow、OCR 或 VL provider 补强。
- `library/transcripts/`：文字语言，来自 ASR 或人工整理。
- `library/frames/`：抽样关键帧；`*.shots/` 子目录保存 shot 代表帧。
- `library/notes/*.visual.md`：视觉语言，来自 VL 模型。
- `library/costs/*.cost.json`：单条视频成本报告，包含 Qwen-VL token 用量、单价、估算金额、pricing source 和 Codex 费用预留项。
- `library/costs/*.ledger.json`：pipeline 级成本账本，汇总单条视频或创作者批量任务的 Qwen-VL 明细，并保留 ASR、Codex、搜索/核验的 reserved 项；creator pipeline 的预算门槛读取这个 artifact。
- `library/notes/*.source.yaml`：单条来源记录，包含原始 URL、下载路径、metadata 路径、下载 provider、fallback 状态和下载诊断。
- `library/notes/*.summary.md`：快速摘要，不作为长期聚合主数据。
- `library/notes/*.creator-videos.yaml`：创作者视频列表，作为后续批量下载、批量分析和 UP 级聚合的入口。
- `library/notes/*.book-note.md`：手动导入的书籍/笔记。
- `library/runs/`：pipeline run manifest，记录 step 状态、输入输出、错误、provider/model 和耗时。
- `library/runs/*.video-pipeline.status.json`：pipeline 运行态快照，面向 CLI 进度表和后续 live DAG 轮询；包含 pending/running/completed/skipped/failed 状态、当前 step、耗时、artifact paths 和 cost delta。
- `library/runs/*.video-pipeline.live.html`：pipeline 运行态画布，使用独立 step graph 展示 pending/running/completed/skipped/failed；打开静态文件可看嵌入快照，通过本地 HTTP 打开时可轮询同目录 status JSON。
- `library/semantics/*.video-semantics.md`：单条视频语义，是后续聚合的主数据。
- `library/semantics/*.finance-signals.json`：财经 domain 的单条视频结构化信号，记录 instruments、recommendations、macro theses、methodology signals、risk flags 和 evidence gaps；进入 video DAG 和 creator DAG，但不能被视为投资建议。
- `library/semantics/*.book-semantics.md`：书籍/笔记语义，默认没有 visual language。
- `library/timelines/*.timeline.json`：视频时间线事件，包含 transcript chunk、keyframe、内容结构、广告候选和不确定性。
- `library/claims/*.claims.json`：待核验 claim 队列，状态至少从 `unverified` 开始。
- `library/claims/*.verified.json`：外部核验后的 claim 状态、来源、分阶段证据和 verdict；自动判断支持 `supported`、`contradicted`、`unclear`、`unverified`，但没有外部证据时不得升级状态。
- `library/graphs/*.video-dag.json`：视频分析链路的可视化图谱，可由 `tools/video-dag-canvas.html` 直接展示。
- `library/graphs/*.video-dag.html`：嵌入 graph JSON 的静态画布快照，本地打开即可查看；媒体文件仍按相对路径读取 `library/`。
- `library/graphs/*.creator-dag.json` 和 `*.creator-dag.html`：UP/作者级画布。
- `library/distilled/*.topic-profile.md`：跨书籍/笔记/视频的主题聚合草稿。
- `library/distilled/*.creator-profile.md`：创作者级聚合画像。
- `library/distilled/*.creator-profile.validation.json`：creator profile 输出后证据校验报告，只提示缺口，不自动改写 profile。
- `library/skills/` 和 `library/checks/`：从 creator profile 生成、待人工 review 的 Agent 可加载资产。
- `library/checks/*.agent-assets.review.json`：Agent 资产 review manifest，记录每个 skill/check 的 `draft/reviewed/installed/deprecated` 状态。
- `library/reflections/*.reflection.jsonl`：Agent 使用方法论后的复盘记录，用于后续修订 creator profile、skills 和 checks。
- `library/reflections/*.revision-suggestions.md`：基于 reflection log 的修订建议草稿，不自动覆盖原资产。

## 当前真实样本

2026-05-11 已用 `影视飓风` 跑通 3 条 Bilibili 视频样本，生成单条视频 DAG、成本账本、creator profile、creator validation、agent asset draft 和 creator DAG。2026-05-12 已对同一批视频补跑 Qwen-VL visual notes，并重建 video semantics、timeline、claims、video DAG、creator profile 和 creator DAG。当前视觉结论来自 12 帧抽样关键帧，适合支撑场景、物体、屏幕文字和构图判断，不适合作为逐帧动作或精确时间点证据。

同日验证了 Bilibili `owner_id` 入口：`影视飓风` mid `946974` 可用；`燕三嘤嘤嘤` mid `430426421` 在当前网络下仍触发 Bilibili 352/412 风控。平台发现失败时应优先尝试 cookies 或手动 `*.creator-videos.yaml`，不要把失败归因到 ASR、DAG 或聚合层。
