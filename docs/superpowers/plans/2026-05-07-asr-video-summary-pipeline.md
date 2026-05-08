# ASR Video Summary Pipeline Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a decoupled local pipeline that extracts audio from downloaded videos, transcribes it with an online ASR provider, stores transcript artifacts locally, then launches a Codex subprocess to summarize the transcript using a reusable video-summary skill.

**Architecture:** Keep platform download, ASR, and summarization independent. `media` handles ffmpeg and file sizing, `asr` exposes provider-specific transcription behind one function, `summarizers` launches Codex, and `skills/video-note-summarizer` stores reusable summarization instructions.

**Tech Stack:** Python 3.11+, Typer CLI, ffmpeg/ffprobe, DashScope/Qwen ASR, optional OpenAI Audio Transcriptions API, Codex CLI, Markdown/YAML local artifacts.

---

## Research Summary

- `danielmiessler/Fabric` is the strongest prompt-pattern reference: MIT, about 41k stars, includes `summarize`, `extract_wisdom`, and YouTube transcript processing patterns.
- `Mathews-Tom/armory` is a useful skill reference: MIT, about 225 stars, includes `youtube-analysis` with structured transcript analysis, video type patterns, timestamps, key concepts, technical terms, and takeaways.
- `Telhassani/openclaw-skill-video-summary` is a useful output-format reference: MIT, low stars, has Obsidian-style frontmatter and sections like Summary, Ideas, Insights, Quotes, Habits, Key Points, Takeaways.
- OpenAI official speech-to-text docs list `whisper-1`, `gpt-4o-mini-transcribe`, `gpt-4o-transcribe`, and `gpt-4o-transcribe-diarize`; upload limit is 25 MB.
- DashScope/Qwen is the default ASR provider for Chinese-first videos. Current implementation uses `qwen3-asr-flash` via DashScope's OpenAI-compatible API.

## Files

- Create: `src/seed/media.py` for ffmpeg audio extraction and size checks.
- Create: `src/seed/asr/__init__.py`, `src/seed/asr/openai_provider.py` for online ASR.
- Create: `src/seed/transcripts.py` for transcript markdown paths and formatting.
- Create: `src/seed/summarizers/__init__.py`, `src/seed/summarizers/codex_runner.py` for Codex subprocess summaries.
- Modify: `src/seed/cli.py` to add `transcribe-media` and `summarize-transcript`.
- Modify: `pyproject.toml` and `.env.example` for OpenAI ASR config.
- Create: `skills/video-note-summarizer/SKILL.md` and `skills/video-note-summarizer/references/video-summary-template.md`.
- Create tests for path generation, prompt rendering, command construction, and ffmpeg command arguments.

## Task 1: Media Audio Extraction

- [x] Add `seed.media.extract_audio()` with ffmpeg command construction.
- [x] Add `seed.media.ensure_upload_size()` with MB limit.
- [x] Test command shape without invoking OpenAI.

## Task 2: Online ASR Provider

- [x] Add OpenAI SDK dependency.
- [x] Add `transcribe_openai_audio()` with `OPENAI_API_KEY`, model, language, prompt, and response text extraction.
- [x] Keep provider boundary small so Deepgram/AssemblyAI can be added without changing CLI flow.

## Task 3: Transcript Artifact Writer

- [x] Add transcript markdown formatter with YAML frontmatter and plain transcript body.
- [x] Store under `library/transcripts/{slug}.transcript.md`.
- [x] Include provider, model, source media path, audio path, and created timestamp.

## Task 4: Codex Summary Runner

- [x] Add prompt renderer that combines transcript, metadata, and skill template.
- [x] Add `run_codex_summary()` that calls `codex exec` non-interactively and writes last message to `library/notes/`.
- [x] Support `--dry-run` to save the prompt without calling Codex.

## Task 5: Video Summary Skill

- [x] Create a repo-local skill based on the researched patterns: summary, ideas, insights, quotes, habits, key points, takeaways, methodology candidates, and agent checks.
- [x] Keep it platform-neutral for Bilibili, Xiaohongshu, YouTube, and local files.
- [x] Document transcript-only limitations and visual-content caveats.

## Task 6: CLI Integration and Verification

- [x] Add `seed transcribe-media`.
- [x] Add `seed summarize-transcript`.
- [x] Update README quickstart.
- [x] Run `ruff`, `pytest`, CLI help, and demo where credentials allow.
