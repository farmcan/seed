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
- [x] 增强 `seed verify-claims` 的自动判断。
  - 状态至少支持 `supported`、`contradicted`、`unclear`、`unverified`。
  - 没有外部证据时不得把 claim 标成 verified。
  - 已按 claim decomposition、query planning、evidence snippets、source score、verdict 分阶段写入 artifact；自动判断保持保守。
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
  - 输入平台 + UP/作者名称，按本地创作者清单或预置映射批量跑视频 pipeline。
  - 已支持 limit、start-index、失败继续、跳过已完成、成本预算上限、creator profile 聚合、agent assets 生成和 creator DAG HTML 导出。
- [x] 为 `seed run-creator-pipeline` 增加成本预算上限。
  - 建议先做本地 budget gate：开始处理下一条视频前读取已有 cost ledger，超过预算则停止并写入 run manifest。
- [x] 增加 `seed build-creator-dag`。
  - 按 UP/作者展示多条视频、每条状态、共性方法论、代表证据、反例、成本和 reflection 入口。
- [x] 强化 creator profile 的证据引用。
  - 当前 prompt 已注入共享 lenses；下一步要在输出后做结构校验，要求每个创作者级结论回溯到具体视频、timestamp/keyframe/transcript chunk 或 semantic section。
- [x] Agent 资产 review 流程。
  - 从 creator profile 生成的 skill/check 需要人工确认状态，例如 `draft`、`reviewed`、`installed`。
  - `generate-agent-assets` 会写入 review manifest；`review-agent-assets` 支持 `draft/reviewed/installed/deprecated` 状态流转。

## P3：书籍和非视频来源

- [x] 增加手动书籍/笔记导入。
  - 保留作者、章节、页码/位置、引用边界。
- [x] 增加 book semantics artifact。
  - 类似 video semantics，但默认没有 visual language。
- [x] 增加 book methods 第一版。
  - 参考 NotebookLM source-grounded summary、LlamaIndex/LangChain 长文档合成、Readwise/Zotero highlights/annotations 和 Zettelkasten/evergreen notes。
  - `seed distill-book-methods` 把读书笔记切成 `B*` evidence blocks，输出 stable principles、decision rules、mental models、agent checks、适用边界、anti-patterns、cross-source hooks、source gaps 和 open questions。
- [x] 支持按作者/主题聚合。
  - 复用 creator aggregation 的思路，但不绑定视频平台。
- [x] 增加 reading source artifact。
  - 已新增 `seed import-book-source`，当前支持本地 Markdown 导入为 `library/notes/*.book-source.json`。
  - Artifact 统一记录 provider、source metadata、author/title、location、highlight、note、tag、source_url 和 `B*` evidence refs。
  - Provider 分层仍按本地 Markdown/CSV 优先；Readwise export、Zotero annotations、Kindle/Koreader highlights 后续做可选 provider。
- [ ] 调研并接入微信读书（WeRead）数据源。
  - 第一步优先官方链路：研究 `weread-skills` + `WEREAD_API_KEY`，目标先能消费书架、读书元数据、笔记/划线到 `library/notes/*.book-source.json`。
  - 非官方 cookie / 逆向接口保留为可选备选，不做主链路，不在核心 pipeline 默认路径强依赖。
  - 需要先明确产物约束与合规边界：是否可按书源与作者稳定抽取、是否可持续更新、是否保留时间戳与来源引用。
- [ ] 增加分层 book distillation。
  - 目标：block/chapter methods -> book methods -> topic profile，不把整本书一次性塞进 prompt。
  - 借鉴 `map_reduce/refine/tree_summarize`，保留每层 source gaps 和冲突观点。
  - [x] P0 先生成 deterministic `*.book-layers.json`：按 Markdown heading 把 `B*` evidence blocks 归入 section/chapter 候选，记录 section-level method candidates、book-level distillation strategy 和 source gaps，并注入 `distill-book-methods` prompt。
  - [ ] P1 再做真正的 section methods -> book methods 多阶段 LLM 合成，避免长书一次性进入 prompt。
- [x] 增加 book methods 报告和 playbook 输出。
  - 新增 `seed build-book-methods-report`，输出 `library/reports/*.book-methods-report.html` 给人看。
  - 新增 `seed build-book-methods-playbook`，输出 `library/checks/*.book-methods-playbook.md` 给 agent 使用前检查。
- [x] 增加 book homepage 和作者级聚合入口。
  - 新增 `seed build-book-homepage`，消费 book-source、book-layers、book-methods、report 和 playbook，输出 `library/reports/*.book-homepage.html`。
  - 新增 `seed build-book-author-profile`，对同一作者多本 `*.book-methods.json` 做确定性聚合，输出 `library/distilled/*.book-author-profile.json`。
  - 新增 `seed build-book-author-homepage`，消费 author profile 输出 `library/reports/*.book-author-homepage.html`。
  - 当前作者 profile 是 deterministic aggregation，不是 LLM 作者思想综合；后续再做多阶段作者级蒸馏。
- [x] 增加 book 一键 pipeline。
  - 新增 `seed run-book-pipeline`，输入本地 Markdown 读书笔记后一次生成 `book-source.json`、`book-layers.json`、`book-methods.json`、HTML 报告、book homepage 和 agent playbook。
  - `--dry-run` 只生成 Codex prompt，不尝试渲染报告和 playbook。
- [ ] 把 book methods 接入跨来源对照。
  - 在 creator profile / finance digest / news facts / earnings digest 中引用 `cross_source_hooks`，用于判断 UP 观点是否符合长期方法论、是否需要事实核验或边界提醒。

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
- [x] 实现 claim verification 分阶段 artifact。
  - claim -> query plan -> evidence snippets -> source score -> verdict -> uncertainty。
  - 没有足够来源时只能输出 `unclear` 或 `unverified`。
- [x] 实现 creator profile evidence validator。
  - 检查 creator profile 中强结论是否含视频、timestamp/keyframe/transcript chunk 或 semantic section 引用。
  - 不自动改写 profile，先输出 validation report。
- [x] 增强 DAG 媒体联动。
  - 从 timeline event、transcript chunk 或 keyframe 节点跳转到视频/音频对应位置。
  - 已给带 `start_seconds` 的 timeline event 写入 `media_anchor`，画布详情区可按时间点预览视频/音频。
- [x] 优化 DOM/ELK 卡片式画布性能。
  - 保留当前 canvas 视觉，不切到低信息密度图谱库。
  - 已做默认简版、节点媒体默认显示、媒体一键开关、卡片正文手动展开、视口裁剪和右侧详情可收起。
- [x] 增强 Creator DAG 的媒体证据入口。
  - UP/作者级画布默认展示 profile、方法论、视频语义和 Agent 资产；每条视频节点可展开 4 个子节点：单条 video DAG HTML、本地视频、本地音频、关键帧截图 gallery。
  - 顶部 toolbar 改为自适应高度，控件换行时不再被 canvas 覆盖。
- [x] 增强 pipeline 运行可观测性。
  - 目标：用户运行一条视频时，能看到预计耗时、当前 step、已完成/运行中/失败/跳过状态、每步耗时、关键日志、当前产物路径和成本增量。
  - [x] P0 先增强 CLI 进度：用 Rich table 展示 step 状态，运行结束后输出耗时汇总；每个 step 在 manifest 写入 `duration_seconds`、`artifact_paths` 和 `cost_delta`。
  - [x] P1 增加 run status artifact：在 `library/runs/*.video-pipeline.yaml` 之外同步写一个更适合前端轮询的 `*.status.json`，每个 step 开始/结束时更新。
  - [x] P2 增加 live DAG preview：生成 `*.video-pipeline.live.html`，节点默认有 `pending/running/completed/skipped/failed` 状态；未完成节点虚线/半透明，运行中节点有轻量 pulse 动画；前端优先轮询同目录 status JSON，静态打开时至少展示嵌入快照。
  - [x] P3 增加历史耗时粗估和运行摘要：status/manifest 顶层记录 run duration、step counts、estimated total/remaining；每步记录 `message`、`estimated_duration_seconds` 和历史样本数，CLI 与 live DAG 同步展示。
  - P4 再评估是否需要 Prefect/Dagster/Temporal 这类外部编排。当前不引入重型服务，除非出现多 worker、定时调度、复杂重试或团队协作需求。
  - 设计原则：运行态画布是辅助视图，不替代准确的 manifest、日志和最终静态 DAG；动画只表达状态，不承载核心信息。

## P6：真实样本验证

- [x] 跑通真实 UP 三条视频样本。
  - 2026-05-11 用 `影视飓风` 跑通 3 条 Bilibili 视频：下载、ASR 分段、video semantics、timeline、claims、cost ledger、video DAG、creator profile、creator validation、agent assets 和 creator DAG。
  - 2026-05-12 已对同一批 3 条视频补跑 Qwen-VL visual notes，并重建 video semantics、timeline、claims、video DAG、creator profile 和 creator DAG；当前视觉证据仍是 12 帧抽样，不等于逐帧完整分析。
- [x] 明确样本来源输入为清单。
  - `run-creator-pipeline` 与 `run-creator-batch` 优先消费本地 creator 视频清单文件，线上抓取入口不作为主链路。
- [x] 修复 source-only 记录阻止后续下载的问题。
  - 批量清单入口在 `--skip-existing` 下，只有在已有 source record 同时存在本地 `raw_path` 时才跳过；如果之前只是记录 URL，会继续下载并补齐 source record。
- [x] 修复长音频 ASR 只按文件大小判断的问题。
  - DashScope 可能因音频时长拒绝请求；当前 ASR chunking 同时按文件大小和 `ffprobe` duration 判断，默认超过 300 秒会切片。
- [x] 增加 UP 批量执行入口。
  - 新增 `run-creator-batch`，支持一次跑多位 UP，用于固定样本池的回归测试。
  - 当前计划默认用同一参数批量跑：`影视飓风`、`燕三嘤嘤嘤`（后者预计仍然触发 352/412，用于验证失败提示链路），以及后续补充的财经/行业样本池。
- [x] 增加 UP 横向对比入口。
  - 新增 `compare-up-profiles`，直接读取已有 profile / manifest / ledger / validation，生成 `library/reports/*.up-comparison.html`。
  - 对比报表包含：视频样本量、video runs 完成率、validation 结果、缺口计数、方法点数、skill 数和 cost 聚合，支持快速横向决策。
- [x] 增加 UP 名单蒸馏入口。
  - 新增 `distill-up-list`：读取 UP 名单配置后，一次性跑 creator pipeline 并生成横向报告。
  - 同时自动产出每位 UP 的 `.up-homepage.html` 主页，便于点击查看概要与产物入口。
  - 新增 `build-up-homepage`：对已有结果快速重建 UP 主页。
  - 财经名单支持 `news_digest_paths` 配置；如果已有 news digest，会自动生成 news-context finance digest、finance-news-report HTML，并链接到 UP 主页。

## P7：60s 短视频强分析

- [x] 增加短视频 profile 判断。
  - 输入本地视频或 URL 后先用 `ffprobe` 记录 duration、fps、分辨率、宽高比、音轨信息和平台来源。
  - 默认规则：`duration <= 60s` 进入短视频强分析；允许 CLI 显式 `--short-form/--long-form` 覆盖。
  - artifact：`library/shorts/*.short-video-profile.json`，已由 pipeline 和 DAG 消费。
- [x] 增加 shot boundary artifact。
  - P0 已先接 `ffmpeg` scene threshold 做本地 baseline；输出 shot start/end、duration、代表帧、transition confidence、detector/provider。
  - P1 再把 TransNetV2 做成可选 provider；不要把深度模型依赖放进默认安装路径。
  - artifact：`library/shots/*.shots.json`；DAG 中展示 shot strip，并允许点击 shot 跳转视频时间段。
- [x] 增加短视频逐帧/密集帧证据索引。
  - 已支持 `--frame-mode every-frame|fps|shot-keyframes`；默认先用 `shot-keyframes` 控成本，用户要求强分析时再启用逐帧或 1 fps。
  - 每帧已记录 timestamp、frame path、shot id、图像尺寸，并预留 VL caption、OCR/text overlay、主体/物体、场景、构图、动作、人的运动关系、蒙版、画中画、贴纸、字幕、滤镜、变速、转场和剪辑意图字段。
  - artifact：`library/frames/*.frame-notes.jsonl`，已接入 pipeline 和 DAG。
- [x] 增加短视频语义 skill/lens。
  - 扩展共享 `video-analysis-lenses.md`，不要另起一套重复 prompt。
  - 输出结构聚焦：前三秒 hook、beat map、shot function、视觉语言、字幕/OCR、剪辑技巧、节奏密度、payoff/loop/CTA、可复用脚本模板。
  - 强结论必须引用 transcript、OCR、shot、frame evidence；营销式“爆款公式”只能作为 lens，不能当证据。
- [x] 把短视频强分析接入 DAG。
  - Video DAG 增加 short profile、shot strip、frame evidence gallery、OCR/text overlay、editing technique 节点。
  - 当前已接入 short profile、shot strip、shot 代表帧节点和 frame evidence notes；蒙版、画中画、贴纸、字幕、人的运动关系、OCR/text overlay、editing technique 字段已预留，后续由 VL/OCR provider 补齐。
- [x] 增加人物/物体运动关系 baseline artifact。
  - 输出 `library/shots/*.motion-relations.json`，由 `build-motion-relations` 和 `run-video-pipeline` 生成。
  - 默认 `schema-baseline` 只根据相邻 frame notes 生成可追溯候选，状态为 `needs_pose_or_vl`，不把未识别的动作关系写成结论。
  - Video DAG 已接入 `motion-relations` 节点和可点击的 relation 子节点，带时间点时写入 `media_anchor`。
- [x] 跑真实短视频样本验证。
  - 以本地 `library/raw/short-effects-demo.mp4`（3.6s）验证短视频链路：`run-video-pipeline` 能稳定进入 short profile / shots / frame notes / motion relations / timeline / claims / DAG，全链路完备。
  - 发现并修复无音频素材导致转写中断问题：`short-profile` 可继续，`transcribe` 输出 `no_audio_stream` reason 的 skipped 状态。
  - 选 3 条 60s 内 Bilibili/小红书/手动本地视频，至少覆盖口播型、图文字幕型、强剪辑型。
  - 验证项：shot boundary 是否合理、逐帧成本是否可控、DAG 是否可读、短视频 semantics 是否比长视频模板更有信息密度。
- [ ] 接入可选视觉 provider。
  - [x] OCR sidecar baseline：`build-frame-notes` 和 `run-video-pipeline` 支持 `--ocr-provider sidecar-json --ocr-path <json>`，把外部 OCR 工具产出的 `text/start_seconds/end_seconds/bbox/confidence` 段落按时间戳写入 frame notes，不引入默认重依赖。
  - [x] Frame motion baseline：`build-frame-notes` 和 `run-video-pipeline` 支持 `--frame-motion-provider ffmpeg-diff`，用相邻采样帧的 ffmpeg difference score 记录 `frame_delta` 和 `editing.camera_motion` 候选；只表达视觉变化强度，不识别人、物体或真实 optical flow。
  - OCR provider：优先调研 PaddleOCR / RapidVideOCR；输出字幕区域、字幕文字、位置、样式和时间段。
  - Human-motion provider：优先调研 MediaPipe / OpenPose / YOLO pose；输出人物框、pose/hand/face landmarks、人物间距离变化、人物与物体/镜头运动关系，并补强 `*.motion-relations.json`。
  - Motion/editing provider：优先用 OpenCV optical flow 做镜头运动、运动强度和速度变化 baseline；复杂剪辑效果交给 VL/LLM 基于 frame evidence 判断。
  - 所有 provider 都必须可选，默认链路只保留 deterministic baseline 和 schema，不引入重依赖。

## P8：财经 UP 数据蒸馏

- [x] 调研财经/finfluencer 分析参考。
  - 已参考 VideoConviction：把金融视频里的 ticker/标的、action、conviction、reasoning 和回测管线拆开。
  - 已参考 AlphaCheck：频道级追踪不只是摘要，还要对齐视频发布时间、标的、当时价格、当前价格、benchmark 和上下文理由。
  - 已参考 FinGPT、FinRobot、FinBERT、FinRL：作为金融文本任务 taxonomy、金融 agent 数据源、情绪/stance 和策略表达的参考，不直接把它们塞进默认依赖。
  - 新增调研结论：VideoConviction 的 annotation workflow 比普通 summary 更适合 Seed，核心对象应是“观点事件”，包含 recommendation presence、ticker/entity、action、price/quantity、action timestamps、conviction score 和后验价格。
  - 新增调研结论：TickerReceipts/AlphaCheck 类产品把 YouTube stock picks 做成 time-stamped feed 和 channel track record，说明财经 UP 方向必须把“证据时间点 + 后验表现 + 频道级画像”放在同一条链路。
  - 新增调研结论：FinCap 这类短视频金融 caption 研究强调 T/A/V 多模态组合，财经短视频不能只看 ASR；口播、字幕/OCR、图表/持仓截图和语气都可能影响 conviction 判断。
- [x] 增加财经 domain lens。
  - `--domain finance` 会追加 `domain-finance-lenses.md`，用于 `summarize-transcript`、`analyze-video-semantics`、`aggregate-owner`、`run-video-pipeline` 和 `run-creator-pipeline`。
  - 领域 lens 只约束结构和风险边界，不生成 Seed 自己的投资建议。
- [x] 增加单条视频 finance signals artifact。
  - `seed extract-finance-signals <semantics.md>` 或 `seed run-video-pipeline --domain finance ...` 生成 `library/semantics/*.finance-signals.json`。
  - artifact 记录 instruments、`viewpoint_events`（主对象）、兼容 recommendations、macro theses、methodology signals、risk flags 和 evidence gaps。
  - video DAG 和 creator DAG 已接入 finance signals 节点。
- [x] 做最近 10 天财经 UP 批量 digest。
  - 输入平台、UP 名称、时间窗口和 limit。
  - [x] `run-creator-pipeline` 已支持 `--published-after/--published-before`，可只分析发布时间落在窗口内的视频。
  - `run-creator-pipeline --domain finance` 会在窗口内批量样本后生成 `library/distilled/*.finance-digest.json`。
  - `seed build-finance-digest --owner ... --signal ...` 可对已有 signals 重建 digest。
  - 当前 digest 输出最近提到的标的、方向、动作、核心理由、风险、重复方法论和证据缺口；价格后验在 `enrich-finance-prices` 做 event-level。
- [x] 接入行情/价格 provider baseline。
  - `seed enrich-finance-prices <digest.json> --ticker-map 标的=ticker` 会生成 `*.finance-digest.priced.json`。
  - 当前 provider 是可选 `stooq` 日线 CSV，记录发布日附近收盘价、最新收盘价、涨跌幅、可选 benchmark 和数据来源 URL。
  - 行情 provider 独立于视频分析；没有显式 ticker mapping 时保持 `missing_ticker`，不猜。
- [x] 增加金融观点前瞻草案报告。
  - `seed build-finance-outlook-report` 从 `*.finance-digest*.json` 生成 `*.finance-outlook-report.html` 与 `*.finance-outlook.json`。
  - 报告输出标的级风险收益、上行/下行空间、利空因素、软件和 AI 行业变量与证据边界。
  - `seed distill-up-list --domain finance` 默认可自动附带生成 outlook（新增可选 `--skip-finance-outlook-reports`）。

- [ ] 增加财经方法论回测/后验评估。
  - 当前 priced digest 已有 event-level 基础价格后验，缺少系统性回测框架。
  - 下一步才做系统性评估：按 action/direction/horizon 计算命中、超额收益、窗口收益，并汇总到 UP 方法论层。
  - 仍然只评估“创作者当时表达的观点是否被后续市场验证”，不输出交易建议。

- [x] 建立“财报 + 研报”结构化技能工作流。
  - 已从 `skills/financial-statement-reviewer` 与 `skills/equity-research-report-analyzer` 形成可复用模板。
  - 已接入 CLI：`extract-equity-research-note`（离线文本到 note）、`extract-equity-research-json`（note 到结构化 ledger）、`build-equity-research-report`（输出可阅读 HTML）。
  - `parse-earnings` 增加 `--review-financial-statement`，可直接生成 `library/distilled/*.financial-statement-review.json`。
  - 产物对齐 `equity-research.json` 的 `viewpoint_events` schema：`claim`、`support_refs`、`evidence_level`、`conviction`、`horizon`、`exit_or_invalidation`、`risk_flags`、`open_questions`。
  - 新增 `first_principles` 字段，补充第一性商业分析结构：商业模式、营收逻辑、竞争格局与护城河、客户依赖、AI 替代风险、海外营收与出海进度、核心不确定性，并新增 `ecosystem_implications`（工具/平台、模型公司含义、算力/硬件信号、相关受益公司、传导不确定性）。对应 HTML 报告新增“第一性原理（商业结构）”下的产业传导启发卡片，用于从美图这类标的提炼对卖铲子与算力链条的参考。
  - 暂不输出 buy/sell 建议；仅输出“成立条件、失效条件、证据边界和不确定性”。
- [x] 做一个美图（MEITU）股价分析样例。
  - 输入：美图 2025 年报/2026Q1 更新 + 行情历史（不依赖单一 provider）。
  - 输出：盈利能力变化、软件板块风险因子、近期价格路径、情景化收益与下行情景、`risk / reward` 框架。
  - 先给“财务/事件证据链完整度”，不是预测价格短线。
  - 已补齐：时间覆盖、同类公司上下文、最新价与基于 priced 事件的上/下行目标草案（非投资建议）、以及风险收益草案展示。


## P9：财经观点事件模型升级

- [x] 把 `finance-signals.json` 从摘要字段升级为观点事件 ledger。
  - 保留现有 `recommendations` 兼容字段，但新增 `viewpoint_events` 作为主对象。
  - 每个 event 至少包含：`event_id`、`video_title`、`published_at`、`instrument`、`ticker`、`asset_class`、`action`、`direction`、`horizon`、`conviction`、`entry_condition`、`exit_or_invalidation`、`risk_flags`、`evidence_refs`、`timestamp_start/end`、`modality_evidence`、`uncertainty`。
  - action taxonomy 参考 VideoConviction：buy、hold、don't buy、sell、short sell，再加 Seed 当前已有 watch/add/reduce/allocate/unknown。
- [x] 增加 recommendation detection 阶段。
  - 先判断视频/片段是否存在明确 recommendation，不存在时只记录 commentary，不进入回测。
  - 避免把一般行情评论、新闻解读、情绪表达误判成交易建议；这是 VideoConviction 明确指出的模型难点。
- [x] 增加 conviction 评估字段。
  - 先用 LLM 基于 transcript、visual notes、timestamp 和风险说明给出 1-3 或 low/medium/high。
  - 之后再补 VL/音频线索：语气、表情、图表展示、仓位/持仓截图、反复强调程度。
- [x] 做 event-level priced outcome。
  - 价格补强从 digest 级移动到 event 级，按 event 的 `published_at` 和 `horizon` 计算 1D/5D/20D/60D/latest。
  - 输出 `event_outcomes`，包含 asset return、benchmark return、relative return、max drawdown、price source、交易日对齐和 ticker mapping 来源。
- [ ] 做 creator-level finance profile。
  - 从多个 event 和 outcome 中总结 UP 的方法论：偏宏观/政策/产业/财报/估值/技术面/情绪面，是否给风险和失效条件，哪些 horizon 更稳定，哪些标的/行业经常误判。
  - 输出可以合入 `creator-profile.md` 的 finance section，也可以先生成 `*.finance-profile.json`。

## P10：新闻检索、facts 蒸馏和财报解析

- [x] 增加通用新闻检索 baseline。
  - 默认 provider 使用 GDELT DOC 2.0 `artlist` JSON，命令为 `seed search-news` 和 `seed research-news`。
  - 检索结果输出 `library/news/*.news-search.json`，保留 query、时间窗口、source URL、标题、来源域名、语言、国家和发布时间。
- [x] 增加 facts-first 新闻蒸馏 skill。
  - 新增 `skills/facts-distiller/SKILL.md` 和 `domain-news-lenses.md`。
  - `seed distill-news-facts` / `seed research-news` 输出 `library/distilled/*.news-digest.json`，结构化 facts、reported claims、industry impacts、market relevance、source gaps 和 open questions。
  - `run-video-pipeline --domain news` 会额外输出 `library/semantics/*.news-facts.json`，并进入 video DAG。
- [x] 增加 SEC 财报解析 baseline。
  - 默认 provider 使用 SEC EDGAR `submissions` 和 XBRL `companyfacts` JSON，ticker/CIK 映射来自 SEC `company_tickers.json`。
  - `seed fetch-earnings` 输出 `library/earnings/*.sec-earnings.json`，保留 CIK、accession、form、filing date、report date、filing index URL 和关键 XBRL 指标。
  - `seed parse-earnings` / `seed distill-earnings` 输出 `library/distilled/*.earnings-digest.json`。
- [x] 增加财报视频 domain。
  - 新增 `skills/earnings-parser/SKILL.md` 和 `domain-earnings-lenses.md`。
  - `run-video-pipeline --domain earnings` 会额外输出 `library/semantics/*.earnings-analysis.json`，把视频里的公司、财报 claim、driver 和 source gap 拆成待 SEC 核验 artifact，并进入 video DAG。
- [x] 补新闻/财报 provider 的缓存与重试。
  - 已增加 `src/seed/http_fetch.py`，为 GDELT/SEC 请求提供 TTL cache、指数退避重试和 source quality 评分；
    `seed search-news`、`seed research-news`、`seed fetch-earnings`、`seed parse-earnings` 已默认接入 `root/.cache/http`。
- [x] 把新闻 facts digest 接入财经事件上下文。
  - `seed enrich-finance-news` 可把一个或多个 `*.news-digest.json` 确定性挂到 `viewpoint_events[].news_context`。
  - 匹配依据是实体、ticker、标的、行业和 fact refs；只引用 facts、source URLs、industry impacts、market relevance、source gaps 和 open questions，不自动生成交易建议。
- [x] 增加财经观点新闻事实 HTML 报告。
  - `seed build-finance-news-report <*.finance-digest.news-context.json>` 输出 `library/reports/*.finance-news-report.html`。
  - 报告按热点概览、UP 观点卡、视频观点事件、新闻 facts 对照、行业影响、source gaps 和 open questions 展示，方便人工快速看每天 UP 观点和事实支撑。
  - `distill-up-list` 会在财经名单配置 `news_digest_paths` 时自动补生成该报告；未配置新闻 digest 时，也会为已有 `*.finance-digest.news-context.json` 重建报告。

## P11：AI 方法论与个人能力账本

- [x] 增加 AI practices domain lens。
  - `--domain ai-practices` 会追加 `domain-ai-practices-lenses.md`，用于 `summarize-transcript`、`analyze-video-semantics`、`aggregate-owner`、`run-video-pipeline` 和 `run-creator-pipeline`。
  - 领域 lens 聚焦“真实 AI 使用流程、时代判断、能力信号、工具模式、个人反补和 Seed 项目反补”，不是 AI 新闻摘要。
- [x] 增加单条视频 AI practice signals artifact。
  - `seed extract-ai-practice-signals <semantics.md>` 或 `seed run-video-pipeline --domain ai-practices ...` 生成 `library/semantics/*.ai-practice-signals.json`。
  - artifact 记录 `practice_events`、`belief_events`、`capability_signals`、`tooling_patterns`、`personal_application_candidates`、`project_application_candidates`、`evidence_gaps` 和 `open_questions`。
  - video DAG 和 creator DAG 已接入 AI practice signals 节点。
- [x] 增加人物/窗口级 AI practice digest。
  - `run-creator-pipeline --domain ai-practices` 会在窗口内批量样本后生成 `library/distilled/*.ai-practice-digest.json`。
  - `seed build-ai-practice-digest --person ... --signal ...` 可对已有 signals 重建 digest。
  - 当前 digest 先做 evidence-grounded ledger：聚合实践事件、观点事件、能力信号、工具模式、个人小实验和 Seed 项目候选。
- [ ] 增加 AI practice 报告和个人 playbook。
  - 下一步可从 digest 生成 `library/reports/*.ai-practice-report.html`、`library/checks/*.personal-ai-playbook.md` 和候选 `library/skills/*/SKILL.md` 草稿。
  - 报告需要展示跨人物共识、冲突、证据强度、可执行实验、失败模式和 Seed 项目影响面。

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
- [x] 创作者样本批量入库：`seed run-creator-batch` 在本地清单基础上支持选择前 N 条、跳过已入库 URL，并复用现有下载适配器。
- [x] 长视频 ASR 分段：`seed transcribe-media` 默认在音频超过 provider 上传限制或默认时长阈值时自动切片、逐片转写、合并 transcript，并记录 `asr_chunks` 元数据。
- [x] Timeline artifact：`seed build-timeline` 生成 `library/timelines/*.timeline.json`，包含 transcript chunk、关键帧、内容结构、广告候选和不确定性。
- [x] 下载可靠性记录：source record 会保存 `download_provider`、`fallback_used` 和 `download_notes`；下载失败时提示平台 cookies 配置。
- [x] DAG 自动发现：`seed build-video-dag --title "..."` 会自动找齐本地 raw、audio、transcript、frames、visual notes、semantics 和 timeline。
- [x] DAG timeline 展示：video DAG 会读取 timeline artifact，并生成 timeline event 子节点；带时间点的事件会接入视频/音频跳转。
- [x] Fact-check claim 节点：`seed extract-claims` 从 `video-semantics.md` 拆出 `library/claims/*.claims.json`，DAG 会展示 claim 子节点，默认状态是 `unverified`。
- [x] DAG 画布体验：`seed serve-video-dag` 提供本地 server 打开 graph；HTML 画布支持节点搜索/过滤、边标签、节点媒体预览、媒体一键开关和右侧详情媒体预览。
- [x] DAG 静态导出：`seed export-video-dag-html` 会把 graph JSON 嵌进 HTML，默认全展开，避免关闭本地 server 后无法查看。
- [x] 视频成本报告：`seed analyze-frames` 会按视频写入 `library/costs/*.cost.json`，记录 Qwen-VL tokens、估算费用、pricing source 和 Codex 预留项；`seed build-video-dag` 会把成本节点接入画布。
- [x] Pipeline 成本账本：`seed build-cost-ledger` 和 `run-video-pipeline` 会写入 `library/costs/*.ledger.json`，汇总 Qwen-VL 并预留 ASR、Codex、搜索/核验费用。
- [x] 创作者预算门槛：`seed run-creator-pipeline --max-estimated-cost ...` 在预算达到后停止后续视频，并把 `budget_exceeded` 写入 manifest。
- [x] Creator profile 证据校验：`seed validate-creator-profile` 和 `aggregate-owner` 会输出 `*.creator-profile.validation.json`。
- [x] Agent 资产生成：`seed generate-agent-assets` 从 creator profile 生成候选 `SKILL.md`、pre-check、post-task reflection checklist 和 review manifest，默认需要人工 review。
- [x] Reflection log：`seed record-reflection` 记录 Agent 使用 creator 方法后的 outcome、worked、failed 和 revise 项。
- [x] Creator profile 最小样本约束：`seed aggregate-owner` 默认要求同一 owner 至少 3 条 video semantics；少量样本必须显式 `--min-videos` 降级。
- [x] Reflection 修订建议：`seed suggest-revisions` 基于 reflection log 生成 revision suggestions 草稿，不自动覆盖原资产。
- [x] 单条视频 pipeline：`seed run-video-pipeline` 串起现有分析步骤并写入 `library/runs/*.video-pipeline.yaml`。
- [x] Pipeline 可观测性：`seed run-video-pipeline` 会显示 Rich step 进度表，并同步写入 `library/runs/*.video-pipeline.status.json`；manifest/status 都记录 step 耗时、artifact paths、cost delta、message、历史 ETA、运行摘要和 step counts。
- [x] Pipeline live DAG：`seed run-video-pipeline` 会同步生成 `library/runs/*.video-pipeline.live.html`，用独立运行态 step graph 展示 pending/running/completed/skipped/failed，不污染最终内容分析 `video-dag.html`。
- [x] 创作者 pipeline 收敛：`seed run-creator-pipeline` 可以按清单批量运行视频 pipeline，并自动串起 creator profile、agent assets 和 creator DAG。
- [x] Creator DAG 第一版：`seed build-creator-dag` 生成 UP/作者级 DAG JSON 和静态 HTML，并可从每条视频展开本地视频、音频、截图和单条 video DAG。
- [x] 真实创作者样本：`影视飓风` 已生成 3 条 video semantics、creator profile、validation、agent asset draft 和 creator DAG。
- [x] 书籍/笔记入口：`seed import-book-note`、`seed analyze-book-note`、`seed distill-book-methods`、`seed build-book-homepage`、`seed build-book-author-profile`、`seed build-book-author-homepage`、`seed aggregate-topic` 支持非视频来源的基础语义、单书主页、作者级聚合和稳定方法论产物。
  - `seed distill-book-methods` 输出 `library/distilled/*.book-methods.json`，把读书笔记拆成 stable principles、decision rules、mental models、agent checks、适用边界、anti-patterns、source gaps 和 open questions。
- [x] Canvas 布局离线化：`tools/vendor/elk.bundled.js` 固定 `elkjs`，导出 HTML 不再依赖 CDN。
- [x] 视频分析 lenses：`skills/video-semantics-analyzer/references/video-analysis-lenses.md` 收敛 Fabric、BiliNote、tldw、短视频结构等参考框架。
- [x] 视频分析证据锚点：prompt 构建统一注入共享 lenses 和 `[T*]`、`[V*]`、`[F*]` 证据引用要求，避免纯主观总结。
- [x] 短视频运动关系候选：`seed build-motion-relations` 和 `run-video-pipeline` 会输出 `library/shots/*.motion-relations.json`，并在 Video DAG 展示 relation candidates。
