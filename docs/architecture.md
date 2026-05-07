# Architecture

`seed` 的主流程分为五层：

1. Source capture：保存 URL、平台、UP/作者、发布时间、素材路径和元数据。
2. Transcript：把视频、音频、书籍摘录或人工笔记统一成文本。
3. Summary：围绕一个创作者、主题或作品生成结构化总结。
4. Distillation：从总结中提炼方法论、决策规则、反例和检查问题。
5. Agent assets：输出 `SKILL.md`、checklist 和 prompt context，供 Agent 在任务前后使用。

```text
URL / book / note
  -> raw asset
  -> transcript / note
  -> structured summary
  -> methodology
  -> skill + pre-check + reflection log
```

平台下载适配器只负责采集和记录。内容理解、方法论提炼和 Agent 使用是独立层，避免把平台耦合扩散到整个系统。
