# 最短实现路径

目标：用最小工程量跑通“授权内容 -> 转写/导入 -> 单条总结 -> UP/作者方法论 -> Agent skill/check”的闭环。

## MVP 范围

第一版不要做全自动爬虫平台。先做半自动、本地优先、可审计：

1. URL 记录：保存平台、UP/作者、标题、URL、是否授权、原始文件路径。
2. 内容导入：优先支持手动 Markdown/字幕导入；Bilibili 用 yt-dlp 作为可选下载器。
3. 转写：本地文件走 faster-whisper 或 Whisper；已有字幕就直接清洗。
4. 单条总结：输出结构化 Markdown/YAML。
5. 作者方法论：把多条总结聚合成 `distilled/{owner}-{topic}.yaml`。
6. Agent 资产：生成 `skills/{name}/SKILL.md` 和 `checks/{topic}.md`。

## 推荐技术栈

| 层 | MVP 选择 | 原因 |
| --- | --- | --- |
| CLI | Python + Typer | 快速实现批处理命令，易和下载/转写库集成。 |
| 数据格式 | Markdown + YAML | 人能读，Agent 能读，Git diff 友好。 |
| 下载 | yt-dlp 优先，XHS-Downloader 可选外部工具 | Bilibili 和小红书都先走同一个轻量路径；GPL 工具只作为外部进程，避免 license 混入。 |
| 转写 | faster-whisper 优先，Whisper 兜底 | 批量处理速度更好。 |
| LLM 调用 | 先抽象 provider 接口 | 后续可切 OpenAI、DeepSeek、Qwen 或本地模型。 |
| 检索 | 先用文件系统 + ripgrep | 初期知识量小，避免过早上向量库。 |
| 后期 RAG | LanceDB/Chroma + GraphRAG 思路 | 内容规模上来后再加。 |

## 里程碑

### M0：仓库初始化

- 建立 `library/` 私有目录。
- 建立 `docs/` 调研和 schema。
- 建立 CLI：`seed init-library`、`seed ingest-url`、`seed distill-note`。
- 默认不提交原始素材和总结产物。

### M1：手动导入闭环

- 从 Bilibili/小红书/书籍手动导入一份 transcript 或读书笔记。
- 生成单条总结：
  - 讲了什么
  - 解决什么问题
  - 方法步骤
  - 关键例子
  - 适用条件
  - 失效条件
- 聚合同一个 UP 的 3-5 条内容，生成一个方法论草稿。

### M2：Bilibili 半自动

- 用 yt-dlp 获取 metadata、字幕、音频。
- 若没有字幕，抽音频后转写。
- 支持合集/分 P/UP 空间的 manifest，但每次下载前要求 `authorized=true`。
- 保留 `download-archive`，避免重复抓取。

### M2.5：小红书半自动

- 默认走 `yt-dlp` 内置 `XiaoHongShu` extractor。
- 优先使用带 `xsec_token` 的新鲜分享链接，公开页面失效时提示需要 cookie。
- 支持 `XIAOHONGSHU_COOKIES_FILE` 或显式 `--cookies-from-browser chrome/safari/firefox`。
- 不把小红书专用 GPL 下载器代码并入仓库；如需增强稳定性，采用外部命令适配器调用 `JoeanAmier/XHS-Downloader`。

### M3：Skill 生成

- 把方法论 YAML 转成 skill 文件：
  - `name`
  - `description`
  - `when to use`
  - `workflow`
  - `checks`
  - `failure modes`
- 生成事前检查清单和任务后反思问题。

### M4：爆款结构分析

- 输入：视频 transcript、标题、封面描述、发布时间、播放/点赞/收藏/评论等指标。
- 输出：
  - 选题角度
  - 前 3 秒/前 30 秒 hook
  - 叙事结构
  - 信息密度
  - 情绪曲线
  - 证据和案例使用
  - CTA 或互动设计
  - 可复用模板

## 当前最短路径建议

先从“人工导入 10 条高质量视频/书籍笔记”开始，不要先写复杂下载器。下载器会消耗大量时间处理 cookies、反爬、平台变化和合规边界；方法论提炼能力才是 seed 的核心。

可执行顺序：

1. 用 `seed ingest-url --no-download` 记录视频。
2. 手动保存字幕、转写或读书摘录到 `library/transcripts/`。
3. 用总结 prompt 生成单条 note。
4. 每 3-5 条同作者内容做一次方法论聚合。
5. 把聚合结果转成 Agent skill。
6. 让 Agent 在真实任务前使用 skill，并记录哪里有效、哪里误导。

## 合规边界

Bilibili 用户协议中包含未经许可不得通过机器人、蜘蛛、爬虫等自动程序获取平台服务、内容、数据的条款。小红书也有平台内容和用户内容相关知识产权约束。实现上应采用“授权内容优先、默认只记录 URL、显式授权才下载、本地私有保存、不把素材推到 GitHub”的策略。

## Sources

- yt-dlp README: https://github.com/yt-dlp/yt-dlp/blob/master/README.md
- yt-dlp supported sites: https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md
- XHS-Downloader: https://github.com/JoeanAmier/XHS-Downloader
- OpenAI Whisper announcement: https://openai.com/index/whisper/
- faster-whisper: https://github.com/SYSTRAN/faster-whisper
- Bilibili 用户协议: https://game.bilibili.com/licence/h5/
- Bilibili Terms of User Service: https://www.bilibili.com/blackboard/protocal/activity-1RIGA-C2-.html
