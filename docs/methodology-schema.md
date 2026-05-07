# Methodology Schema

每个方法论产物建议包含：

```yaml
id: creator-or-topic-slug
title: 标题
source:
  platform: bilibili
  owner: UP 或作者
  urls: []
core_ideas: []
repeatable_methods: []
decision_rules: []
failure_modes: []
agent_checks: []
reflection_questions: []
```

生成 Agent skill 时，把 `repeatable_methods` 变成操作步骤，把 `decision_rules` 变成判断条件，把 `agent_checks` 变成事前检查项。
