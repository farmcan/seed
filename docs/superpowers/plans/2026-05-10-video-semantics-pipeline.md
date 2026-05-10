# Video Semantics Pipeline Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a composable video semantics layer that fuses transcript and visual notes into a stable Markdown artifact for later creator-level aggregation.

**Architecture:** Keep video semantics separate from raw summary notes. `semantics.analyzer` owns output paths, prompt construction, and Codex execution; `skills/video-semantics-analyzer/SKILL.md` owns the analysis schema; CLI only wires inputs to the analyzer.

**Tech Stack:** Python 3.11+, Typer CLI, Codex CLI subprocess, Markdown artifacts, existing transcript and visual note readers.

---

## Research Summary

- Fabric patterns show that reusable prompt units should be Markdown, explicit about output sections, and focused on extraction.
- Existing video skills model video as two channels: audio/verbal evidence and visual/frame evidence.
- Short-form analysis frameworks are useful only as conditional sections: hook, promise/value, proof/reveal, retention devices, and CTA.

## Files

- Modify: `src/seed/library.py` to add `semantics` to local library directories.
- Modify: `.gitignore` to keep `library/semantics/*` private.
- Create: `src/seed/semantics/__init__.py`.
- Create: `src/seed/semantics/analyzer.py`.
- Create: `skills/video-semantics-analyzer/SKILL.md`.
- Modify: `src/seed/cli.py` to add `analyze-video-semantics`.
- Add: `tests/test_video_semantics.py`.
- Modify: `tests/test_library.py`.
- Modify: `README.md`.

## Task 1: Local Artifact Boundary

- [x] Add `semantics` to `LIBRARY_DIRS`.
- [x] Ignore `library/semantics/*` while preserving `.gitkeep`.
- [x] Update `test_init_library_creates_expected_dirs`.

## Task 2: Semantics Analyzer

- [x] Create `video_semantics_output_path(library_root, transcript_path, title=None)`.
- [x] Create `build_video_semantics_prompt(...)`.
- [x] Create `run_video_semantics_analysis(...)` with `dry_run` support.
- [x] Reuse `build_codex_exec_command` from the existing Codex runner.
- [x] Test output path, prompt inclusion, and dry-run output.

## Task 3: Analyzer Skill

- [x] Create `skills/video-semantics-analyzer/SKILL.md`.
- [x] Attribute inspirations to Fabric, multimodal video skills, and short-form structure frameworks.
- [x] Define sections for metadata, evidence, semantic summary, verbal language, visual language, structure, methodology, creator signals, and agent reuse.

## Task 4: CLI and Docs

- [x] Add `seed analyze-video-semantics TRANSCRIPT --visual-notes ...`.
- [x] Support `--title`, `--owner`, `--platform`, `--skill-path`, `--codex-model`, `--dry-run`, and `--root`.
- [x] Update README quickstart and route explanation.

## Task 5: Verification

- [x] Run `ruff check .`.
- [x] Run `pytest`.
- [x] Run CLI help for `analyze-video-semantics`.
- [x] Run a dry-run demo against local transcript plus visual notes.
- [x] Commit and push relevant code, docs, tests, and skills.
