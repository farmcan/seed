# 竞品与类似项目调研

调研日期：2026-05-07；画布与计费补充：2026-05-10；架构复核补充：2026-05-11；视觉笔记、核验、编排补充：2026-05-11；短视频 shot 级分析补充：2026-05-12；运行可观测性补充：2026-05-13；财经 UP 蒸馏补充：2026-05-14；新闻检索与财报解析补充：2026-05-17；AI 方法论与 agent 工作流补充：2026-05-18；书籍/读书方法论补充：2026-05-18；微信读书接入补充：2026-05-18。

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
| AlphaCheck | 面向金融 YouTube，提取股票提及、推荐强度、上下文理由，并把发布时价格和最新价格对齐；还支持按频道追踪历史表现。 | 财经方向要把“标的、动作、信念强度、理由、发布时间价格、后验表现”结构化，不要停留在自然语言摘要。 | Seed 先做多平台本地蒸馏和 evidence DAG；后验收益、benchmark 和行情数据作为财经 domain 后续 provider。 |

## 开源项目与组件

| 项目 | 现状 | 对 seed 的用途 |
| --- | --- | --- |
| `JoeanAmier/XHS-Downloader` | GitHub 上约 11k stars，专注小红书链接提取、作品采集和下载，GPL-3.0。 | 小红书适配器候选，但应作为可选外部工具隔离。 |
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
| `OpenWeRead` / 微信读书技能生态 | 社区实现以微信读书官方 skill（`weread-skills`）能力为基础，核心路径是书架、metadata 与笔记/划线。 | 书籍源接入优先走官方授权链路，保留非官方兜底，但不让其主导主流水线，先确保 `book-source` 落库稳定。 |
| `google-ai-edge/mediapipe` | GitHub 上约 35k stars，Apache-2.0；面向 live/streaming media 的跨平台 ML pipeline，常用于 pose、hand、face 等实时视觉任务。 | 人物运动关系 provider 候选：人的位置、姿态、手势、遮挡、人物与镜头/物体关系可以先用 pose/hand/face landmarks 辅助，再交给 VL 总结。 |
| `CMU-Perceptual-Computing-Lab/openpose` | GitHub 上约 34k stars；实时多人 body/face/hand/foot keypoint detection。 | 适合后续做多人关系和肢体动作的更强 provider，但 license 和安装复杂度需要单独隔离。 |
| `opencv/opencv` | GitHub 上约 87k stars，Apache-2.0；提供 optical flow、tracking、image processing 等基础视觉算法。 | 当前短视频默认 provider 应优先用 OpenCV/ffmpeg 做低成本 baseline，例如镜头运动、画面变化、字幕区域、运动强度，不依赖大模型。 |
| `gtfintechlab/VideoConviction` | KDD 2025 项目，研究 YouTube finfluencer 的多模态股票推荐；包含 YouTube data pipeline、annotation pipeline、prompting 和 backtesting。 | 财经 UP 分析应显式抽取 ticker/标的、action、conviction、reasoning 和多模态表达；同时要警惕模型把一般评论误判成明确推荐。 |
| AlphaCheck / fintuber 类频道追踪工具 | 产品形态是“单条视频抽取股票信号 -> 按频道汇总历史 picks -> 对齐价格/benchmark”。 | 证明“最近 10 天 top UP 说了什么”需要先做稳定频道采集和行情对齐；没有完整样本时不能靠搜索结果猜推荐。 |
| TickerReceipts | 公开站点展示 YouTube stock picks，按频道、ticker、日期、price at mention、current price 和 return 组织。 | Seed 的财经 digest 应该继续向 time-stamped event feed 演进，而不是只有 UP 画像摘要。 |
| FinCap / finfluencer short-video caption 研究 | 面向金融短视频 caption，强调文本、音频和视觉模态组合。 | 适合补强财经短视频：ASR 只能覆盖口播，图表、字幕、持仓截图和语气也应进入 conviction 与 evidence。 |
| `AI4Finance-Foundation/FinGPT` | 开源金融大模型项目，覆盖金融情绪、关系抽取、NER、问答、forecaster 等任务。 | 适合作为财经文本任务的参考 taxonomy：sentiment、relation extraction、headline classification、NER、QA；Seed 暂不直接引入模型。 |
| `AI4Finance-Foundation/FinRobot` | 金融 AI Agent 平台，组合 LLM、金融数据源、量化分析和报告生成；示例包含 FMP、SEC、yfinance 等数据源和 equity report pipeline。 | 后续财经 domain 可以把外部行情、财报、公告和估值工具作为 provider，和视频观点分离。 |
| `ProsusAI/finBERT` | 金融文本情绪分析 BERT，面向金融语料情绪分类。 | 可作为低成本 sentiment/stance baseline 的参考，但财经视频 recommendation 不能只看情绪，还要抽取 action、horizon、risk。 |
| `AI4Finance-Foundation/FinRL` | 金融强化学习框架，强调 market environment、agent、application 和 train-test-trade。 | 方法论蒸馏时可借鉴“状态 -> 行动 -> 风险约束 -> 回测”的表达；UP 观点不是可执行策略，必须保留适用条件和失效条件。 |
| Anthropic Building Effective Agents | Anthropic 工程文章总结 agent/workflow 落地经验，强调组合式 workflow、透明控制流、工具使用、评估和人机协作边界。 | AI practices domain 不应只总结观点，而要抽取真实 workflow、工具链、验证方法、失败模式和 guardrails。 |
| OpenAI Codex 文档与安全实践 | Codex 被定位为能读写代码、运行命令并在工作区内执行任务的 coding agent；OpenAI 的安全实践强调 workspace 控制、日志、权限和 review。 | Seed 的 AI 方法论账本要记录“如何委派 agent、如何 review、如何限制权限、如何验收结果”，并把这些反补到 agent skill/check。 |
| Simon Willison Using LLMs 系列 | 长期记录 LLM 在编程、数据处理、研究、工具构建和日常工作中的真实用法与失败经验。 | 适合作为“人物方法论”样本：记录具体 task、prompt/spec、工具组合、验证方式和可复用经验，而不是只摘录抽象观点。 |
| Stooq daily CSV / pandas-datareader StooqDailyReader | Stooq 提供历史行情 CSV 下载，pandas-datareader 也内置 StooqDailyReader，底层使用 `https://stooq.com/q/d/l/`。 | 适合做轻量行情后验 baseline；Seed 先要求显式 ticker mapping，避免把视频里的中文标的名猜成错误代码。 |
| GDELT DOC 2.0 API | 官方文档说明 DOC API 支持全文新闻搜索、跨语言机器翻译覆盖、`artlist` 文章列表、JSON 输出和 timeline/tone/source country 等模式。 | 新闻检索 baseline 不自建爬虫，先用 GDELT `mode=artlist&format=json` 拉取候选来源，再由 facts distiller 拆 facts、reported claims、source gaps 和行业影响机制。 |
| SEC EDGAR data APIs | SEC 官方文档说明 `data.sec.gov` 提供无需 API key 的 JSON API，包括 company submissions 和 XBRL companyfacts，更新随 filings disseminated。 | 财报解析 baseline 使用官方 `submissions/CIK##########.json` 和 `api/xbrl/companyfacts/CIK##########.json`，保留 CIK、accession、form、period、unit 和 filing URL。 |
| SEC ticker/CIK mapping files | SEC “Accessing EDGAR Data” 页面列出 `company_tickers.json` 和 `company_tickers_exchange.json`，用于 ticker、CIK 和 company name association。 | `parse-earnings <ticker>` 先通过 SEC mapping 解析 CIK；没有可靠映射时失败，不猜。 |
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
| NotebookLM source guide / source chat | 官方帮助强调 Source Guide 的整源摘要、对特定主题提问，以及多 source 场景下通过点名 source 缩小检索范围。 | 读书能力应保持 source-grounded：每个方法论结论都要回到书籍/笔记 evidence block，而不是直接输出“书的智慧”。 |
| LlamaIndex response synthesizers | 官方文档内置 `refine`、`compact`、`tree_summarize` 等 response modes；`refine` 会按 chunk 顺序逐步更新答案，`tree_summarize` 适合分层合成。 | 长书/多本书不要一次塞进 prompt；Seed 应拆成 evidence blocks、chapter/section methods、book methods、topic profile 的层级合成。 |
| LangChain map-reduce/refine summarization | LangChain 文档与示例长期把 summarization 拆成 `stuff`、`map_reduce`、`refine` 等 combine documents 模式。 | 读书蒸馏可借鉴 map -> reduce：先对 block/chapter 抽原则和规则，再合并去重、保留冲突和适用边界。 |
| Readwise / Reader API | Readwise API 支持 highlights export，保留 book/article metadata、highlight、note、location、tags、updated cursor 和分页。 | 未来读书 ingestion 不应只收一篇 Markdown；应设计 `book-source` artifact，兼容 Readwise/Kindle/Koreader/手动 Markdown highlights。 |
| Zotero Web API / annotations | Zotero Web API 提供在线 library 的 read-only access；Zotero 生态强调 PDF annotations、notes、collections 和 tags。 | 学术/研究类书籍应兼容 Zotero annotations：保留 item key、collection、annotation text、note、page/location 和 citation metadata。 |
| Zettelkasten / evergreen notes 实践 | Obsidian/Zettelkasten 社区强调 literature notes、permanent notes、atomic notes、links 和长期复用。 | Seed 的 `book_methods` 不应停在摘要；应输出可复用的 principle/rule/check/hook，并能和 UP、新闻 facts、财报 facts 互相引用。 |

## 关键洞察

1. 单条视频总结已经是红海。差异化要放在“长期知识资产”和“Agent 可执行方法论”。
2. 下载适配器是易碎层。它应该是插件，不应该污染核心数据模型。
3. 小红书生态的非官方工具多，但稳定性和合规风险高。MVP 应先支持手动导入、URL 记录、截图/文案复制，再做下载适配器。
4. 下载适配器是易碎层，适合保持可替换；线上抓取能力应作为可选插件，不替代离线清单驱动的主流程。
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
26. 财经 UP 方向要作为 domain lens，而不是复制一套视频 pipeline。通用层仍负责采集、ASR、视觉、semantics、creator profile 和 DAG；财经层只补充 instruments、recommendations、macro theses、methodology signals、risk flags、evidence gaps 和后验行情 provider。
27. VideoConviction 的关键启发是：多模态输入能帮助 ticker 抽取，但 action 和 conviction 容易被误判；Seed 的 finance signals 必须允许 `unknown`、保留证据引用和 uncertainty，不能把每次提及都当推荐。
28. AlphaCheck 的产品启发是：用户真正关心频道级 track record，包括每个标的当时价格、当前价格、是否跑赢 benchmark、top winners/losers 和上下文理由。Seed 当前先落地 `*.finance-signals.json`，下一步再接行情 provider 和跨视频收益归因。
29. “最近 10 天 top UP 都说了什么”不是单纯搜索问题，而是 date window + 批量 video pipeline + finance signals + channel digest。核心样本应由清单驱动，并在失败时保留原始平台错误与人工兜底策略。
30. 行情后验应先做可解释 baseline：显式 `标的=ticker` mapping、发布日附近收盘价、最新收盘价、可选 benchmark、source URL 和价格日期。不要在没有可靠映射时猜 ticker，也不要把涨跌幅解释成交易建议。
31. 下一步不要继续堆 summary 字段，应把 `finance-signals.json` 升级成观点事件 ledger：先判断是否存在 recommendation，再抽 ticker/entity、action、direction、horizon、conviction、entry/exit/invalidation、timestamp evidence 和 modality evidence。
32. VideoConviction 的 action taxonomy 可直接作为 Seed 初版参考：buy、hold、don't buy、sell、short sell；Seed 还需要兼容 watch、add、reduce、allocate、unknown，因为中文财经 UP 经常是“观察/等回调/配置/减仓”。
33. 后验评估不能只看 latest return。event 应根据 horizon 计算 1D/5D/20D/60D/latest、benchmark relative return 和风险指标；没有 horizon 时只输出 baseline，不做命中判断。
34. 新闻检索不要从“观点总结”开始。GDELT 适合作为开放覆盖 baseline，但结果仍是媒体报道集合；Seed 的 `news-digest` 必须先分 facts、reported claims、source gaps，再写行业影响机制。
35. 财报解析不要优先抓网页正文。SEC `submissions` 给 filing history，`companyfacts` 给可结构化 XBRL 指标；Seed 初版先把这两类 primary data 变成稳定 artifact，HTML filing/table 解析作为后续 provider。
36. 通用能力新增前必须保留调研记录。新闻检索、财报解析、OCR、motion、行情、fact-check 这类常见能力都应先查官方或成熟开源项目，把选型写进 `docs/research-competitors.md`，再实现最小 provider。
37. AI 方法论方向也应该作为 domain lens，而不是复制视频 pipeline。通用层继续负责采集、ASR、视觉、semantics、creator profile 和 DAG；AI practices 层只补充 practice events、belief events、capability signals、tooling patterns、个人/项目反补候选和证据缺口。
38. AI 时代“牛人观点”的核心价值不在名言摘抄，而在可复用工作流。Anthropic 和 OpenAI 的 agent 文档共同指向：真实价值来自任务边界、工具调用、验证、权限、日志和 review；Seed 应把这些结构化成 `ai-practice-signals`，再反补到 skills/checks。
39. 人物方法论要保留冲突和上下文。不同 AI 研究者、工程师、产品人对自动化程度、模型信任、eval、prompt/spec 和组织变革的观点可能相互冲突；digest 应聚合共识，也保留不一致和 evidence gaps。
40. 读书能力应按 source-grounded 长文档合成来做，而不是新增一个“大摘要”。NotebookLM、LlamaIndex 和 LangChain 的共同点是：source/chunk 先结构化，再按问题合成；Seed 应先落 `B*` evidence blocks，再抽 stable principles、decision rules、mental models、agent checks 和 source gaps。
41. Readwise/Zotero/Koreader 证明 reading ingestion 的主数据不是“整本书全文”，而是 highlights、annotations、notes、location、tags 和 source metadata。Seed 初版用本地 Markdown，后续 provider 应兼容这些来源，不把某一个平台格式写死到核心。
42. Zettelkasten/evergreen note 的启发是：书籍价值在于长期可复用的原子原则和链接，而不是一次性摘要。Seed 的 book methods 应能和 creator profile、video semantics、news facts、earnings facts、finance digest 做 cross-source hooks。
43. 微信读书接入建议先用官方 `weread-skills` 与 `WEREAD_API_KEY` 路径；非官方 cookie 逆向仅做备份能力，不作为主链路，先避免稳定性和合规风险。接入目标是可持续把书架与书籍笔记落入 `book-source`。
44. 美股股价展望类报告应先做“事实-观点-后验”分层：先记录标的、时间、动作、置信度与证据引用，再给出情景化区间。目标位只用于研判输入草案，不应以确定值写入或作为交易信号，必须标注不确定和替代假设。

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
- XHS-Downloader: https://github.com/JoeanAmier/XHS-Downloader
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
- VideoConviction: https://github.com/gtfintechlab/VideoConviction
- VideoConviction dataset: https://huggingface.co/datasets/gtfintechlab/VideoConviction
- AlphaCheck: https://alphacheck.ai/
- TickerReceipts: https://tickerreceipts.com/
- FinCap paper: https://arxiv.org/abs/2509.25745
- FinGPT: https://github.com/AI4Finance-Foundation/FinGPT
- FinRobot: https://github.com/AI4Finance-Foundation/FinRobot
- FinBERT: https://github.com/ProsusAI/finBERT
- FinRL: https://github.com/AI4Finance-Foundation/FinRL
- Anthropic Building Effective Agents: https://www.anthropic.com/research/building-effective-agents
- OpenAI Codex docs: https://platform.openai.com/docs/codex
- OpenAI Running Codex safely: https://openai.com/index/running-codex-safely/
- OpenAI Using Codex with your ChatGPT plan: https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan
- Simon Willison Using LLMs series: https://feeds.simonwillison.net/series/using-llms/
- pandas-datareader StooqDailyReader: https://pydata.github.io/pandas-datareader/devel/readers/stooq.html
- pandas-datareader Stooq source: https://github.com/pydata/pandas-datareader/blob/master/pandas_datareader/stooq.py
- GDELT DOC 2.0 API: https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/
- SEC EDGAR APIs: https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- SEC Accessing EDGAR Data: https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data
- LlamaIndex response synthesizers: https://developers.llamaindex.ai/python/framework/module_guides/querying/response_synthesizers/
- LangChain MapReduceDocumentsChain: https://api.python.langchain.com/en/latest/langchain/chains/langchain.chains.combine_documents.map_reduce.MapReduceDocumentsChain.html
- LangChain summarization examples: https://langchain-doc.readthedocs.io/en/latest/modules/indexes/chain_examples/summarize.html
- Readwise API: https://readwise.io/api_deets
- Readwise Reader API: https://readwise.io/reader_api
- OpenWeRead: https://github.com/Ceelog/OpenWeRead
- 微信读书官方 Skill: https://weread.qq.com/r/weread-skills
- Zotero Web API: https://www.zotero.org/support/dev/web_api/v3/basics
- NotebookLM source help: https://support.google.com/notebooklm/answer/16215270
- Obsidian Zettelkasten overview: https://obsidian.rocks/getting-started-with-zettelkasten-in-obsidian/
