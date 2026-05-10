# seed

`seed` 是一个个人知识蒸馏仓库，用来把视频、书籍、文章等内容整理成 Agent 可复用的方法论、skills、思考框架和事前检查清单。

当前仓库先建立基础结构：

1. 采集授权内容来源，例如 Bilibili、小红书、书籍笔记或手动转写。
2. 保存原始素材、转写文本和结构化笔记。
3. 为每个 UP、作者或主题生成总结。
4. 抽取可复用的方法论、skill、反思问题和 pre-check 清单。
5. 让后续 Agent 在任务前、任务中、任务后检索这些知识资产。

## 重要边界

下载和分析平台内容时，只处理你拥有权利、获得授权、或平台规则允许保存与分析的内容。仓库默认把 `library/` 里的原始素材、转写、笔记和蒸馏结果都排除在 git 之外，避免把受版权、隐私或平台条款约束的数据误推到 GitHub。

## 目录

```text
configs/              示例配置
docs/                 架构和数据格式说明
src/seed/             Python 包
tests/                基础测试
library/              本地私有知识库，默认不提交内容
  raw/                原始下载或导入素材
  transcripts/        转写文本
  notes/              人工或模型整理笔记
  semantics/          融合口播和视觉语言的视频语义
  distilled/          UP/作者/主题总结
  skills/             Agent 可读取的 skills
  checks/             事前检查清单
```

## 快速开始

```bash
cd seed
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
seed init-library
seed ingest-url "https://www.bilibili.com/video/..." --platform bilibili --owner "some-up" --authorized --no-download
seed ingest-url "https://www.bilibili.com/video/..." --platform bilibili --authorized --download --max-height 360 --max-filesize-mb 100
seed ingest-url "https://www.xiaohongshu.com/explore/..." --platform xiaohongshu --authorized --download --cookies-from-browser chrome
seed transcribe-media library/raw/example.mp4 --title "example" --provider dashscope
seed extract-frames library/raw/example.mp4 --every-seconds 5 --max-frames 12
seed analyze-frames library/frames/example --title "example" --model qwen-vl-max
seed summarize-transcript library/transcripts/example.transcript.md --title "example" --platform bilibili
seed summarize-transcript library/transcripts/example.transcript.md --title "example" --platform bilibili --visual-notes library/notes/example.visual.md
seed analyze-video-semantics library/transcripts/example.transcript.md --title "example" --owner "some-up" --platform bilibili --visual-notes library/notes/example.visual.md
seed aggregate-owner --owner "some-up" --platform bilibili
seed distill-note library/transcripts/example.md --owner "some-up" --topic "增长方法论"
```

`ingest-url` 默认不下载视频，只记录来源。需要下载时显式传入 `--download`，并确保你对内容保存和分析有合法授权。下载文件会进入 `library/raw/`，同名 `.info.json` 保存平台元数据。Bilibili 优先使用 `yt-dlp`；如果网页层被 412 拦截，会回退到公开 playurl API，并用 `ffmpeg` 合成低清晰度 mp4。小红书优先使用 `yt-dlp` 内置的 `XiaoHongShu` extractor；如果公开页面拿不到格式，可以传入新鲜分享链接、`XIAOHONGSHU_COOKIES_FILE`，或显式使用 `--cookies-from-browser`。

ASR 默认使用 DashScope/Qwen，模型为 `qwen3-asr-flash`，需要先配置 `DASHSCOPE_API_KEY` 或 `QWEN_API_KEY`。也可以传 `--provider openai --model gpt-4o-mini-transcribe` 使用 OpenAI。转写前会用 `ffmpeg` 抽取 16 kHz 单声道 MP3，兼容 DashScope 和 OpenAI。`--prompt` 只在需要术语表或上下文偏置时显式传入。需要视觉分析时，先用 `extract-frames` 抽帧，再用 `analyze-frames --model qwen-vl-max` 生成视觉笔记；总结时传入 `--visual-notes` 合并画面信息。总结阶段通过 `codex exec` 非交互进程读取 transcript 和 `skills/video-note-summarizer/SKILL.md`，输出 Markdown 到 `library/notes/`。

视频语义阶段通过 `analyze-video-semantics` 融合口播语言和视觉语言，读取 transcript、visual notes 和 `skills/video-semantics-analyzer/SKILL.md`，输出 Markdown 到 `library/semantics/`。这个文件是后续按 UP 主聚合、抽取爆款结构、沉淀 Agent skills 和 pre-check 的稳定中间层。

UP 主聚合阶段通过 `aggregate-owner` 读取同一 owner 的多个 `library/semantics/*.video-semantics.md`，结合 `skills/creator-profile-aggregator/SKILL.md`，输出创作者画像和可复用方法论到 `library/distilled/`。

本地可视化原型在 `tools/video-dag-canvas.html`，可直接用浏览器打开。它提供无限画布、DAG 节点拖拽、缩放、平移、节点编辑和 JSON 导出，用于展示视频分析链路中的 source、transcript、frames、visual notes、timeline、semantics、creator profile 和 agent assets。

## 未来路线

- 平台适配器：Bilibili、小红书、YouTube、手动导入。
- 转写：Whisper、本地 ASR 或第三方字幕。
- 总结：按 UP/作者、主题、场景、策略进行多层蒸馏。
- Skill 化：输出 Agent 可直接加载的 `SKILL.md`、检查清单和提示模板。
- 反思闭环：记录 Agent 使用某个方法论后的效果，反向修订 skill。
