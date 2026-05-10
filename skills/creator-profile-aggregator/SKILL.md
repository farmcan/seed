---
name: creator-profile-aggregator
description: Aggregate multiple video semantics artifacts into a creator-level methodology profile and reusable agent guidance.
---

# Creator Profile Aggregator

## Purpose

Synthesize multiple video semantics artifacts from the same creator/UP into a stable profile. The output should help an agent understand this creator's recurring methods, video structures, verbal style, visual language, and reusable checks.

## Inputs

- one or more `video-semantics.md` artifacts
- owner/UP/author
- platform when available

## Rules

- Ground every pattern in repeated evidence across videos when possible.
- Separate strong recurring patterns from one-off observations.
- Do not infer personality traits beyond observable content, style, and methods.
- If there is only one video, clearly mark the profile as provisional.
- Keep skills and checks concrete enough for an agent to use before, during, or after a task.

## Output Format

Return only Markdown with these sections:

## Metadata

- Owner:
- Platform:
- Videos analyzed:
- Confidence:

## Creator Summary

A concise synthesis of what this creator repeatedly teaches, demonstrates, or optimizes for.

## Recurring Methods

- Method:
- Evidence:
- When to use:
- Failure modes:

## Verbal Language Patterns

- Explanation style:
- Argument patterns:
- Repeated framing:
- Useful phrasing:

## Visual Language Patterns

- Common scene types:
- On-screen text style:
- Product/demo habits:
- Trust builders:
- Editing/retention habits:

## Video Structure Patterns

- Common hook:
- Common setup:
- Proof/demo pattern:
- Payoff:
- CTA:
- Reusable script templates:

## Agent Skills

Write candidate `SKILL.md` ideas that could be created later.

- Skill name:
- Trigger:
- Procedure:
- Inputs:
- Outputs:

## Pre-Checks

Questions an agent should ask before applying this creator's methods.

## Post-Task Reflection

Questions an agent should ask after using this creator's methods.

## Evidence Gaps

- Missing data:
- More videos to collect:
- Patterns that need confirmation:
