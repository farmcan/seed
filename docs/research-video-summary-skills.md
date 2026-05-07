# 视频总结 Skills 调研

调研日期：2026-05-07。

## 选型结论

第一版采用“自建 Seed skill + 借鉴成熟开源 prompt 结构”的方式，不直接复制某个完整项目。

原因：

- Fabric star 最高、prompt pattern 成熟，但它是通用 AI pattern 框架，不是 Seed 的本地知识库 pipeline。
- Armory 的 `youtube-analysis` 是更接近 Agent skill 的形态，但主要针对 YouTube，Seed 需要 Bilibili、小红书和本地视频都能复用。
- OpenClaw video-summary 的笔记输出对 Obsidian 友好，但依赖外部 transcript API，不适合作为 Seed 核心。
- 直接引入下载/总结一体项目会让平台下载、ASR、总结、存储耦合在一起，不利于后续替换 ASR provider 或总结 Agent。

## 候选项目

| 项目 | Stars | License | 可借鉴点 | 是否直接采用 |
| --- | ---: | --- | --- | --- |
| `danielmiessler/Fabric` | ~41.6k | MIT | `summarize`、`extract_wisdom`、YouTube transcript processing；强调 pattern 化处理。 | 借鉴 prompt 结构，不引入框架。 |
| `Mathews-Tom/armory` | ~225 | MIT | `youtube-analysis` skill：内容类型识别、关键概念、技术术语、takeaways、timestamp-aware 深度分析。 | 借鉴 skill 结构和类型化分析。 |
| `Telhassani/openclaw-skill-video-summary` | 低 | MIT | Summary、Ideas、Insights、Quotes、Habits、Key Points、Takeaways 和 Obsidian 风格输出。 | 借鉴输出章节。 |
| `lifesized/youtube-transcriber` | 低 | AGPL-3.0 | 浏览器/YouTube transcript + LLM 总结工作流。 | 不采用代码；license 不适合混入。 |

## 落地到 Seed

Seed 的 `skills/video-note-summarizer/SKILL.md` 综合了三类结构：

1. Fabric：summary、ideas、insights、quotes、habits、recommendations。
2. Armory：lecture/tutorial/interview/podcast/tech-talk 等类型化分析。
3. OpenClaw：笔记友好的 Markdown 输出和元数据意识。

Seed 增加两个命令：

```bash
seed transcribe-media library/raw/demo.mp4 --title "demo"
seed summarize-transcript library/transcripts/demo.transcript.md --title "demo" --platform bilibili
```

架构边界：

- 下载层：只负责平台视频落盘。
- ASR 层：只负责音频转文字，默认 OpenAI，后续可接 Deepgram/AssemblyAI。
- Transcript 层：只负责本地 markdown artifact。
- Summary 层：只负责启动 Codex subprocess 并写 summary。
- Skill 层：只放总结工作流和输出结构。

## Sources

- Fabric: https://github.com/danielmiessler/Fabric
- Fabric `extract_wisdom`: https://raw.githubusercontent.com/danielmiessler/Fabric/main/data/patterns/extract_wisdom/system.md
- Fabric `summarize`: https://raw.githubusercontent.com/danielmiessler/Fabric/main/data/patterns/summarize/system.md
- Fabric YouTube processing: https://raw.githubusercontent.com/danielmiessler/Fabric/main/docs/YouTube-Processing.md
- Armory: https://github.com/Mathews-Tom/armory
- OpenClaw video summary skill: https://github.com/Telhassani/openclaw-skill-video-summary
- OpenAI Speech to text: https://platform.openai.com/docs/guides/speech-to-text
