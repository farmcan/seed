# Agent 指南

任意 AI agent 接手本仓库时，先读这个文件，再看：

- 主架构：`docs/architecture.md`
- 主计划：`docs/todos.md`
- 竞品调研：`docs/research-competitors.md`

## 项目目标

Seed 是本地优先的内容蒸馏系统，用来把授权视频、书籍、笔记和创作者内容转成可复用的方法论、Agent skills、事前检查和复盘资产。

当前主链路：

```text
fetch-creator-videos
  -> ingest-creator-videos
  -> transcribe-media
  -> extract-frames
  -> analyze-frames
  -> analyze-video-semantics
  -> build-video-dag
  -> aggregate-owner
```

下一阶段主入口要收敛成：

```text
run-video-pipeline
  -> video semantics + timeline + claims + cost ledger + video DAG HTML

run-creator-pipeline
  -> 多条 video pipeline + budget gate + creator profile + creator DAG + agent assets
```

## 重要文件

- CLI：`src/seed/cli.py`
- 创作者视频列表：`src/seed/sources/creator_videos.py`
- 创作者批量入库：`src/seed/creator_ingest.py`
- 视频 pipeline：`src/seed/pipeline.py`
- 创作者 pipeline：`src/seed/creator_pipeline.py`
- ASR 分段转写：`src/seed/asr/chunked.py`
- 成本计量：`src/seed/costs.py`
- Creator profile 证据校验：`src/seed/semantics/validation.py`
- Claim verification：`src/seed/claim_verification.py`
- 书籍/笔记：`src/seed/books.py`
- Timeline artifact：`src/seed/timeline.py`
- Fact-check claim：`src/seed/factcheck.py`
- Agent 资产生成：`src/seed/agent_assets.py`
- Reflection log：`src/seed/reflections.py`
- Codex 进程封装：`src/seed/agents/codex.py`
- Markdown artifact 工具：`src/seed/markdown.py`
- 共享分析 lens 入口：`src/seed/skill_refs.py`
- 视频证据锚点：`src/seed/semantics/evidence.py`
- Video DAG 构建：`src/seed/graphs/video_dag.py`
- Creator DAG 构建：`src/seed/graphs/creator_dag.py`
- DAG 本地服务：`src/seed/dag_server.py`
- DAG 静态导出：`src/seed/dag_export.py`
- 画布 UI：`tools/video-dag-canvas.html`
- 画布布局库：`tools/vendor/elk.bundled.js`
- Skills：
  - `skills/video-note-summarizer/SKILL.md`
  - `skills/video-semantics-analyzer/SKILL.md`
  - `skills/video-semantics-analyzer/references/video-analysis-lenses.md`
  - `skills/creator-profile-aggregator/SKILL.md`

## 架构规则

- `cli.py` 只做参数接线、轻量校验和用户输出。
- 新增主要功能必须能归入 `run-video-pipeline`、`run-creator-pipeline` 或明确的 artifact 消费链路；不要新增只能手动调用、无法被 pipeline 编排的孤立命令。
- `run-creator-pipeline` 是创作者级默认入口，必须把 video pipeline、creator cost ledger、creator profile、agent assets 和 creator DAG 串到同一个 manifest；后处理状态写入 `creator_steps`。
- 新增主要功能必须写稳定 artifact 到 `library/`，不要只打印到 stdout。
- 新增 artifact 必须说明谁生产、谁消费、是否进入 DAG、是否需要计费；这些信息要同步更新 `docs/architecture.md` 和 `docs/todos.md`。
- pipeline step 必须幂等：目标产物已存在时要能跳过或覆盖明确可控，失败后要能从中间步骤续跑。
- 长任务必须记录 run manifest，至少包含 step、status、input、output、provider/model、started_at、finished_at、error。
- 平台下载逻辑只放在 `src/seed/sources/`。
- 下载相关 source record 必须保留 `download_provider`、`fallback_used` 和 `download_notes`，方便定位 cookies、风控和 fallback 问题。
- 创作者视频列表发现也属于 `sources/`，输出 `library/notes/*.creator-videos.yaml`，不要直接混入 ASR、视觉分析或总结逻辑；Bilibili 用户名搜索被风控时优先尝试 `--owner-id <mid>`。
- 创作者批量入库从 `*.creator-videos.yaml` 读取 URL，复用 `download_url` 和 `save_source_record`，不要复制单链接下载逻辑；已有 source record 但没有本地 `raw_path` 时不能跳过下载。
- ASR 长音频分段在 `seed.asr.chunked`，不要在 CLI 或 provider 里重复实现切片与合并；线上 ASR provider 可能同时限制文件大小和音频时长，默认长于 300 秒要切片。
- 短视频结构分析在 `seed.shorts`，不要把 shot detection 写进 timeline 或 visual notes；`run-video-pipeline` 会生成 short profile，并仅在 `is_short_form` 为 true 时生成 shots artifact。
- shot detection 当前默认是 `ffmpeg-scene` baseline；后续接 PySceneDetect、TransNetV2 时必须做成 provider，不要把重依赖放进默认路径。
- 短视频 frame evidence 必须结构化记录字幕、OCR、蒙版、画中画、贴纸、滤镜、变速、镜头运动、人物运动关系、转场和剪辑目的；默认可以是 pending 字段，但不要退化成一段不可追溯的自然语言。
- OCR、人姿态、运动估计和视觉效果检测都应是可选 provider：优先参考 PaddleOCR/RapidVideOCR、MediaPipe/OpenPose/YOLO pose、OpenCV optical flow；默认安装路径不要强制引入这些重依赖。
- Qwen-VL 成本记录在 `seed.costs`，`analyze-frames` 必须按单条视频写入 `library/costs/*.cost.json`；`run-video-pipeline` 和 `build-cost-ledger` 必须写入 `library/costs/*.ledger.json`；费用是基于 token usage 和配置单价的估算，实际账单以服务商后台为准。
- 创作者批量任务支持 `--max-estimated-cost` 预算门槛；达到预算后停止后续视频，并在 run manifest 写入 `budget_exceeded`。
- 任何外部模型/API 调用都要考虑成本记录；如果 provider 暂时拿不到 token，就写 `reserved` 或 `unknown`，不要伪造 token 或金额。
- Timeline 生成在 `seed.timeline`，只做确定性抽取；无法定位具体时间时使用 `start_seconds: null`，不要伪造时间点。
- Fact-check claim 抽取在 `seed.factcheck`，默认状态是 `unverified`；不要在没有外部证据时改成 verified。
- Claim verification 必须保留来源 URL、访问日期、证据摘要、分阶段 artifact 和不确定性；不允许只有模型判断，没有外部证据时必须保持 `unverified`。
- 从 creator profile 生成的 `library/skills/` 和 `library/checks/` 都是 draft，必须通过 `review-agent-assets` 更新 review manifest 后再安装或长期使用。
- Reflection log 只追加记录；`suggest-revisions` 只生成修订建议草稿，不直接覆盖 creator profile、skills 或 checks。
- `aggregate-owner` 默认至少 3 条 video semantics；如果用 `--min-videos 1` 或 `2`，输出只能视为 provisional。
- Video DAG 构建支持按标题自动发现本地产物；显式传入的路径优先，resolver 逻辑在 `seed.graphs.video_dag.resolve_video_dag_artifacts`。短视频的 short profile 和 shots artifact 也应进入 resolver 和 DAG。
- DAG 画布调试优先用 `seed serve-video-dag <graph.json>` 打开；需要给用户直接查看时，用 `seed export-video-dag-html <graph.json>` 生成静态 HTML。
- DAG timeline event 如果有 `start_seconds`，应通过 `media_anchor` 连接本地视频/音频；不要只把时间点写成普通文本。
- DOM/ELK 画布使用 vendored `elkjs` layered layout 做自动分层布局；手写布局只能作为本地脚本加载失败的 fallback。画布必须保留卡片式信息密度和媒体详情能力，不能降级成低信息密度图谱。
- DAG HTML 默认必须保留节点媒体预览；顶部 `媒体` 按钮用于一键隐藏或恢复节点媒体。默认仍保持简版、卡片正文折叠、右侧详情关闭。
- Creator DAG 默认是 UP/作者级聚合入口，不应把所有媒体一次性铺满；每条视频节点通过折叠子节点挂载单条 video DAG、本地视频、本地音频和关键帧 gallery。
- 给用户看的 DAG 默认优先生成静态 HTML；本地 server 只用于调试。
- 视频分析 skills 必须复用 `video-analysis-lenses.md`，不要在 summarizer、semantics analyzer 和 creator aggregator 里各写一套互相冲突的分析框架。
- 视频总结、视频语义和创作者聚合 prompt 必须注入共享 lenses；单条视频 prompt 还必须注入 `[T*]`、`[V*]`、`[F*]` 证据锚点。
- 视频语义和 creator profile 的强结论必须带证据引用；如果证据不足，写入 Open Questions 或 Evidence Gaps，不要用模型猜测补齐。
- `aggregate-owner` 生成 creator profile 后要写 evidence validation report；手动检查已有 profile 时使用 `seed validate-creator-profile`。
- 内容分析模块不要直接调用 `codex exec`，统一用 `seed.agents.codex.run_codex_prompt`。
- 不要在多个地方手写 Markdown frontmatter 解析，统一用 `seed.markdown`。
- 本地私有产物都放在 `library/`，默认不要提交。
- 真实样本状态：2026-05-11 已用 `影视飓风` 3 条 Bilibili 视频跑通 creator profile、validation、agent asset draft 和 creator DAG；2026-05-12 已补跑 Qwen-VL visual notes 并重建单条视频与创作者级产物。注意视觉证据是 12 帧抽样，不等于逐帧完整分析。

## Lint 规则

- 文档 lint：Markdown 尽可能中文；代码、变量、函数、注释和 commit message 用英文。
- 文档 lint：除非 `tests/test_docs_structure.py` 同步允许，不要新增 `docs/*.md`；优先更新 `docs/architecture.md`、`docs/todos.md`、`docs/research-competitors.md` 和 `agents.md`。
- 功能 lint：新增功能必须更新 `docs/todos.md` 的状态，长期存在的功能必须更新 `docs/architecture.md`。
- Artifact lint：新增 `library/<dir>` 必须更新 `.gitignore`、`.gitkeep`、`src/seed/library.py`、`docs/architecture.md` 和本文件。
- Pipeline lint：新增视频处理能力必须说明它在 pipeline 中的位置，不能只提供单步 demo。
- Source lint：平台发现失败要保留 provider、错误码和 cookies/owner-id 建议；不要吞掉 352/412 这类风控诊断。
- Cost lint：新增外部模型/API/provider 调用必须记录或预留成本字段，并接入 cost ledger；批量 pipeline 必须考虑预算门槛。
- DAG lint：新增关键 artifact 必须考虑是否需要 DAG 节点；如果节点能回到视频/音频证据，必须写入 `media_anchor` 或说明缺少时间点的原因。
- Verification lint：涉及事实、价格、平台规则、模型价格、库选型等易变信息时，必须查官方或 primary source，并把来源写入调研或 artifact。
- Canvas lint：不要再手写主布局算法；主路径使用 vendored 成熟布局库，手写逻辑只允许作为 fallback 或小交互 glue。遇到卡顿先做默认简版、卡片正文折叠、视口裁剪和右侧详情收起，不要降级成低信息密度图谱。
- Skill lint：新增视频分析 prompt/skill 之前，先检查 `video-analysis-lenses.md` 是否能扩展；优先更新共享 lens，避免重复造轮子。
- Evidence lint：新增或改动内容分析 prompt 时，必须保留证据锚点注入；不要输出无法追溯到 transcript、visual notes、timeline 或 keyframe 的强判断。
- Vendor lint：新增 vendored 前端库必须固定版本，并提交对应 LICENSE 或来源说明。
- Privacy lint：不要提交 `library/` 的私有内容，除 `.gitkeep` 外都应被 ignore。
- Review lint：从 LLM 生成的 creator skill/check 默认是 draft，不能自动视为可安装或可信资产。
- Test lint：测试优先覆盖 pipeline、DAG/export、artifact schema、docs/skill lint 等主链路；避免为简单 path helper、薄 wrapper、常量映射和第三方库直通逻辑堆大量低价值单元测试。

## 文档规则

- Markdown 尽可能用中文描述。
- 只要新增或改变主要功能，必须同步更新主入口文档：
  - 已实现并需要长期说明的功能，更新 `docs/architecture.md`。
  - 已实现但还有后续工作或限制的功能，更新 `docs/todos.md`。
  - 依赖竞品、开源库或外部服务取舍的功能，更新 `docs/research-competitors.md`。
- 除非有明确长期价值，不要新增文档；优先更新：
  - `docs/architecture.md`
  - `docs/todos.md`
  - `docs/research-competitors.md`
  - `agents.md`
- 如果确实要新增 docs 文件，必须同步更新文档 lint 测试。
- 已完成的一次性 implementation plan 不要长期保留在 docs 里。

## 代码规则

- 所有代码、变量名、函数名和代码注释使用英文。
- 测试代码也遵守英文命名。
- 面向用户的 CLI 输出可以是英文；如需中文文案，优先放在 Markdown/skill 文档里。
- 不要把私有 `library/` 内容写进测试 fixture 或 git。
- Git commit message 使用英文，保持简短动作式描述，例如 `Consolidate project docs`。

## 本地产物目录

```text
library/raw/          原始视频、音频、metadata
library/raw/*.chunks/ ASR 分片音频
library/shorts/       短视频 profile JSON
library/shots/        shot boundary JSON
library/transcripts/  ASR 或人工 transcript
library/frames/       抽帧截图和 shot 代表帧
library/notes/        source record、creator video list、visual notes、quick summary
library/runs/         pipeline run manifest，待实现
library/semantics/    单条视频语义
library/timelines/    视频时间线 JSON
library/claims/       待核验 claim JSON
library/costs/        单条视频 Qwen-VL 成本 JSON 和 pipeline cost ledger
library/graphs/       画布 DAG JSON 和静态 HTML 快照
library/distilled/    creator profile 和方法论
library/skills/       生成的 skills
library/checks/       生成的 checks
library/reflections/  Agent 使用方法论后的复盘记录
```

## 验证命令

完成代码改动前至少运行：

```bash
.venv/bin/ruff check .
.venv/bin/pytest
git status -sb
```

当前测试集刻意保持偏 smoke/integration，不追求每个 helper 都有单测。新增测试时优先问：它能防止主 pipeline、artifact、DAG 或文档约束退化吗？

常用 CLI 检查：

```bash
.venv/bin/seed --help
.venv/bin/seed run-video-pipeline --help
.venv/bin/seed profile-short-video --help
.venv/bin/seed detect-shots --help
.venv/bin/seed fetch-creator-videos --help
.venv/bin/seed ingest-creator-videos --help
.venv/bin/seed run-creator-pipeline --help
.venv/bin/seed build-cost-ledger --help
.venv/bin/seed build-video-dag --help
.venv/bin/seed build-creator-dag --help
.venv/bin/seed serve-video-dag --help
.venv/bin/seed export-video-dag-html --help
.venv/bin/seed verify-claims --help
.venv/bin/seed import-book-note --help
.venv/bin/seed analyze-book-note --help
.venv/bin/seed aggregate-topic --help
.venv/bin/seed generate-agent-assets --help
.venv/bin/seed review-agent-assets --help
.venv/bin/seed record-reflection --help
.venv/bin/seed suggest-revisions --help
.venv/bin/seed analyze-video-semantics --help
.venv/bin/seed validate-creator-profile --help
```

## 已知缺口

- Creator profile 证据校验目前是 warning report，还没有阻断生成或自动修复。
- HTML 画布是单文件原型，不是完整前端应用；复杂交互继续先保持单文件，但主布局必须继续依赖成熟布局库。
- Bilibili UP 空间列表仍可能触发 352/412 风控；`--owner-id` 只能绕过用户名搜索，不能替代 cookies 或登录态。
