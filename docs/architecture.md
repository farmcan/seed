# Architecture

`seed` 的主流程分为七层：

1. Source capture：保存 URL、平台、UP/作者、发布时间、素材路径和元数据。
2. Media language extraction：把视频拆成文字语言和视觉语言，分别生成 transcript 与 visual notes。
3. Video semantics：融合口播、字幕、画面和屏幕文字，形成单条视频的稳定语义资产。
4. Creator aggregation：按 UP/作者聚合多条视频语义，提炼创作者级表达风格、结构模板和方法论。
5. Distillation：从聚合结果中提炼方法论、决策规则、反例和检查问题。
6. Agent assets：输出 `SKILL.md`、checklist 和 prompt context，供 Agent 在任务前后使用。
7. Reflection loop：记录 Agent 使用方法论后的结果，反向修订 skills 和 checks。

```text
URL / book / note
  -> raw asset
  -> transcript + visual notes
  -> video semantics
  -> creator profile
  -> methodology / checks
  -> skill + pre-check + reflection log
```

平台下载适配器只负责采集和记录。内容理解、方法论提炼和 Agent 使用是独立层，避免把平台耦合扩散到整个系统。

## Module Boundaries

- `sources/`：平台采集适配器。只关心 URL、授权、下载、metadata，不做内容理解。
- `asr/` 和 `media.py`：音频抽取和线上 ASR provider。只产出 transcript。
- `vision/`：抽帧、Qwen-VL 调用和 visual notes。只描述画面证据，不负责最终方法论。
- `summarizers/`：单条 transcript 的轻量总结，适合作为人工快速预览。
- `semantics/analyzer.py`：单条视频语义融合，输入 transcript 和 visual notes，输出 `library/semantics/*.video-semantics.md`。
- `semantics/aggregator.py`：按 owner 聚合多条视频语义，输出 `library/distilled/*.creator-profile.md`。
- `agents/codex.py`：统一管理 `codex exec` 命令、dry-run、输出文件写入。内容分析模块不得直接调用 `subprocess` 跑 Codex。
- `markdown.py`：统一读取 Markdown frontmatter、正文和 metadata 字段，避免不同 artifact 各写一套解析逻辑。
- `cli.py`：只做参数接线、轻量校验和用户输出。业务逻辑应留在对应模块。

## Artifact Boundaries

- `library/raw/`：本地私有原始素材。
- `library/transcripts/`：文字语言，来自 ASR 或人工整理。
- `library/frames/`：抽样关键帧。
- `library/notes/*.visual.md`：视觉语言，来自 VL 模型。
- `library/notes/*.summary.md`：快速摘要，不作为长期聚合主数据。
- `library/semantics/*.video-semantics.md`：单条视频语义，是后续聚合的主数据。
- `library/distilled/*.creator-profile.md`：创作者级聚合画像。
- `library/skills/` 和 `library/checks/`：后续 Agent 可加载资产。
