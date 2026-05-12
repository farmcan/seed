# Video Analysis Lenses

这些 lenses 用来约束视频分析，不是固定模板。只有当 transcript、visual notes、timeline 或截图证据支持时才使用。

## 来源参考

- Fabric prompt patterns：借鉴 transcript-first、timestamp-first、extract wisdom 的结构化提炼方式。
- BiliNote：借鉴 Markdown 笔记、截图、时间戳、关键帧与正文对齐的产品形态。
- tldw server / NotebookLM 类产品：借鉴媒体 ingestion、source-grounded analysis、后续问答和研究助手形态。
- 短视频结构分析：借鉴 hook、promise、setup、proof、payoff、CTA、retention device 的拆解方式。

## 证据层级

1. Transcript evidence：ASR、字幕、明确出现的口播内容。
2. Visual evidence：关键帧、屏幕文字、人物/物体/界面、场景变化。
3. Timeline evidence：timestamp、chunk、keyframe、广告候选、结构阶段。
4. Cross-video evidence：同一 UP/作者多条视频中反复出现的模式。
5. Inference：基于以上证据的解释，必须标明不确定性。

## 单条视频分析

- Content type：教程、评论、访谈、播客、产品演示、短视频、广告植入、观点输出。
- Viewer job：观众为什么看这条视频，想解决什么问题。
- Claim map：核心主张、支撑证据、反例、缺失证据。
- Structure map：hook、promise、setup/context、proof/reveal/demo、payoff、CTA。
- Retention map：悬念、冲突、反转、节奏、视觉切换、口头梗、列表化进度。
- Method map：原则、步骤、判断规则、适用场景、失效条件。
- Visual map：场景流、屏幕文字、演示证据、信任构建、封面/标题信号。

## 60 秒内短视频强分析

- Short profile：先确认 duration、fps、竖屏/横屏、音轨、平台和是否强制进入短视频链路。
- Shot map：按 shot boundary 拆 start/end、duration、代表帧、转场类型和节奏密度。
- Frame evidence：逐帧或密集帧记录 timestamp、所属 shot、画面主体、物体、场景、构图、动作、字幕/OCR、视觉效果和不确定性。
- First-three-seconds：前三秒是否给出人物/场景/冲突/承诺/反差，不要只看标题。
- Beat map：Hook -> Setup/Context -> Proof/Development -> Turn/Reframe -> Payoff/Loop/CTA。
- Editing map：cut frequency、jump cut、match cut、速度变化、字幕节奏、音效卡点、画面反差、循环结尾。
- Visual semantics：画面本身传达的信息，包括主体关系、视线方向、空间层次、屏幕文字、手势、道具和界面状态。
- Visual effects：识别蒙版、画中画、贴纸、滤镜/LUT、变速、文字覆盖、绿幕/抠像、分屏和素材叠加；这些是短视频叙事证据，不只是装饰。
- Subtitle map：记录字幕是否存在、文案、样式、位置、节奏和是否承担主要信息传递。
- Human motion relation：记录人物之间、人物与镜头、人物与物体的运动关系，例如靠近/远离、追随、对视、手部演示、遮挡、转场动作。
- Retention devices：悬念、进度条、倒计时、反转、连续动作、未完成任务、问题延迟回答、结尾回环。

短视频结论必须引用 transcript、OCR、shot timing、frame evidence 或 timeline。营销式“爆款公式”只能作为观察 lens，不能当作无证据结论。

## 创作者聚合

- Recurring method：同一判断方式是否在多条视频中重复出现。
- Recurring structure：开场、铺垫、论证、收尾是否稳定。
- Recurring evidence style：偏数据、案例、截图、亲历、权威引用还是情绪化表达。
- Recurring language：常用类比、口头禅、价值判断、世界观框架。
- Reliability gap：哪些结论只出现一次，哪些缺少外部核验。

## 输出要求

- 输出必须能被 `video-semantics.md`、`timeline.json`、`claims.json`、short profile、shots、frame notes、creator profile 和 Agent skills 消费。
- 不要只写“内容很好/很有启发”这类不可复用描述。
- 每个强结论都要能回到 transcript、visual notes、timeline 或具体视频语义。
- 如果证据不足，显式写进 Open Questions 或 Evidence Gaps。
