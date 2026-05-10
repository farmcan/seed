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
  -> video semantics + timeline + claims + cost + video DAG HTML

run-creator-pipeline
  -> 多条 video pipeline + creator profile + creator DAG + agent assets
```

## 重要文件

- CLI：`src/seed/cli.py`
- 创作者视频列表：`src/seed/sources/creator_videos.py`
- 创作者批量入库：`src/seed/creator_ingest.py`
- ASR 分段转写：`src/seed/asr/chunked.py`
- 成本计量：`src/seed/costs.py`
- Timeline artifact：`src/seed/timeline.py`
- Fact-check claim：`src/seed/factcheck.py`
- Agent 资产生成：`src/seed/agent_assets.py`
- Reflection log：`src/seed/reflections.py`
- Codex 进程封装：`src/seed/agents/codex.py`
- Markdown artifact 工具：`src/seed/markdown.py`
- Video DAG 构建：`src/seed/graphs/video_dag.py`
- DAG 本地服务：`src/seed/dag_server.py`
- DAG 静态导出：`src/seed/dag_export.py`
- 画布 UI：`tools/video-dag-canvas.html`
- Skills：
  - `skills/video-note-summarizer/SKILL.md`
  - `skills/video-semantics-analyzer/SKILL.md`
  - `skills/creator-profile-aggregator/SKILL.md`

## 架构规则

- `cli.py` 只做参数接线、轻量校验和用户输出。
- 新增主要功能必须能归入 `run-video-pipeline`、`run-creator-pipeline` 或明确的 artifact 消费链路；不要新增只能手动调用、无法被 pipeline 编排的孤立命令。
- 新增主要功能必须写稳定 artifact 到 `library/`，不要只打印到 stdout。
- 新增 artifact 必须说明谁生产、谁消费、是否进入 DAG、是否需要计费；这些信息要同步更新 `docs/architecture.md` 和 `docs/todos.md`。
- pipeline step 必须幂等：目标产物已存在时要能跳过或覆盖明确可控，失败后要能从中间步骤续跑。
- 长任务必须记录 run manifest，至少包含 step、status、input、output、provider/model、started_at、finished_at、error。
- 平台下载逻辑只放在 `src/seed/sources/`。
- 下载相关 source record 必须保留 `download_provider`、`fallback_used` 和 `download_notes`，方便定位 cookies、风控和 fallback 问题。
- 创作者视频列表发现也属于 `sources/`，输出 `library/notes/*.creator-videos.yaml`，不要直接混入 ASR、视觉分析或总结逻辑。
- 创作者批量入库从 `*.creator-videos.yaml` 读取 URL，复用 `download_url` 和 `save_source_record`，不要复制单链接下载逻辑。
- ASR 长音频分段在 `seed.asr.chunked`，不要在 CLI 或 provider 里重复实现切片与合并。
- Qwen-VL 成本记录在 `seed.costs`，`analyze-frames` 必须按单条视频写入 `library/costs/*.cost.json`；费用是基于 token usage 和配置单价的估算，实际账单以服务商后台为准。
- 任何外部模型/API 调用都要考虑成本记录；如果 provider 暂时拿不到 token，就写 `reserved` 或 `unknown`，不要伪造 token 或金额。
- Timeline 生成在 `seed.timeline`，只做确定性抽取；无法定位具体时间时使用 `start_seconds: null`，不要伪造时间点。
- Fact-check claim 抽取在 `seed.factcheck`，默认状态是 `unverified`；不要在没有外部证据时改成 verified。
- Claim verification 必须保留来源 URL、访问日期、证据摘要和不确定性；不允许只有模型判断。
- 从 creator profile 生成的 `library/skills/` 和 `library/checks/` 都是 draft，必须人工 review 后再安装或长期使用。
- Reflection log 只追加记录；`suggest-revisions` 只生成修订建议草稿，不直接覆盖 creator profile、skills 或 checks。
- `aggregate-owner` 默认至少 3 条 video semantics；如果用 `--min-videos 1` 或 `2`，输出只能视为 provisional。
- Video DAG 构建支持按标题自动发现本地产物；显式传入的路径优先，resolver 逻辑在 `seed.graphs.video_dag.resolve_video_dag_artifacts`。
- DAG 画布调试优先用 `seed serve-video-dag <graph.json>` 打开；需要给用户直接查看时，用 `seed export-video-dag-html <graph.json>` 生成静态 HTML。
- HTML 画布使用 `elkjs` layered layout 做自动分层布局；手写布局只能作为 CDN 加载失败的 fallback。画布内置搜索过滤、边标签、简版/全展开、节点展开和节点卡片内媒体预览，不要再新增独立可视化入口。
- 给用户看的 DAG 默认优先生成静态 HTML；本地 server 只用于调试。
- 内容分析模块不要直接调用 `codex exec`，统一用 `seed.agents.codex.run_codex_prompt`。
- 不要在多个地方手写 Markdown frontmatter 解析，统一用 `seed.markdown`。
- 本地私有产物都放在 `library/`，默认不要提交。

## Lint 规则

- 文档 lint：Markdown 尽可能中文；代码、变量、函数、注释和 commit message 用英文。
- 文档 lint：除非 `tests/test_docs_structure.py` 同步允许，不要新增 `docs/*.md`；优先更新 `docs/architecture.md`、`docs/todos.md`、`docs/research-competitors.md` 和 `agents.md`。
- 功能 lint：新增功能必须更新 `docs/todos.md` 的状态，长期存在的功能必须更新 `docs/architecture.md`。
- Artifact lint：新增 `library/<dir>` 必须更新 `.gitignore`、`.gitkeep`、`src/seed/library.py`、`docs/architecture.md` 和本文件。
- Pipeline lint：新增视频处理能力必须说明它在 pipeline 中的位置，不能只提供单步 demo。
- Cost lint：新增外部模型/API/provider 调用必须记录或预留成本字段。
- DAG lint：新增关键 artifact 必须考虑是否需要 DAG 节点；如果不接入 DAG，要在实现说明中解释原因。
- Verification lint：涉及事实、价格、平台规则、模型价格、库选型等易变信息时，必须查官方或 primary source，并把来源写入调研或 artifact。
- Canvas lint：不要再手写主布局算法；主路径使用成熟布局库，手写逻辑只允许作为 fallback 或小交互 glue。
- Privacy lint：不要提交 `library/` 的私有内容，除 `.gitkeep` 外都应被 ignore。
- Review lint：从 LLM 生成的 creator skill/check 默认是 draft，不能自动视为可安装或可信资产。

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
library/transcripts/  ASR 或人工 transcript
library/frames/       抽帧截图
library/notes/        source record、creator video list、visual notes、quick summary
library/runs/         pipeline run manifest，待实现
library/semantics/    单条视频语义
library/timelines/    视频时间线 JSON
library/claims/       待核验 claim JSON
library/costs/        单条视频 Qwen-VL 成本 JSON
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

常用 CLI 检查：

```bash
.venv/bin/seed --help
.venv/bin/seed build-video-dag --help
.venv/bin/seed serve-video-dag --help
.venv/bin/seed export-video-dag-html --help
.venv/bin/seed generate-agent-assets --help
.venv/bin/seed record-reflection --help
.venv/bin/seed suggest-revisions --help
.venv/bin/seed analyze-video-semantics --help
```

## 已知缺口

- claim 状态还没有外部核验流程，目前只支持默认 `unverified`。
- 还没有 `run-video-pipeline` 和 run manifest，端到端处理仍需要手动串命令。
- 还没有 `run-creator-pipeline` 和 creator DAG，UP 主级总览仍不完整。
- 非视频来源还没有接入 semantics 和聚合流程。
- `build-video-dag` 可以按标题自动发现常见产物，但跨视频聚合后的复杂画布还没有自动生成。
- HTML 画布是单文件原型，不是完整前端应用；复杂交互继续先保持单文件，但主布局必须继续依赖成熟布局库。
