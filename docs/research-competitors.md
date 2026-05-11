# 竞品与类似项目调研

调研日期：2026-05-07；画布与计费补充：2026-05-10；架构复核补充：2026-05-11。

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
| `tldraw/tldraw` | 高 star infinite canvas SDK，支持自定义 shape、工具、binding、协作和 DOM canvas。 | 如果单文件 HTML 原型变成正式前端，可以用它承载自由画布和富媒体节点。 |
| tldraw workflow starter kit | 官方 workflow starter kit 演示节点、连接、port binding、图执行和数据流。 | 可参考它的节点/边数据模型，但当前不直接引入 React 前端。 |
| `xyflow/react` / React Flow | Node-based UI 生态成熟，官方示例覆盖 auto layout、expand/collapse、minimap 和 controls。 | 如果后续要做“可折叠分析 DAG + 自动布局 + 节点编辑器”，React Flow 是迁移首选。 |
| `kieler/elkjs` | ELK 的 JavaScript 布局引擎，适合有方向的 node-link diagram 和 layered layout。 | 可作为 DAG 自动布局算法，不负责画布 UI；适合替换当前手写列布局。 |
| `jagenjo/litegraph.js` | 老牌 HTML5 Canvas2D graph node editor，偏蓝图/工作流。 | 可参考紧凑节点和 JSON graph 思路；富媒体 DOM 节点不如 React Flow/tldraw 直接。 |
| Prefect | Python-native workflow orchestration，强调 state tracking、failure handling、retry 和本地/云端运行。 | 后续 pipeline 复杂到需要调度、重试 UI 和 worker 时再考虑；当前先用本地 run manifest，避免过早引入服务。 |
| Dagster | 面向 data assets 的 orchestrator，强调 lineage、observability、declarative model 和 testability。 | 如果 `library/` 产物变成大量数据资产和跨主题依赖，可以参考 asset model；当前项目还不到引入 Dagster 的复杂度。 |
| Temporal Python SDK | durable workflow 平台，有 Python SDK，适合长时间运行、可靠重试和分布式任务。 | 如果后续视频批处理需要强一致重试、队列和 worker，再评估；本地 MVP 暂不需要。 |
| Fabric `youtube_summary` pattern | transcript-first 视频总结 pattern，强调通读 transcript、识别主题、提取关键时间点、按视频进程组织 Markdown。 | Seed 的 video semantics 不应直接复制 prompt，但应吸收 timestamp-first、structure-first 和 extract-wisdom 的分析 lenses。 |
| HoverNotes / Obsidian 视频笔记类产品 | 强调本地 Markdown、截图、timestamp、视觉内容和学习笔记联动。 | 支持 Seed 继续把 keyframe/screenshot/timeline 作为一等证据，而不是只保存 transcript 摘要。 |

## 关键洞察

1. 单条视频总结已经是红海。差异化要放在“长期知识资产”和“Agent 可执行方法论”。
2. 下载适配器是易碎层。它应该是插件，不应该污染核心数据模型。
3. 小红书生态的非官方工具多，但稳定性和合规风险高。MVP 应先支持手动导入、URL 记录、截图/文案复制，再做下载适配器。
4. Bilibili 可先用 yt-dlp 跑通，但要支持 cookies、字幕、弹幕、分 P、合集和 UP 空间批处理。
5. 真正有价值的总结不是“这条视频说了什么”，而是“这个创作者反复依赖什么判断模型、内容结构、表达套路、决策规则和禁忌”。
6. 视频分析画布是共性问题，短期最稳是继续保留单文件 HTML：简版/展开、媒体预览和 DAG JSON 仍在本地完成，但布局不要手写，应使用 `elkjs` layered layout，并 vendor 固定版本以保证静态 HTML 离线可打开。中期如果交互复杂度继续上升，应迁移到 React Flow + ELK；如果更像白板和自由资料编排，再考虑 tldraw。
7. Qwen-VL 计费需要作为 artifact，而不是只在日志里打印。按单条视频记录 token usage、单价、pricing source、估算金额，并允许环境变量覆盖单价，避免价格变化导致历史结果不可解释。
8. Pipeline 编排先不要引入重型服务。Prefect/Dagster/Temporal 都能解决状态、重试和可观测性，但当前 seed 主要是本地单人工作流；先用 `library/runs/*.yaml` 记录 step 状态，等出现定时调度、多 worker、复杂重试或团队协作再迁移。
9. 视频分析 skills 需要一个共享 lens 层。Fabric、BiliNote、tldw 和 HoverNotes 的共同点不是某个固定 prompt，而是 transcript、timestamp、screenshot/keyframe、source-grounded analysis 和 reusable method extraction。Seed 应把这些作为 `video-analysis-lenses.md`，让 summarizer、semantics analyzer 和 creator aggregator 复用同一套词汇。
10. 不要直接抄单个视频总结 prompt。Fabric 的 pattern 化适合拆成可复用 lens；BiliNote 类工具提醒我们截图、时间戳和 Markdown 必须对齐；tldw/NotebookLM 类工具强调来源 grounding。Seed 的落地方式是 prompt 构建时注入共享 lenses 和证据锚点，让输出天然带 `[T*]`、`[V*]`、`[F*]` 引用。

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
- tldraw: https://github.com/tldraw/tldraw
- tldraw workflow starter kit: https://tldraw.dev/starter-kits/workflow
- React Flow auto layout: https://reactflow.dev/examples/layout/auto-layout
- elkjs: https://github.com/kieler/elkjs
- litegraph.js: https://github.com/jagenjo/litegraph.js
- ELK layout options: https://eclipse.dev/elk/reference/options.html
- 阿里云百炼模型价格： https://www.alibabacloud.com/help/zh/model-studio/model-pricing
- Prefect docs: https://docs.prefect.io/
- Dagster docs: https://docs.dagster.io/
- Temporal Python SDK: https://python.temporal.io/
- Fabric youtube_summary pattern: https://fabric.gavinslater.co.uk/view/youtube_summary
- HoverNotes: https://hovernotes.io/
