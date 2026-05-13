# 竞品与类似项目调研

调研日期：2026-05-07；画布与计费补充：2026-05-10；架构复核补充：2026-05-11；视觉笔记、核验、编排补充：2026-05-11；短视频 shot 级分析补充：2026-05-12；运行可观测性补充：2026-05-13。

## 结论

`seed` 不应该只做“视频总结器”。现有产品已经把单条视频总结做得足够轻，真正有差异化的方向是：长期追踪一个 UP/作者/主题，把多条内容压缩成可复用的方法论、Agent skill、pre-check 和反思日志。

## 产品竞品

| 产品 | 主要能力 | 可借鉴点 | seed 的差异化 |
| --- | --- | --- | --- |
| BibiGPT | 支持 Bilibili、YouTube、本地文件、播客等音视频总结和对话；其 v1 开源仓库描述也提到小红书、抖音、快手等来源。 | 中文视频生态覆盖广，单链接总结路径成熟。 | 不止做单条总结，要做“跨视频/跨作者的方法论沉淀”。 |
| BiliNote | 开源 AI 视频笔记，支持 Bilibili、YouTube、抖音、本地视频，输出 Markdown 笔记、时间戳、截图。 | “视频 -> 转写 -> 结构化 Markdown”的产品形态很接近 MVP。 | 可先借鉴笔记结构，但下游输出面向 Agent skill，而不是只给人看。 |
| NotebookLM | 支持上传/引用资料、YouTube transcript、音频文件，并围绕来源做摘要、提问和 Audio Overview；官方帮助说明 YouTube URL 只导入文字 transcript，不导入画面。 | 强调 grounded sources 和资料内引用，适合学习型知识库；但它的 YouTube 输入更偏文字源。 | seed 的差异化应继续保留本地视频、关键帧、视觉 notes 和 DAG，而不是只做 transcript 知识库。 |
| Recall | 面向网页、YouTube、播客、PDF 等内容总结、知识库、问答，并强调 spaced repetition 和 active recall。 | “总结后还要记住和复习”的闭环值得借鉴。 | seed 可以把复习变成 Agent 使用后的反思和方法论更新。 |
| Readwise Reader / Ghostreader | 对文章、PDF、YouTube 等资料做 AI 总结、自定义 prompt 和阅读辅助；Reader 支持视频旁边展示 time-synced transcript、点击片段跳转、highlight 和 enhanced transcript。 | 视频学习体验的关键不是“摘要按钮”，而是视频、转写、笔记、高亮和当前位置同步。 | seed 的 DAG/HTML 后续可以借鉴这种“媒体预览 + 当前证据片段 + 可回放”的交互。 |
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
| `rmusser01/tldw_server` | 自称 open-source NotebookLM，支持视频、音频、PDF、文档、转写、RAG 和多 LLM；README 显示它是 API-first，提供 media add/search、OpenAI-compatible chat、RAG、Audio STT、VLM backends 等接口。 | 参考“媒体分析 + 私有研究助手”的完整形态；Seed 短期不需要服务端化，但可以学习它把 ingestion、search、chat、STT、VLM 分成独立接口。 |
| `tldraw/tldraw` | 高 star infinite canvas SDK，支持自定义 shape、工具、binding、协作和 DOM canvas。 | 如果单文件 HTML 原型变成正式前端，可以用它承载自由画布和富媒体节点。 |
| tldraw workflow starter kit | 官方 workflow starter kit 演示节点、连接、port binding、图执行和数据流。 | 可参考它的节点/边数据模型，但当前不直接引入 React 前端。 |
| `xyflow/react` / React Flow | Node-based UI 生态成熟，官方 auto layout 示例支持在 dagre、d3-hierarchy 和 elk 之间切换；expand/collapse 生态也成熟。 | 如果后续要做“可折叠分析 DAG + 自动布局 + 节点编辑器”，React Flow 是迁移首选；当前单文件 HTML 只保留为本地快照和原型。 |
| `kieler/elkjs` | ELK 的 JavaScript 布局引擎，选项丰富，适合有方向的 node-link diagram、layered layout、边标签和复杂间距控制。 | 当前继续作为 DAG 自动布局主算法；不要回到手写布局。 |
| `jagenjo/litegraph.js` | 老牌 HTML5 Canvas2D graph node editor，偏蓝图/工作流。 | 可参考紧凑节点和 JSON graph 思路；富媒体 DOM 节点不如 React Flow/tldraw 直接。 |
| `Breakthrough/PySceneDetect` | GitHub 上约 4.8k stars，BSD-3-Clause；Python/OpenCV shot/scene cut detection 库，支持内容阈值、fade 等检测方式。 | 60s 内短视频先用它做本地、低依赖 shot boundary baseline，输出 shot artifact；适合快速落地和可解释调参。 |
| `soCzech/TransNetV2` | GitHub 上约 0.9k stars，MIT；深度学习 shot boundary detection，README 给出多数据集 F1 对比。 | 作为可选高质量 shot detector provider；比纯阈值法更适合快速剪辑和复杂转场，但模型依赖更重。 |
| `wentaozhu/AutoShot` | GitHub 上约 0.2k stars，MIT；CVPRW 2023 短视频 shot boundary dataset/方法，论文指出短视频有更密集、垂直化和复杂转场特征。 | 证明短视频不能完全复用长视频抽帧策略；后续可参考其短视频 dataset 视角设计评测指标。 |
| VCapsBench / ShotBench 等视频理解 benchmark | 近年 benchmark 开始把 camera movement、shot type、cinematic language、fine-grained caption quality 作为评估维度。 | Seed 的短视频 visual notes 应从“描述画面”升级为“shot 类型、镜头运动、主体、字幕、构图、剪辑目的、叙事功能”。 |
| `PaddlePaddle/PaddleOCR` | GitHub 上约 77k stars，Apache-2.0；支持 100+ 语言 OCR 和文档/图像结构化。 | 短视频字幕/OCR provider 首选候选；先作为可选依赖接入，不放入默认安装，避免环境复杂度影响主链路。 |
| `SWHL/RapidVideOCR` / `timminator/VideOCR` | 分别约 0.5k / 0.6k stars；都聚焦从视频硬字幕中提取文字，RapidVideOCR 偏 CLI，VideOCR 支持 GUI 和多语言。 | 证明“硬字幕抽取”应作为短视频一等证据，不应只依赖 ASR；可以参考其抽帧、OCR、合并相邻字幕为 SRT 的流程。 |
| `google-ai-edge/mediapipe` | GitHub 上约 35k stars，Apache-2.0；面向 live/streaming media 的跨平台 ML pipeline，常用于 pose、hand、face 等实时视觉任务。 | 人物运动关系 provider 候选：人的位置、姿态、手势、遮挡、人物与镜头/物体关系可以先用 pose/hand/face landmarks 辅助，再交给 VL 总结。 |
| `CMU-Perceptual-Computing-Lab/openpose` | GitHub 上约 34k stars；实时多人 body/face/hand/foot keypoint detection。 | 适合后续做多人关系和肢体动作的更强 provider，但 license 和安装复杂度需要单独隔离。 |
| `opencv/opencv` | GitHub 上约 87k stars，Apache-2.0；提供 optical flow、tracking、image processing 等基础视觉算法。 | 当前短视频默认 provider 应优先用 OpenCV/ffmpeg 做低成本 baseline，例如镜头运动、画面变化、字幕区域、运动强度，不依赖大模型。 |
| Prefect | Python-native workflow orchestration；官方 docs 强调 task state lifecycle、client-side orchestration、`.submit()` 并发和 `.delay()` worker 分发。 | 后续 pipeline 复杂到需要调度、重试 UI 和 worker 时再考虑；当前先把本地 run manifest 做扎实。 |
| Dagster | 面向 data assets 的 orchestrator，强调 integrated lineage、observability、declarative model 和 testability。 | 如果 `library/` 产物变成大量数据资产和跨主题依赖，可以参考 asset model；当前项目还不到引入 Dagster 的复杂度。 |
| Temporal Python SDK | durable workflow 平台，有 Python SDK，适合长时间运行、可靠重试和分布式任务。 | 如果后续视频批处理需要强一致重试、队列和 worker，再评估；本地 MVP 暂不需要。 |
| Airflow UI | 官方 UI 提供 Grid、Graph、Calendar、Task Duration、Gantt、Code 等视图，并能查看 task instance 详情和日志。 | 证明运行态可观测性至少需要 step 状态、耗时、日志、依赖图和失败定位；Seed 不需要引入 Airflow，但可以借鉴它的多视图拆分。 |
| Prefect UI / states | Prefect 的核心是 flow/task state lifecycle、task run、logs 和 orchestration 视图，Python 代码可通过 `.submit()` 并发执行 task。 | Seed 可先学习“状态机 + logs + duration + retry 信息”模型；暂时保留本地 manifest，不引入 server。 |
| Dagster UI | Dagster 强调 asset lineage、run observability、logs、materialization 和图谱视图。 | 对 Seed 的启发是把 `library/` 产物视为 asset，运行中节点应显示输入/输出 artifact，而不只是“任务名”。 |
| Temporal Web UI | Temporal Web 用 workflow execution history 和 event timeline 调试长任务。 | 如果未来需要可恢复长任务和可靠重试，可以参考 event history；当前先用 append-only step events 或 status JSON。 |
| LangGraph Studio | 面向 agent graph 的可视化调试工具，支持在图上调试、观察 node 执行和状态。 | 对 Seed 的 live DAG 有直接参考意义：画布节点可以表达 pending/running/completed/failed，但最终仍要落到 artifact 和 run manifest。 |
| React Flow / XYFlow 状态节点 | React Flow 官方示例和文档支持动态更新 nodes/edges、自定义节点、layout 和交互。 | 如果 live DAG 变成正式前端，React Flow + ELK 是首选；当前单文件 HTML 可以先用轮询 status JSON 做轻量状态刷新。 |
| Server-Sent Events / EventSource | 浏览器原生 EventSource 适合服务端向页面推送单向事件流。 | 本地 live preview 可以先轮询 JSON；如果需要更顺滑的运行中动画和日志流，再加 SSE，不必一开始引入 WebSocket。 |
| Rich Progress / Live | Python Rich 提供 Progress、Live table、spinner 和 console status，适合 CLI 长任务可视化。 | Seed 的第一步应是 CLI 进度条和 step table，因为它实现成本最低，也不依赖浏览器打开。 |
| ClaimCheck / RAG fact-checking 研究 | 近年的 automated fact-checking 研究普遍拆成 claim decomposition、query planning、evidence retrieval、evidence synthesis、verdict prediction。 | `verify-claims` 不应只是“搜到来源就 unclear”；下一步应实现分阶段 artifact：query plan、evidence snippets、source quality、verdict 和 residual uncertainty。 |
| Fabric `youtube_summary` pattern | transcript-first 视频总结 pattern，强调通读 transcript、识别主题、提取关键时间点、按视频进程组织 Markdown。 | Seed 的 video semantics 不应直接复制 prompt，但应吸收 timestamp-first、structure-first 和 extract-wisdom 的分析 lenses。 |
| HoverNotes / Obsidian 视频笔记类产品 | 强调本地 Markdown、截图、timestamp、视觉内容和学习笔记联动。 | 支持 Seed 继续把 keyframe/screenshot/timeline 作为一等证据，而不是只保存 transcript 摘要。 |

## 关键洞察

1. 单条视频总结已经是红海。差异化要放在“长期知识资产”和“Agent 可执行方法论”。
2. 下载适配器是易碎层。它应该是插件，不应该污染核心数据模型。
3. 小红书生态的非官方工具多，但稳定性和合规风险高。MVP 应先支持手动导入、URL 记录、截图/文案复制，再做下载适配器。
4. Bilibili 可先用 yt-dlp 跑通，但要支持 owner mid、cookies、字幕、弹幕、分 P、合集和 UP 空间批处理。实测 `--owner-id` 能绕过用户名搜索失败，但不能绕过所有 UP 空间 352/412 风控。
5. 真正有价值的总结不是“这条视频说了什么”，而是“这个创作者反复依赖什么判断模型、内容结构、表达套路、决策规则和禁忌”。
6. 视频分析画布是共性问题，短期最稳是继续保留单文件 HTML：简版/展开、媒体预览和 DAG JSON 仍在本地完成，但布局不要手写，应使用 `elkjs` layered layout，并 vendor 固定版本以保证静态 HTML 离线可打开。中期如果交互复杂度继续上升，应迁移到 React Flow + ELK；如果更像白板和自由资料编排，再考虑 tldraw。
7. Qwen-VL 计费需要作为 artifact，而不是只在日志里打印。按单条视频记录 token usage、单价、pricing source、估算金额，并允许环境变量覆盖单价，避免价格变化导致历史结果不可解释。
8. Pipeline 编排先不要引入重型服务。Prefect/Dagster/Temporal 都能解决状态、重试和可观测性，但当前 seed 主要是本地单人工作流；先用 `library/runs/*.yaml` 记录 step 状态，等出现定时调度、多 worker、复杂重试或团队协作再迁移。
9. 视频分析 skills 需要一个共享 lens 层。Fabric、BiliNote、tldw 和 HoverNotes 的共同点不是某个固定 prompt，而是 transcript、timestamp、screenshot/keyframe、source-grounded analysis 和 reusable method extraction。Seed 应把这些作为 `video-analysis-lenses.md`，让 summarizer、semantics analyzer 和 creator aggregator 复用同一套词汇。
10. 不要直接抄单个视频总结 prompt。Fabric 的 pattern 化适合拆成可复用 lens；BiliNote 类工具提醒我们截图、时间戳和 Markdown 必须对齐；tldw/NotebookLM 类工具强调来源 grounding。Seed 的落地方式是 prompt 构建时注入共享 lenses 和证据锚点，让输出天然带 `[T*]`、`[V*]`、`[F*]` 引用。
11. NotebookLM 官方帮助明确 YouTube 来源只导入 transcript，网页 URL 也不导入图片和嵌入视频。这反而说明 Seed 的关键差异化是“视觉语言也作为一等证据”，尤其是教程、产品演示、剪辑结构和屏幕文字。
12. 视频学习体验应该借鉴 Readwise Reader 的同步 transcript：画布节点可以继续显示媒体，但下一步更有价值的是让 transcript chunk、keyframe、timeline event 和视频播放位置互相跳转。
13. Fact-check 应按研究里的分阶段流程做，而不是一次 prompt 给 verdict。最小实现顺序：claim -> search queries -> evidence snippets -> source score -> verdict -> uncertainty；所有中间产物进 `library/claims/` 或 run manifest。
14. Orchestration 暂不引入 Prefect/Dagster/Temporal。Prefect 最接近 Seed 的 Python step runner，但当前痛点不是缺框架，而是 cost ledger、budget gate、resume semantics 和 evidence validation 还没做完整。
15. 阿里云百炼价格在 2026-04-01 官方页显示不同部署区价格差异明显：International 下 `qwen-vl-max` 为 $0.8/$3.2 per 1M input/output tokens，Global 下 `qwen-vl-max` 为 $0.23/$0.574 per 1M input/output tokens。Seed 成本 artifact 必须记录 deployment/region 或 pricing source snapshot，不能只记 model 名。
16. DAG 卡顿时不能牺牲视觉表达直接降级成低信息密度图谱。后续仍应保留卡片式画布视觉，通过默认简版、视口裁剪、按需媒体加载和更成熟的 canvas SDK 解决性能。
17. 真实 UP 样本比单条 demo 更容易暴露架构问题。本轮 `影视飓风` 三条样本暴露了两个必须保留的工程规则：source-only 记录不能阻止后续下载；线上 ASR 不能只按文件大小判断是否分段，还要按音频时长分段。
18. 60s 以内短视频应该走独立强分析链路，不应只是长视频 pipeline 的 `--max-frames` 调大。关键区别是：逐秒/逐帧成本可控、shot 密度高、前三秒 hook 决定理解入口、字幕/OCR 常常比口播更短促，且剪辑技巧本身就是语义。
19. 短视频强分析的推荐 artifact 顺序：`short-video-profile.json` 判断时长/竖屏/帧率 -> `shots/*.shots.json` 记录 shot boundary、shot duration、transition type -> `frames/*.frame-notes.jsonl` 逐帧或抽样逐帧 VL/OCR -> `short-video-semantics.md` 聚合 hook、beat、shot function、视觉语言、剪辑技巧和可复用模板 -> DAG 展示 shot strip 和 frame evidence。
20. 短视频方法论可先采用“Hook -> Setup/Context -> Proof/Development -> Turn/Reframe -> Payoff/Loop/CTA”的 beat lens，但必须用 transcript、OCR、shot timing、frame evidence 支撑；不要把营销文章里的爆款公式当成无证据结论。
21. 视觉效果和剪辑手法需要被结构化，不应只写进自然语言总结。短视频 frame evidence 至少要预留：字幕、OCR、蒙版、画中画、贴纸、滤镜/LUT、变速、文字覆盖、镜头运动、人物运动关系、转场类型、声音卡点和剪辑目的。
22. Provider 设计要分层：默认 deterministic baseline 只做 ffprobe/ffmpeg/OpenCV 级别信息；OCR provider 用 PaddleOCR/RapidVideOCR 类工具；human-motion provider 用 MediaPipe/OpenPose/YOLO pose；cinematic taxonomy 参考 ShotBench/CineTechBench，但最终结论仍由 VL/LLM 基于 evidence 汇总。
23. 运行过程可观测性应先补数据模型，再补动画。Airflow、Prefect、Dagster、Temporal、LangGraph Studio 的共同点是先记录状态、事件、日志、耗时、依赖和产物，再提供图或时间线视图。Seed 不应先做漂亮动画，而应先让 `run-video-pipeline` 持续写 status artifact。
24. 对 Seed 最轻量的 live DAG 方案是：每个 step 开始/结束时更新 `library/runs/*.status.json`，CLI 用 Rich 展示 step table，HTML 画布轮询这个 JSON 并把节点显示为 pending/running/completed/skipped/failed。动画只做运行中 pulse 和未完成节点虚化，不引入重型前端或编排服务。
25. 预计耗时可以先用历史 run manifest 估算：同类平台、视频时长、是否 vision、frame 数、ASR 分片数和模型 provider 作为粗粒度特征。不要一开始承诺精确 ETA；先显示每步已耗时和历史均值区间。

## Sources

- BibiGPT v1: https://github.com/JimmyLv/BibiGPT-v1
- BiliNote: https://github.com/JefferyHcool/BiliNote
- NotebookLM YouTube/audio sources: https://blog.google/technology/ai/notebooklm-audio-video-sources/
- NotebookLM source help: https://support.google.com/notebooklm/answer/16215270
- Recall docs: https://docs.getrecall.ai/
- Readwise Ghostreader: https://docs.readwise.io/reader/guides/ghostreader/overview
- Readwise YouTube videos: https://docs.readwise.io/reader/docs/faqs/videos
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
- Prefect tasks docs: https://docs.prefect.io/v3/concepts/tasks
- Dagster docs: https://docs.dagster.io/
- Temporal docs: https://docs.temporal.io/
- Temporal Python SDK: https://python.temporal.io/
- Airflow UI docs: https://airflow.apache.org/docs/apache-airflow/stable/ui.html
- Prefect states: https://docs.prefect.io/v3/concepts/states
- Prefect tasks: https://docs.prefect.io/v3/concepts/tasks
- Dagster UI: https://docs.dagster.io/guides/operate/webserver
- Temporal Web UI: https://docs.temporal.io/web-ui
- LangGraph Studio: https://docs.langchain.com/langgraph-platform/langgraph-studio
- React Flow updating nodes: https://reactflow.dev/learn/advanced-use/state-management
- MDN EventSource: https://developer.mozilla.org/en-US/docs/Web/API/EventSource
- Rich Progress: https://rich.readthedocs.io/en/stable/progress.html
- ClaimCheck paper: https://arxiv.org/abs/2510.01226
- Evidence-backed fact checking with RAG: https://arxiv.org/abs/2408.12060
- Fabric youtube_summary pattern: https://fabric.gavinslater.co.uk/view/youtube_summary
- HoverNotes: https://hovernotes.io/
- PySceneDetect: https://www.scenedetect.com/
- PySceneDetect GitHub: https://github.com/Breakthrough/PySceneDetect
- TransNetV2: https://github.com/soCzech/TransNetV2
- AutoShot: https://arxiv.org/abs/2304.06116
- AutoShot GitHub: https://github.com/wentaozhu/AutoShot
- VCapsBench: https://arxiv.org/abs/2505.23484
- ShotBench: https://arxiv.org/abs/2506.21356
- CineTechBench: https://arxiv.org/abs/2505.15145
- PaddleOCR: https://github.com/PaddlePaddle/PaddleOCR
- RapidVideOCR: https://github.com/SWHL/RapidVideOCR
- VideOCR: https://github.com/timminator/VideOCR
- MediaPipe: https://github.com/google-ai-edge/mediapipe
- OpenPose: https://github.com/CMU-Perceptual-Computing-Lab/openpose
- OpenCV: https://github.com/opencv/opencv
