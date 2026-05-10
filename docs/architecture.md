# 架构

`seed` 的主流程分为七层：

1. 来源采集：保存 URL、平台、UP/作者、发布时间、素材路径和元数据。
2. 媒体语言抽取：把视频拆成文字语言和视觉语言，分别生成 transcript 与 visual notes。
3. 视频语义分析：融合口播、字幕、画面和屏幕文字，形成单条视频的稳定语义资产。
4. 创作者聚合：按 UP/作者聚合多条视频语义，提炼创作者级表达风格、结构模板和方法论。
5. 方法论蒸馏：从聚合结果中提炼方法论、决策规则、反例和检查问题。
6. Agent 资产：输出 `SKILL.md`、checklist 和 prompt context，供 Agent 在任务前后使用。
7. 反思闭环：记录 Agent 使用方法论后的结果，反向修订 skills 和 checks。

```text
URL / book / note
  -> raw asset
  -> transcript + visual notes
  -> video semantics
  -> video DAG graph
  -> creator profile
  -> methodology / checks
  -> skill + pre-check + reflection log
```

平台下载适配器只负责采集和记录。内容理解、方法论提炼和 Agent 使用是独立层，避免把平台耦合扩散到整个系统。

## 功能模块总览

| 模块 | CLI | 主要代码 | 主要产物 |
| --- | --- | --- | --- |
| 来源采集 | `seed ingest-url` | `src/seed/sources/`, `src/seed/library.py` | `library/raw/*`, `library/notes/*.source.yaml` |
| 创作者视频列表 | `seed fetch-creator-videos` | `src/seed/sources/creator_videos.py`, `src/seed/library.py` | `library/notes/*.creator-videos.yaml` |
| 创作者批量入库 | `seed ingest-creator-videos` | `src/seed/creator_ingest.py`, `src/seed/sources/yt_dlp_adapter.py` | `library/raw/*`, `library/notes/*.source.yaml` |
| ASR 转写 | `seed transcribe-media` | `src/seed/media.py`, `src/seed/asr/`, `src/seed/transcripts.py` | `library/raw/*.asr.mp3`, `library/raw/*.asr.chunks/*`, `library/transcripts/*.transcript.md` |
| 视觉语言 | `seed extract-frames`, `seed analyze-frames` | `src/seed/vision/` | `library/frames/*`, `library/notes/*.visual.md` |
| 快速总结 | `seed summarize-transcript` | `src/seed/summarizers/` | `library/notes/*.summary.md` |
| 视频语义 | `seed analyze-video-semantics` | `src/seed/semantics/analyzer.py` | `library/semantics/*.video-semantics.md` |
| 时间线 | `seed build-timeline` | `src/seed/timeline.py` | `library/timelines/*.timeline.json` |
| 事实核验队列 | `seed extract-claims` | `src/seed/factcheck.py` | `library/claims/*.claims.json` |
| DAG 图谱 | `seed build-video-dag`, `seed serve-video-dag` | `src/seed/graphs/video_dag.py`, `src/seed/dag_server.py`, `tools/video-dag-canvas.html` | `library/graphs/*.video-dag.json` |
| 创作者聚合 | `seed aggregate-owner` | `src/seed/semantics/aggregator.py` | `library/distilled/*.creator-profile.md` |

当前视频 DAG 会展示本地视频、音频、关键帧截图、transcript、visual notes、timeline 占位、semantic 子节点、creator signals、fact-check queue 和 agent assets。选择视频、音频或截图节点时，HTML 画布右侧 inspector 可以直接预览本地素材。

## 模块边界

- `sources/`：平台采集适配器。只关心 URL、授权、下载、metadata，不做内容理解；下载结果需要记录 provider、fallback 和 cookies 相关诊断。
- `sources/creator_videos.py`：按平台和创作者名称发现视频列表。Bilibili 优先复用 `yt-dlp` 的 UP 空间 extractor，并保留 WBI API fallback；小红书先输出搜索候选，后续再替换成稳定登录态 provider。
- `creator_ingest.py`：读取 `*.creator-videos.yaml`，按起始位置和数量选择视频，跳过已入库 URL，并复用现有下载适配器与 source record 写入。
- `asr/` 和 `media.py`：音频抽取、超限音频分片和线上 ASR provider。只产出 transcript；长音频 transcript 会在 frontmatter 记录 `asr_chunks`。
- `vision/`：抽帧、Qwen-VL 调用和 visual notes。只描述画面证据，不负责最终方法论。
- `summarizers/`：单条 transcript 的轻量总结，适合作为人工快速预览。
- `semantics/analyzer.py`：单条视频语义融合，输入 transcript 和 visual notes，输出 `library/semantics/*.video-semantics.md`。
- `timeline.py`：从 transcript chunk、关键帧 manifest、video semantics 和 visual notes 生成确定性 timeline JSON；抽不到时间点时保留 `start_seconds: null`。
- `factcheck.py`：从 video semantics 的 main claims 和 open questions 中拆出待核验 claim，默认状态是 `unverified`。
- `semantics/aggregator.py`：按 owner 聚合多条视频语义，输出 `library/distilled/*.creator-profile.md`。
- `graphs/video_dag.py`：把本地分析产物组装成画布可读 DAG JSON，输出 `library/graphs/*.video-dag.json`；支持按标题自动发现 raw、audio、transcript、frames、visual notes、semantics 和 timeline。
- `dag_server.py`：用本地 HTTP server 打开 DAG HTML 和 graph JSON，避免 `file://` 下浏览器策略影响素材加载。
- `agents/codex.py`：统一管理 `codex exec` 命令、dry-run、输出文件写入。内容分析模块不得直接调用 `subprocess` 跑 Codex。
- `markdown.py`：统一读取 Markdown frontmatter、正文和 metadata 字段，避免不同 artifact 各写一套解析逻辑。
- `cli.py`：只做参数接线、轻量校验和用户输出。业务逻辑应留在对应模块。

## 产物边界

- `library/raw/`：本地私有原始素材。
- `library/raw/*.asr.chunks/`：长音频 ASR 分片，供 provider 逐片转写。
- `library/transcripts/`：文字语言，来自 ASR 或人工整理。
- `library/frames/`：抽样关键帧。
- `library/notes/*.visual.md`：视觉语言，来自 VL 模型。
- `library/notes/*.source.yaml`：单条来源记录，包含原始 URL、下载路径、metadata 路径、下载 provider、fallback 状态和下载诊断。
- `library/notes/*.summary.md`：快速摘要，不作为长期聚合主数据。
- `library/notes/*.creator-videos.yaml`：创作者视频列表，作为后续批量下载、批量分析和 UP 级聚合的入口。
- `library/semantics/*.video-semantics.md`：单条视频语义，是后续聚合的主数据。
- `library/timelines/*.timeline.json`：视频时间线事件，包含 transcript chunk、keyframe、内容结构、广告候选和不确定性。
- `library/claims/*.claims.json`：待核验 claim 队列，状态至少从 `unverified` 开始。
- `library/graphs/*.video-dag.json`：视频分析链路的可视化图谱，可由 `tools/video-dag-canvas.html` 直接展示。
- `library/distilled/*.creator-profile.md`：创作者级聚合画像。
- `library/skills/` 和 `library/checks/`：后续 Agent 可加载资产。
