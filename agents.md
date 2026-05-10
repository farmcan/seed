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
  -> ingest-url
  -> transcribe-media
  -> extract-frames
  -> analyze-frames
  -> analyze-video-semantics
  -> build-video-dag
  -> aggregate-owner
```

## 重要文件

- CLI：`src/seed/cli.py`
- 创作者视频列表：`src/seed/sources/creator_videos.py`
- Codex 进程封装：`src/seed/agents/codex.py`
- Markdown artifact 工具：`src/seed/markdown.py`
- Video DAG 构建：`src/seed/graphs/video_dag.py`
- 画布 UI：`tools/video-dag-canvas.html`
- Skills：
  - `skills/video-note-summarizer/SKILL.md`
  - `skills/video-semantics-analyzer/SKILL.md`
  - `skills/creator-profile-aggregator/SKILL.md`

## 架构规则

- `cli.py` 只做参数接线、轻量校验和用户输出。
- 平台下载逻辑只放在 `src/seed/sources/`。
- 创作者视频列表发现也属于 `sources/`，输出 `library/notes/*.creator-videos.yaml`，不要直接混入 ASR、视觉分析或总结逻辑。
- 内容分析模块不要直接调用 `codex exec`，统一用 `seed.agents.codex.run_codex_prompt`。
- 不要在多个地方手写 Markdown frontmatter 解析，统一用 `seed.markdown`。
- 本地私有产物都放在 `library/`，默认不要提交。

## 文档规则

- Markdown 尽可能用中文描述。
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
library/transcripts/  ASR 或人工 transcript
library/frames/       抽帧截图
library/notes/        source record、creator video list、visual notes、quick summary
library/semantics/    单条视频语义
library/graphs/       画布 DAG JSON
library/distilled/    creator profile 和方法论
library/skills/       生成的 skills
library/checks/       生成的 checks
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
.venv/bin/seed analyze-video-semantics --help
```

## 已知缺口

- `seed transcribe-media` 还没有内置长视频 ASR 分段。
- timeline artifact 还没有正式生成；当前 DAG 只有 timeline 占位。
- fact-check claim 还没有拆成独立记录。
- `build-video-dag` 仍需要显式传入产物路径。
- HTML 画布是单文件原型，不是完整前端应用。
