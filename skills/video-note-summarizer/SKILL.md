---
name: video-note-summarizer
description: Summarize ASR transcripts from Bilibili, Xiaohongshu, YouTube, podcasts, interviews, tutorials, and local videos into reusable notes, methodology candidates, viral-content structure, and Agent pre-checks. Use when a transcript should become a durable Seed knowledge artifact.
---

# Video Note Summarizer

## Purpose

Turn a transcript into a structured knowledge artifact that a human can review and an Agent can later reuse. This skill is transcript-first and platform-neutral.

## Inputs

- transcript text
- title, owner/UP/author, platform when available
- source path or source URL when available

## Workflow

1. Identify the content type: lecture, tutorial, interview, podcast, tech talk, vlog/story, product review, or short-form viral video.
2. Produce a grounded summary. Separate what the speaker said from inferred interpretation.
3. Extract reusable ideas, insights, quotes, habits/practices, key points, and takeaways.
4. If the content teaches a method, extract methodology candidates: principles, steps, decision rules, failure modes.
5. If the content is short-form or obviously performance-oriented, analyze the video structure: hook, promise, proof, retention devices, CTA, and reusable script pattern.
6. End with Agent checks: questions an Agent should ask before applying this content to a real task.

## Output Format

Return only Markdown with these sections:

```markdown
# {title}

## Source

- Platform:
- Owner:
- Transcript basis:
- Visual caveat:

## Summary

2-4 paragraphs. Be specific. Do not write generic praise.

## Core Ideas

- 5-12 bullets.

## Insights

- 3-8 bullets that synthesize beyond surface summary.

## Notable Quotes

- Short quotes only when wording is clearly present in transcript. Otherwise paraphrase and label as paraphrase.

## Practices / Habits

- Practical habits, routines, tactics, or behaviors. Use `N/A` if absent.

## Key Points

- 5-12 facts or claims someone should remember.

## Actionable Takeaways

- 3-8 actions the viewer can try.

## Methodology Candidates

- **Principles:**
- **Steps:**
- **Decision rules:**
- **Failure modes:**

## Video Structure

- **Hook:**
- **Viewer promise:**
- **Proof / examples:**
- **Retention devices:**
- **CTA:**
- **Reusable script pattern:**

## Agent Pre-Checks

- 5-10 questions an Agent should ask before applying this method.

## Tags

`#tag` `#tag_two`
```

## Rules

- Ground claims in the transcript. Do not invent metrics, visuals, or unstated facts.
- Mention when visual context is likely missing, especially for tutorials, demos, product reviews, and visual-first short videos.
- Keep quotes short and only use exact wording from the transcript.
- Prefer methodology extraction over generic summary when the content contains repeatable methods.
- For weak or noisy ASR, state uncertainty and avoid overfitting to garbled phrases.
