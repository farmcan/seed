# Qwen VL Visual Pipeline Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a visual-analysis path that extracts representative video frames, analyzes them with DashScope `qwen-vl-max`, stores visual notes locally, and lets Codex summaries combine ASR transcript plus visual context.

**Architecture:** Keep visual processing separate from download, ASR, and summarization. `vision.frames` owns ffmpeg frame extraction, `vision.qwen_vl_provider` owns DashScope/OpenAI-compatible vision calls, `vision.notes` owns visual note artifacts, and `summarizers.codex_runner` accepts optional visual notes as extra context.

**Tech Stack:** Python 3.11+, Typer CLI, ffmpeg, DashScope OpenAI-compatible chat completions, `qwen-vl-max`, Markdown local artifacts.

---

## Research Summary

- Alibaba Cloud Model Studio documents Qwen-VL through an OpenAI-compatible API.
- `qwen-vl-max` and `qwen-vl-max-latest` are listed as supported visual models.
- Local images can be sent as base64 data URLs in `image_url.url`.
- The message format is standard multimodal chat content: text blocks plus `image_url` blocks.

## Files

- Create: `src/seed/vision/__init__.py`
- Create: `src/seed/vision/frames.py` for frame extraction and frame manifests.
- Create: `src/seed/vision/qwen_vl_provider.py` for image data URLs, prompts, and DashScope calls.
- Create: `src/seed/vision/notes.py` for visual note output paths and Markdown formatting.
- Modify: `src/seed/cli.py` to add `extract-frames` and `analyze-frames`.
- Modify: `src/seed/summarizers/codex_runner.py` to accept optional visual notes.
- Modify: `skills/video-note-summarizer/SKILL.md` to mention visual context.
- Add tests for frame command construction, data URLs, visual prompt construction, and summary prompt inclusion.

## Task 1: Frame Extraction

- [x] Create `build_extract_frames_command(media_path, output_dir, every_seconds, max_frames)`.
- [x] Create `extract_frames(media_path, library_root, every_seconds=5, max_frames=12)`.
- [x] Store frames under `library/frames/{media_slug}/frame_%04d.jpg`.
- [x] Add a lightweight `frames.json` manifest with media path, cadence, max frames, and frame paths.
- [x] Test command construction and manifest writing without invoking a real model.

## Task 2: Qwen-VL Provider

- [x] Create `image_data_url(path)` and `mime_type_for_image(path)`.
- [x] Create `build_visual_analysis_messages(frame_paths, prompt)`.
- [x] Create `analyze_frames_with_qwen_vl(frame_paths, model="qwen-vl-max")`.
- [x] Read `DASHSCOPE_API_KEY` or `QWEN_API_KEY`.
- [x] Use `https://dashscope.aliyuncs.com/compatible-mode/v1` by default.
- [x] Test message shape and data URL encoding.

## Task 3: Visual Notes

- [x] Create `visual_notes_output_path(library_root, media_path_or_frame_dir, title=None)`.
- [x] Write Markdown with source metadata, frame list, model, and model analysis.
- [x] Ensure outputs go to `library/notes/{slug}.visual.md`.

## Task 4: CLI Integration

- [x] Add `seed extract-frames MEDIA_PATH`.
- [x] Add `seed analyze-frames FRAME_DIR --model qwen-vl-max`.
- [x] Add `--visual-notes PATH` to `seed summarize-transcript`.
- [x] Keep commands composable; no one-shot process command yet.

## Task 5: Verification

- [x] Run `ruff` and `pytest`.
- [x] Run `extract-frames` on an existing downloaded Bilibili or Xiaohongshu video.
- [x] Run `analyze-frames` with `qwen-vl-max` if `DASHSCOPE_API_KEY` is present.
- [x] Run `summarize-transcript --dry-run --visual-notes ...` to verify visual notes enter the Codex prompt.
- [ ] Commit and push only relevant changes; confirm `git status -sb` is clean.

## Sources

- Qwen-VL official docs: https://www.alibabacloud.com/help/en/model-studio/vision/
- Qwen-VL OpenAI-compatible docs: https://help.aliyun.com/zh/model-studio/qwen-vl-compatible-with-openai
