# Agent Skills 与爆款视频结构分析

## Skill 设计原则

skill 不是长篇知识库，而是 Agent 的工作流入口。每个 skill 应该短、明确、可触发，把复杂资料放到 references 里。

推荐拆成四类：

1. `content-summarizer`：把 transcript/读书笔记转成结构化总结。
2. `methodology-distiller`：把同作者/同主题多条总结提炼成方法论。
3. `viral-video-analyst`：分析爆款视频结构、hook、节奏和可复用模板。
4. `preflight-checker`：在 Agent 执行任务前，根据已有方法论做事前检查。

## content-summarizer

触发场景：有一条视频转写、书摘或文章，需要形成可复用笔记。

输出结构：

```yaml
source_summary:
  one_sentence: ""
  target_problem: ""
  audience: ""
  key_claims: []
  evidence: []
  steps: []
  examples: []
  caveats: []
  quotable_lines: []
  open_questions: []
```

要求：

- 不只总结观点，还要记录“为什么这样讲”和“例子如何支撑观点”。
- 区分事实、作者判断和 Agent 推断。
- 保留时间戳或章节位置，便于回查。

## methodology-distiller

触发场景：同一个 UP/作者/主题已有 3 条以上总结。

输出结构：

```yaml
methodology:
  repeated_beliefs: []
  operating_principles: []
  decision_rules: []
  content_patterns: []
  anti_patterns: []
  applicability:
    works_when: []
    fails_when: []
  skill_candidates: []
```

判断标准：

- 至少在多个来源中重复出现，才升级为方法论。
- 单条视频里的漂亮句子不要直接升格成原则。
- 每条原则都要能转成行为、判断或检查问题。

## viral-video-analyst

触发场景：用户要学习爆款视频结构、拆解创作者表达方式或复用选题模板。

分析维度：

| 维度 | 需要抽取的问题 |
| --- | --- |
| Packaging | 标题承诺了什么？封面/首帧制造了什么期待？ |
| Hook | 前 3 秒/前 30 秒如何让人继续看？有没有结果前置、冲突、反常识、悬念？ |
| Viewer promise | 观众看完会得到什么确定收益？ |
| Structure | 是问题-原因-方法-案例，还是故事-冲突-反转-结论？ |
| Retention devices | 是否有 open loop、阶段性奖励、反复升级问题、视觉变化？ |
| Proof | 用了数据、案例、亲身经历、对比、实验还是权威背书？ |
| Emotion | 情绪曲线如何变化：焦虑、好奇、惊讶、认同、爽感、行动欲？ |
| CTA | 是否引导关注、评论、收藏、购买、私信或下一条内容？ |
| Replicable template | 能否改写成一个可复用脚本骨架？ |

输出模板：

```yaml
viral_analysis:
  title_formula: ""
  hook_type: ""
  first_30_seconds:
    promise: ""
    tension: ""
    proof_preview: ""
  structure_beats: []
  retention_devices: []
  reusable_script: []
  why_it_may_have_worked: []
  risks_when_copying: []
```

YouTube 官方帮助文档建议创作者观察观众留存，并尝试修改视频前 30 秒以提升观看；TikTok Creative Codes 也把创意结构拆成 hook、body、close。这些都支持把开头承诺、主体证明和结尾行动作为通用分析骨架。Bilibili 官方“UP 主起航计划”也有封面、标题、爆款选题和爆款内容结构相关课程。

## preflight-checker

触发场景：Agent 开始写脚本、做选题、做产品、写文案、做策略前，需要拿已沉淀的方法论做检查。

检查问题：

```markdown
- 当前任务是否匹配这个 skill 的适用场景？
- 目标用户/观众是谁？
- 这个输出承诺解决什么具体问题？
- 是否有可验证证据，而不是只有观点？
- 是否有明确步骤、判断规则或取舍标准？
- 哪些条件下这个方法会失效？
- 有没有复盘指标？
```

## 反思闭环

每次 Agent 使用 skill 后，写一条 reflection：

```yaml
reflection:
  skill: ""
  task: ""
  used_checks: []
  helped: []
  failed_or_missing: []
  next_revision: []
```

这样 seed 会从“资料库”变成“会被任务结果校准的方法论库”。

## 第一批建议创建的 skills

1. `video-note-summarizer`：单条视频/书籍笔记总结。
2. `creator-methodology-distiller`：同作者多内容提炼。
3. `viral-video-structure-analyst`：爆款结构拆解。
4. `agent-preflight-from-methodology`：任务前检查。
5. `methodology-reflection-updater`：任务后复盘并更新方法论。

## Sources

- Skill creator guidance: `/Users/levi/.codex/skills/.system/skill-creator/SKILL.md`
- Fabric prompt patterns: https://github.com/danielmiessler/Fabric
- YouTube audience retention help: https://support.google.com/youtube/answer/9314415
- TikTok Creative Codes: https://ads.tiktok.com/business/library/Creative_Codes_ENG.pdf
- Bilibili UP 主起航计划课程: https://www.bilibili.com/video/BV1M3411A77j/
