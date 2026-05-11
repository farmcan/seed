---
name: video-semantics-analyzer
description: Fuse video transcript and visual notes into a reusable semantic artifact for creator-level aggregation and agent skills.
---

# Video Semantics Analyzer

## Purpose

Convert one video into a stable semantic artifact. Treat spoken language and visual language as separate evidence streams, then fuse them into reusable knowledge for later creator/UP aggregation.

Before analysis, use `references/video-analysis-lenses.md` as the shared lens library. Do not invent a new structure when the lens file already covers the evidence type or video structure question.

## Attribution

This skill is inspired by:

- Fabric prompt patterns, especially transcript-first summary and extraction-oriented patterns.
- BiliNote-style timestamped Markdown notes with screenshots/keyframes.
- tldw / NotebookLM-style source-grounded media analysis.
- Short-form video structure frameworks such as Hook -> Value -> Retention -> CTA and Hook -> Context -> Problem -> Reveal -> CTA.

Do not copy those patterns mechanically. Use them as analysis lenses only when supported by the provided transcript and visual notes.

## Inputs

- transcript text: what was said or captioned by ASR
- optional visual notes: what was shown in sampled frames
- title, owner/UP/author, platform, source paths when available

## Evidence Rules

- Separate verbal evidence, visual evidence, and inference.
- Prefer timestamp, chunk, keyframe, screenshot, or source path references when available.
- If visual notes are absent, say visual evidence is unavailable.
- If visual notes are sampled sparsely, avoid overclaiming editing rhythm or exact shot timing.
- Do not invent metrics, screen text, creator intent, or audience outcome.
- Use short quotes only when exact wording appears in the transcript.
- Prefer reusable semantics over generic summary.
- Strong creator-signal claims require repeated evidence across videos; single-video creator claims must be labeled provisional.

## Output Format

Return only Markdown with these sections:

## Metadata

- Title:
- Platform:
- Owner:
- Transcript basis:
- Visual basis:
- Evidence caveat:

## Semantic Summary

One paragraph that fuses what the video says and what it shows.

## Content Type

- Type:
- Why:
- Primary audience:
- Implied job-to-be-done:

## Verbal Language

- Main claims:
- Explanation style:
- Argument pattern:
- Repeated phrases or framing:
- Notable quotes:

## Visual Language

- Scene flow:
- On-screen text:
- Objects, people, actions:
- Product or demo evidence:
- Visual trust builders:
- Editing or retention devices:

## Video Structure

- Hook:
- Promise or value:
- Setup/context:
- Proof/reveal/demo:
- Payoff:
- CTA:
- Reusable script pattern:

## Methods And Principles

- Method candidates:
- Decision rules:
- Operating steps:
- Failure modes:
- When this method applies:
- When this method does not apply:

## Creator Signals

- Worldview:
- Taste/preferences:
- Teaching style:
- Trust-building style:
- Recurring patterns to track across videos:

## Agent Reuse

- Candidate skills:
- Pre-check questions:
- Post-task reflection questions:
- Prompt fragments:

## Open Questions

- Missing evidence:
- Follow-up videos or sources to collect:
