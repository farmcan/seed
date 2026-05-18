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
  -> 本地创作者视频清单
  -> 多条视频 pipeline + budget gate
  -> creator profile + creator DAG + agent assets
  -> `--domain finance` 时按财经 lens 聚合跨视频方法论并生成 finance digest
  -> `--published-after/--published-before` 可限制发布时间窗口

seed run-creator-batch --platform <platform> <owner...>
  -> 批量处理多个 UP/作者，复用 run-creator-pipeline 流程
  -> 适合跑固定样本池和 top UP 并行对比

seed compare-up-profiles --platform <platform> <owner...>
  -> 输出 UP 横向对比 HTML
  -> 显示方法论结构、证据缺口、validation 与成本对齐视角

seed distill-up-list <up-list.yaml>
  -> 按名单一次跑多位 UP 的 creator pipeline（可配置窗口/预算）
  -> 自动生成横向对比 HTML + 每个 UP 的独立 `.up-homepage.html`

seed build-up-homepage --platform <platform> <owner...>
  -> 基于已有 run/manifest 快速补生成每个 UP 的主页卡片视图

seed research-news "<query>"
  -> GDELT 新闻检索 + facts-first 蒸馏
  -> 输出 `library/news/*.news-search.json` 和 `library/distilled/*.news-digest.json`

seed parse-earnings <ticker-or-cik>
  -> SEC EDGAR filings/companyfacts 拉取 + 财报事实蒸馏
  -> 输出 `library/earnings/*.sec-earnings.json` 和 `library/distilled/*.earnings-digest.json`

seed distill-book-methods <book-note.md> --author <author> --title <title>
  -> 读书笔记/高亮 source-grounded 蒸馏
  -> 输出 `library/distilled/*.book-methods.json`
  -> 后续可和 UP profile、新闻 facts、财报 facts、财经 digest 做 cross-source hooks

seed run-book-pipeline <book-note.md> --author <author> --title <title>
  -> 本地 Markdown 读书笔记一键跑完 source artifact + methods JSON + HTML report + agent playbook
  -> 输出 `library/notes/*.book-source.json`、`library/distilled/*.book-methods.json`、`library/reports/*.book-methods-report.html`、`library/checks/*.book-methods-playbook.md`
```

这些命令已经是当前优先入口；其他 CLI 视为可组合 step 或调试入口。新增功能如果不能进入 pipeline、不能生成稳定 artifact、不能被 DAG 或 creator aggregation 消费，就不应作为主功能推进。

## 功能模块总览

| 模块 | CLI | 主要代码 | 主要产物 |
| --- | --- | --- | --- |
| 来源采集 | `seed ingest-url` | `src/seed/sources/`, `src/seed/library.py` | `library/raw/*`, `library/notes/*.source.yaml` |
| 创作者清单输入 | 手工整理清单 + `seed run-creator-pipeline` | `src/seed/creator_pipeline.py`, `src/seed/library.py` | `library/notes/*.creator-videos.yaml` |
| 创作者批量入口 | `seed run-creator-batch` | `src/seed/cli.py`, `src/seed/creator_pipeline.py` | 多 UP 批量 manifest、creator profile、creator DAG、agent assets（按顺序运行） |
| 视频 pipeline | `seed run-video-pipeline` | `src/seed/pipeline.py` | pipeline manifest、单条视频全量产物、cost ledger |
| 创作者 pipeline | `seed run-creator-pipeline` | `src/seed/creator_pipeline.py` | 多视频 manifest、creator profile、creator DAG、creator cost ledger |
| ASR 转写 | `seed transcribe-media` | `src/seed/media.py`, `src/seed/asr/`, `src/seed/transcripts.py` | `library/raw/*.asr.mp3`, `library/raw/*.asr.chunks/*`, `library/transcripts/*.transcript.md` |
| 视觉语言 | `seed extract-frames`, `seed analyze-frames` | `src/seed/vision/` | `library/frames/*`, `library/notes/*.visual.md` |
| 短视频结构 | `seed profile-short-video`, `seed detect-shots`, `seed build-frame-notes`, `seed build-motion-relations`, `seed run-video-pipeline` | `src/seed/shorts.py`, `src/seed/pipeline.py` | `library/shorts/*.short-video-profile.json`, `library/shots/*.shots.json`, `library/shots/*.motion-relations.json`, `library/frames/*.frame-notes.jsonl`, `library/frames/*.shots/*` |
| 成本计量 | `seed analyze-frames`, `seed build-cost-ledger`, `seed build-video-dag` | `src/seed/costs.py`, `src/seed/graphs/video_dag.py` | `library/costs/*.cost.json`, `library/costs/*.ledger.json`, DAG cost 节点 |
| 书籍/笔记 | `seed import-book-note`, `seed import-book-source`, `seed analyze-book-note`, `seed distill-book-methods`, `seed build-book-methods-report`, `seed build-book-methods-playbook`, `seed run-book-pipeline`, `seed aggregate-topic` | `src/seed/books.py`, `skills/book-method-distiller/SKILL.md` | `library/notes/*.book-note.md`, `library/notes/*.book-source.json`, `library/semantics/*.book-semantics.md`, `library/distilled/*.book-methods.json`, `library/reports/*.book-methods-report.html`, `library/checks/*.book-methods-playbook.md`, `library/distilled/*.topic-profile.md` |
| 快速总结 | `seed summarize-transcript` | `src/seed/summarizers/`, `src/seed/skill_refs.py`, `src/seed/semantics/evidence.py` | `library/notes/*.summary.md` |
| 视频语义 | `seed analyze-video-semantics` | `src/seed/semantics/analyzer.py`, `src/seed/skill_refs.py`, `src/seed/semantics/evidence.py` | `library/semantics/*.video-semantics.md` |
| 领域信号 | `seed extract-finance-signals`, `seed build-finance-digest`, `seed enrich-finance-prices`, `seed enrich-finance-news`, `seed build-finance-news-report`, `seed run-video-pipeline --domain finance`, `seed run-creator-pipeline --domain finance` | `src/seed/domains/finance.py`, `src/seed/reports/finance_news.py`, `src/seed/skill_refs.py` | `library/semantics/*.finance-signals.json`, `library/distilled/*.finance-digest.json`, `*.finance-digest.priced.json`, `*.finance-digest.news-context.json`, `library/reports/*.finance-news-report.html`, video DAG / creator DAG finance 节点 |
| 新闻检索与事实蒸馏 | `seed search-news`, `seed distill-news-facts`, `seed research-news`, `seed extract-news-facts`, `seed run-video-pipeline --domain news` | `src/seed/domains/news.py`, `skills/facts-distiller/SKILL.md`, `domain-news-lenses.md` | `library/news/*.news-search.json`, `library/distilled/*.news-digest.json`, `library/semantics/*.news-facts.json`, video DAG news facts 节点 |
| 财报解析 | `seed fetch-earnings`, `seed distill-earnings`, `seed parse-earnings`, `seed extract-earnings-analysis`, `seed run-video-pipeline --domain earnings` | `src/seed/domains/earnings.py`, `skills/earnings-parser/SKILL.md`, `domain-earnings-lenses.md` | `library/earnings/*.sec-earnings.json`, `library/distilled/*.earnings-digest.json`, `library/semantics/*.earnings-analysis.json`, video DAG earnings 节点 |
| 时间线 | `seed build-timeline` | `src/seed/timeline.py` | `library/timelines/*.timeline.json` |
| 事实核验队列 | `seed extract-claims` | `src/seed/factcheck.py` | `library/claims/*.claims.json` |
| 事实核验 | `seed verify-claims` | `src/seed/claim_verification.py` | `library/claims/*.verified.json` |
| DAG 图谱 | `seed build-video-dag`, `seed serve-video-dag`, `seed export-video-dag-html` | `src/seed/graphs/video_dag.py`, `src/seed/dag_server.py`, `src/seed/dag_export.py`, `tools/video-dag-canvas.html` | `library/graphs/*.video-dag.json`, `library/graphs/*.video-dag.html` |
| Creator DAG | `seed build-creator-dag` | `src/seed/graphs/creator_dag.py` | `library/graphs/*.creator-dag.json`, `library/graphs/*.creator-dag.html` |
| 创作者聚合 | `seed aggregate-owner`, `seed validate-creator-profile` | `src/seed/semantics/aggregator.py`, `src/seed/semantics/validation.py` | `library/distilled/*.creator-profile.md`, `*.creator-profile.validation.json` |
| Agent 资产生成 | `seed generate-agent-assets`, `seed review-agent-assets`, `seed record-reflection`, `seed suggest-revisions` | `src/seed/agent_assets.py`, `src/seed/reflections.py` | `library/skills/*/SKILL.md`, `library/checks/*.md`, `library/checks/*.agent-assets.review.json`, `library/reflections/*` |
| 横向对比 | `seed compare-up-profiles` | `src/seed/cross_compare.py` | `library/reports/*.up-comparison.html` |
| UP 主页与名单蒸馏 | `seed distill-up-list`, `seed build-up-homepage` | `src/seed/cli.py` | `library/reports/*.up-comparison.html`, `library/reports/*.up-homepage.html` |

当前视频 DAG 会展示本地视频、音频、关键帧截图、short profile、shot strip、frame evidence notes、motion relation candidates、transcript、visual notes、cost ledger、timeline event、semantic 子节点、可选 finance signals、news facts、earnings analysis、creator signals、fact-check queue 和 agent assets。Creator DAG 以 UP/作者级 profile、方法论和 Agent 资产为主，同时每条视频节点都可展开本地视频、音频、截图 gallery、可选 finance signals 和单条 video DAG HTML 入口。带 `start_seconds` 的 timeline event、shot、frame note 和 motion relation 节点会写入 `media_anchor`，画布详情区可以把视频/音频定位到对应时间点。DOM/ELK 画布保留卡片式视觉，默认简版显示，节点媒体默认渲染，顶部 `媒体` 按钮可一键隐藏或恢复，卡片正文默认折叠，右侧详情默认关闭。

## 模块边界

- `sources/`：平台采集适配器。只关心 URL、授权、下载、metadata，不做内容理解；下载结果需要记录 provider、fallback 和 cookies 相关诊断。
- `creator_pipeline.py`：消费本地清单（`*.creator-videos.yaml`）进行逐条视频处理。默认按清单顺序和限制条件分发任务，已有 source record 但没有本地 `raw_path` 时仍继续下载补齐素材。
- `pipeline.py`：负责把现有单步命令背后的业务函数串成单条视频 pipeline，写入 run manifest、status JSON 和 live DAG HTML，并支持断点续跑。每个 step 记录状态、输入输出、provider/model、耗时、artifact paths 和 cost delta；CLI 可用 Rich 进度表实时展示，live DAG 只展示运行态 step graph，不混入最终内容 DAG。
- `creator_pipeline.py`：负责创作者级批量任务、发布时间窗口过滤、失败继续、成本预算门槛、creator profile 聚合、agent assets 生成和 creator DAG 导出；`--max-estimated-cost` 到达后停止后续视频，并在 manifest 写入 `budget_exceeded`，后处理步骤写入 `creator_steps`。
- `asr/` 和 `media.py`：音频抽取、超限音频分片和线上 ASR provider。只产出 transcript；长音频会同时按文件大小和 `ffprobe` 时长判断是否切片，默认超过 300 秒会分段，transcript 会在 frontmatter 记录 `asr_chunks`。
- `vision/`：抽帧、Qwen-VL 调用和 visual notes。只描述画面证据，不负责最终方法论；Qwen-VL provider 需要返回 token usage，供成本模块记录。
- `shorts.py`：短视频 profile、shot boundary baseline、shot 代表帧、frame evidence notes 和 motion relation candidates。默认用 `ffprobe` 判断 `duration <= 60s` 是否进入短视频强分析，用 `ffmpeg` scene threshold 生成本地 shot artifact；`frame_notes` 默认按 shot 代表帧生成低成本 JSONL，并预留蒙版、画中画、贴纸、字幕、人的运动关系、滤镜、变速、转场和剪辑意图字段；`motion_relations` 默认只从相邻 frame notes 生成可追溯候选并标记 `needs_pose_or_vl`，后续可把 PySceneDetect/TransNetV2、逐帧 Qwen-VL/OCR、MediaPipe/OpenPose/YOLO pose 和 OpenCV optical flow 接成 provider。
- `costs.py`：统一写入单条视频成本报告和 pipeline cost ledger。默认记录 Qwen-VL token 用量、单价来源、估算金额，并为 ASR、Codex、搜索/核验保留成本项；实际价格可通过环境变量覆盖。
- `skill_refs.py`：读取共享 video analysis lenses 和可选 domain lenses。prompt 构建器只引用这个入口，避免各模块复制 lens 文本。
- `domains/finance.py`：财经领域信号抽取、窗口汇总、可选行情补强和新闻 facts 上下文。输入单条 `video-semantics.md`，输出 `*.finance-signals.json`，每条信号优先返回 `viewpoint_events`（主对象）；输入多条 signals，输出 `*.finance-digest.json`；显式 ticker mapping 后可用 Stooq 日线生成 `*.finance-digest.priced.json`；`seed enrich-finance-news` 可把 `*.news-digest.json` 的 facts、industry impacts 和 market relevance 挂到事件级 `news_context`，只做事实引用；`seed build-finance-news-report` 把 news-context digest 渲染成卡片式 HTML 报告。所有观点都必须标记为创作者观点，不是 Seed 投资建议。
- `domains/news.py`：新闻检索和 facts-first 蒸馏。默认 provider 是 GDELT DOC 2.0 `artlist` JSON，检索结果写入 `library/news/*.news-search.json`；Codex 蒸馏只汇总 facts、reported claims、industry impacts、source gaps 和 open questions，输出 `*.news-digest.json`。视频 pipeline 的 `--domain news` 会从 `video-semantics.md` 生成 `*.news-facts.json`，供 DAG 和 fact-check 消费。
- `domains/earnings.py`：财报解析和 SEC baseline。默认 provider 是 SEC EDGAR `submissions` 与 XBRL `companyfacts` JSON，ticker/CIK 映射来自 SEC `company_tickers.json`；原始事实写入 `library/earnings/*.sec-earnings.json`，Codex 蒸馏输出 `*.earnings-digest.json`。视频 pipeline 的 `--domain earnings` 会把视频里的财报说法提取成待 SEC 核验的 `*.earnings-analysis.json`。
- `books.py`：书籍/读书笔记导入、语义化和方法论蒸馏。初版 provider 是本地 Markdown；后续 provider 扩展 Readwise/Reader export、Zotero annotations、Kindle/Koreader highlights 时必须落到统一 `book-source` artifact，而不是把某个平台格式写进 prompt。长书处理采用 evidence blocks -> chapter/book methods -> topic profile 的分层合成，借鉴 NotebookLM source grounding、LlamaIndex/LangChain map-reduce/refine/tree summarize、Readwise/Zotero annotations 和 Zettelkasten literature/permanent notes。
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
- `skills/video-semantics-analyzer/references/domain-news-lenses.md`：新闻领域 lens，强调 facts、reported claims、interpretation、market mechanism 和 source gaps 分离；只在 `--domain news` 时注入。
- `skills/video-semantics-analyzer/references/domain-earnings-lenses.md`：财报领域 lens，强调 SEC/公司 IR primary source、metric period/unit/form/accession 和 source gap；只在 `--domain earnings` 时注入。
- `skills/facts-distiller/SKILL.md`：检索结果 facts-first 蒸馏 skill，用于 `distill-news-facts` 和 `research-news`。
- `skills/earnings-parser/SKILL.md`：SEC 财报事实解析 skill，用于 `distill-earnings` 和 `parse-earnings`。
- `skills/book-method-distiller/SKILL.md`：书籍/读书笔记方法论蒸馏 skill，用于 `distill-book-methods`；输出必须保留 `B*` evidence refs、适用边界、anti-patterns、source gaps、open questions 和 cross-source hooks。
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
- `library/news/*.news-search.json`：新闻检索结果，默认来自 GDELT DOC 2.0 Article List JSON，保留 query、时间窗口、source URL、标题、来源域名、语言、国家和发布时间。
- `library/earnings/*.sec-earnings.json`：SEC 财报事实 artifact，保留 CIK、ticker、公司名、最近 filing、filing index URL、XBRL 指标、单位、期间、form、filed date 和 accession number。
- `library/costs/*.cost.json`：单条视频成本报告，包含 Qwen-VL token 用量、单价、估算金额、pricing source 和 Codex 费用预留项。
- `library/costs/*.ledger.json`：pipeline 级成本账本，汇总单条视频或创作者批量任务的 Qwen-VL 明细，并保留 ASR、Codex、搜索/核验的 reserved 项；creator pipeline 的预算门槛读取这个 artifact。
- `library/notes/*.source.yaml`：单条来源记录，包含原始 URL、下载路径、metadata 路径、下载 provider、fallback 状态和下载诊断。
- `library/notes/*.summary.md`：快速摘要，不作为长期聚合主数据。
- `library/notes/*.creator-videos.yaml`：创作者本地清单，驱动批量分析、聚合与 creator DAG 入口。
- `library/notes/*.book-note.md`：手动导入的书籍/笔记。
- `library/notes/*.book-source.json`：书籍/读书高亮统一 source artifact，记录 provider、source metadata、highlight/note、location、tags、source URL 和 `B*` evidence refs；当前 provider 是本地 Markdown，后续兼容 Readwise/Zotero/Kindle/Koreader。
- `library/reports/*.up-comparison.html`：UP 横向对比报告。
- `library/runs/`：pipeline run manifest，记录 step 状态、输入输出、错误、provider/model 和耗时。
- `library/runs/*.video-pipeline.status.json`：pipeline 运行态快照，面向 CLI 进度表和后续 live DAG 轮询；包含 pending/running/completed/skipped/failed 状态、当前 step、耗时、artifact paths 和 cost delta。
- `library/runs/*.video-pipeline.live.html`：pipeline 运行态画布，使用独立 step graph 展示 pending/running/completed/skipped/failed；打开静态文件可看嵌入快照，通过本地 HTTP 打开时可轮询同目录 status JSON。
- `library/semantics/*.video-semantics.md`：单条视频语义，是后续聚合的主数据。
- `library/semantics/*.finance-signals.json`：财经 domain 的单条视频结构化信号，记录 instruments、`viewpoint_events`、兼容的 `recommendations`、macro theses、methodology signals、risk flags 和 evidence gaps；进入 video DAG 和 creator DAG，但不能被视为投资建议。
- `library/semantics/*.news-facts.json`：新闻 domain 的视频事实队列，记录 stated facts、reported claims、interpretations、industry impacts、source gaps 和 open questions；进入 video DAG。
- `library/semantics/*.earnings-analysis.json`：财报 domain 的视频说法队列，记录 companies、earnings claims、drivers、risks 和待 SEC 核验缺口；进入 video DAG。
- `library/semantics/*.book-semantics.md`：书籍/笔记语义，默认没有 visual language。
- `library/timelines/*.timeline.json`：视频时间线事件，包含 transcript chunk、keyframe、内容结构、广告候选和不确定性。
- `library/claims/*.claims.json`：待核验 claim 队列，状态至少从 `unverified` 开始。
- `library/claims/*.verified.json`：外部核验后的 claim 状态、来源、分阶段证据和 verdict；自动判断支持 `supported`、`contradicted`、`unclear`、`unverified`，但没有外部证据时不得升级状态。
- `library/graphs/*.video-dag.json`：视频分析链路的可视化图谱，可由 `tools/video-dag-canvas.html` 直接展示。
- `library/graphs/*.video-dag.html`：嵌入 graph JSON 的静态画布快照，本地打开即可查看；媒体文件仍按相对路径读取 `library/`。
- `library/graphs/*.creator-dag.json` 和 `*.creator-dag.html`：UP/作者级画布。
- `library/distilled/*.topic-profile.md`：跨书籍/笔记/视频的主题聚合草稿。
- `library/distilled/*.book-methods.json`：读书笔记的方法论蒸馏结果，记录 stable principles、decision rules、mental models、agent checks、适用边界、anti-patterns、source gaps 和 open questions；用于给 UP/新闻/财报分析提供长期方法论参照。
- `library/reports/*.book-methods-report.html`：面向人工阅读的读书方法论卡片报告，展示原则、规则、模型、agent checks、cross-source hooks、source gaps 和 open questions。
- `library/checks/*.book-methods-playbook.md`：面向 agent 使用前检查的读书方法论 playbook，默认 draft，必须保留 evidence refs 和 source gaps。
- `library/distilled/*.creator-profile.md`：创作者级聚合画像。
- `library/distilled/*.finance-digest.json`：财经 domain 的 UP/窗口级汇总，聚合多条 finance signals 的标的、推荐/观察、宏观 thesis、方法论信号、风险和证据缺口；不包含行情后验时只能作为观点汇总。
- `library/distilled/*.finance-digest.priced.json`：在 finance digest 基础上追加 event-level 价格后验，包含 1D/5D/20D/60D/latest horizon、asset/benchmark/relative return、max drawdown、交易日对齐和 ticker mapping 来源；不做交易建议。
- `library/distilled/*.finance-digest.news-context.json`：在 finance digest 基础上为 `viewpoint_events` 追加 `news_context`，引用 news digest 的 facts、source URLs、industry impacts、market relevance、source gaps 和 open questions；只作为事实上下文，不改变创作者观点，也不做交易建议。
- `library/reports/*.finance-news-report.html`：面向人工阅读的财经观点新闻事实报告，按热点、UP、视频、观点事件、facts 对照、行业影响、source gaps 和 open questions 展示。
- `library/distilled/*.news-digest.json`：新闻检索后的 facts-first digest，聚合 facts、reported claims、source coverage、industry impacts、market relevance、source gaps 和 open questions。
- `library/distilled/*.earnings-digest.json`：SEC 财报事实 digest，聚合 latest filings、financial snapshot、changes/drivers、industry implications、source gaps 和 open questions；不做交易建议。
- `library/distilled/*.creator-profile.validation.json`：creator profile 输出后证据校验报告，只提示缺口，不自动改写 profile。
- `library/skills/` 和 `library/checks/`：从 creator profile 生成、待人工 review 的 Agent 可加载资产。
- `library/checks/*.agent-assets.review.json`：Agent 资产 review manifest，记录每个 skill/check 的 `draft/reviewed/installed/deprecated` 状态。
- `library/reflections/*.reflection.jsonl`：Agent 使用方法论后的复盘记录，用于后续修订 creator profile、skills 和 checks。
- `library/reflections/*.revision-suggestions.md`：基于 reflection log 的修订建议草稿，不自动覆盖原资产。

## 当前真实样本

已在本地清单模式下跑通 3 条样本并完成 DAG、creator profile、agent asset draft 与 creator DAG 的闭环；随后补跑 Qwen-VL visual notes 重建 video semantics、timeline、claims、video DAG 与 profile。当前视觉结论来自 12 帧抽样关键帧，适合支撑场景、物体、屏幕文字和构图判断，不适合作为逐帧动作或精确时间点证据。
