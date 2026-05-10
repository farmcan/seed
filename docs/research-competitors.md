# 竞品与类似项目调研

调研日期：2026-05-07。

## 结论

`seed` 不应该只做“视频总结器”。现有产品已经把单条视频总结做得足够轻，真正有差异化的方向是：长期追踪一个 UP/作者/主题，把多条内容压缩成可复用的方法论、Agent skill、pre-check 和反思日志。

## 产品竞品

| 产品 | 主要能力 | 可借鉴点 | seed 的差异化 |
| --- | --- | --- | --- |
| BibiGPT | 支持 Bilibili、YouTube、本地文件、播客等音视频总结和对话；其 v1 开源仓库描述也提到小红书、抖音、快手等来源。 | 中文视频生态覆盖广，单链接总结路径成熟。 | 不止做单条总结，要做“跨视频/跨作者的方法论沉淀”。 |
| BiliNote | 开源 AI 视频笔记，支持 Bilibili、YouTube、抖音、本地视频，输出 Markdown 笔记、时间戳、截图。 | “视频 -> 转写 -> 结构化 Markdown”的产品形态很接近 MVP。 | 可先借鉴笔记结构，但下游输出面向 Agent skill，而不是只给人看。 |
| NotebookLM | 支持上传/引用资料、YouTube transcript、音频文件，并围绕来源做摘要、提问和 Audio Overview。 | 强调 grounded sources 和资料内引用，适合学习型知识库。 | seed 需要本地可控、可版本化、可供 Agent 自动调用。 |
| Recall | 面向网页、YouTube、播客、PDF 等内容总结、知识库、问答，并强调 spaced repetition 和 active recall。 | “总结后还要记住和复习”的闭环值得借鉴。 | seed 可以把复习变成 Agent 使用后的反思和方法论更新。 |
| Readwise Reader / Ghostreader | 对文章、PDF、YouTube 等资料做 AI 总结、自定义 prompt 和阅读辅助。 | 自定义 prompt 是强需求，适合沉淀不同总结模板。 | seed 需要把 prompt 模板升级成可触发的 Agent skills。 |
| Glasp / Eightify / summarize.tech | 轻量 YouTube 总结、转写、时间戳摘要。 | 入口简单，适合“粘贴 URL -> 立即得到摘要”。 | 这些产品偏消费工具，缺少长期方法论建模。 |

## 开源项目与组件

| 项目 | 现状 | 对 seed 的用途 |
| --- | --- | --- |
| `yt-dlp/yt-dlp` | GitHub 上约 160k stars，支持大量站点；官方支持列表包含 Bilibili、Bilibili Space Video 等。 | Bilibili/YouTube 下载和元数据抽取优先用它。 |
| `JoeanAmier/XHS-Downloader` | GitHub 上约 11k stars，专注小红书链接提取、作品采集和下载，GPL-3.0。 | 小红书适配器候选，但应作为可选外部工具隔离。 |
| `yt-dlp` Bilibili Space extractor | 支持 `https://space.bilibili.com/<mid>/video` 形式的 UP 空间列表，但实际请求可能触发登录或 412 风控。 | `fetch-creator-videos` 先复用它；失败时 fallback 到 Bilibili WBI API，并提示 cookies。 |
| SocialSisterYi Bilibili API collect | 维护 Bilibili Web API 和 WBI 签名说明，包含用户投稿接口 `/x/space/wbi/arc/search`。 | Bilibili UP 视频列表 fallback 使用它的接口形态和签名算法。 |
| `xiaohongshu-cli` / `xhs-mcp` 类项目 | 小红书搜索、用户主页、笔记详情通常依赖浏览器 cookie、A1 cookie、QR 登录或逆向 API。 | 暂不把登录态逆向实现写死到核心；先输出搜索候选，后续替换成独立 provider。 |
| `openai/whisper` | GitHub 上约 99k stars，开源多语言 ASR。 | 本地转写基线。 |
| `SYSTRAN/faster-whisper` | GitHub 上约 22k stars，用 CTranslate2 重新实现 Whisper。 | 更快的本地转写候选，适合批量处理视频。 |
| `JefferyHcool/BiliNote` | GitHub 上约 5.9k stars，MIT。 | 参考视频笔记工作流、Markdown 输出和截图/时间戳设计。 |
| `JimmyLv/BibiGPT-v1` | GitHub 上约 6k stars，GPL-3.0。 | 参考多平台总结产品体验，避免直接混用 GPL 代码。 |
| `danielmiessler/Fabric` | GitHub 上约 41k stars，MIT，核心是可复用 AI prompt patterns。 | seed 的 skill/prompt 层可以借鉴 pattern 化设计。 |
| `microsoft/graphrag` | GitHub 上约 33k stars，MIT。 | 后期做跨作者、跨主题的全局总结和关系图谱时参考。 |
| `rmusser01/tldw_server` | 自称 open-source NotebookLM，支持视频、音频、PDF、文档、转写、RAG 和多 LLM。 | 参考“媒体分析 + 私有研究助手”的完整形态。 |

## 关键洞察

1. 单条视频总结已经是红海。差异化要放在“长期知识资产”和“Agent 可执行方法论”。
2. 下载适配器是易碎层。它应该是插件，不应该污染核心数据模型。
3. 小红书生态的非官方工具多，但稳定性和合规风险高。MVP 应先支持手动导入、URL 记录、截图/文案复制，再做下载适配器。
4. Bilibili 可先用 yt-dlp 跑通，但要支持 cookies、字幕、弹幕、分 P、合集和 UP 空间批处理。
5. 真正有价值的总结不是“这条视频说了什么”，而是“这个创作者反复依赖什么判断模型、内容结构、表达套路、决策规则和禁忌”。

## Sources

- BibiGPT v1: https://github.com/JimmyLv/BibiGPT-v1
- BiliNote: https://github.com/JefferyHcool/BiliNote
- NotebookLM YouTube/audio sources: https://blog.google/technology/ai/notebooklm-audio-video-sources/
- NotebookLM source help: https://support.google.com/notebooklm/answer/16215270
- Recall docs: https://docs.getrecall.ai/
- Readwise Ghostreader: https://docs.readwise.io/reader/guides/ghostreader/overview
- Glasp YouTube Summary: https://glasp.co/youtube-summary
- summarize.tech: https://www.summarize.tech/
- yt-dlp supported sites: https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md
- XHS-Downloader: https://github.com/JoeanAmier/XHS-Downloader
- yt-dlp Bilibili Space issue: https://github.com/yt-dlp/yt-dlp/issues/12007
- Bilibili WBI 签名说明: https://socialsisteryi.github.io/bilibili-API-collect/docs/misc/sign/wbi.html
- Bilibili 用户投稿接口: https://socialsisteryi.github.io/bilibili-API-collect/docs/user/space.html
- xiaohongshu-cli: https://pypi.org/project/xiaohongshu-cli/
- xhs-mcp-fy: https://pypi.org/project/xhs-mcp-fy/
- Whisper: https://github.com/openai/whisper
- faster-whisper: https://github.com/SYSTRAN/faster-whisper
- Fabric: https://github.com/danielmiessler/Fabric
- GraphRAG: https://github.com/microsoft/graphrag
- tldw server: https://github.com/rmusser01/tldw_server
