from pathlib import Path

from seed.semantics.aggregator import build_creator_profile_prompt
from seed.semantics.analyzer import build_video_semantics_prompt
from seed.summarizers.codex_runner import build_summary_prompt


def test_video_skills_share_analysis_lenses():
    lens_path = Path("skills/video-semantics-analyzer/references/video-analysis-lenses.md")

    assert lens_path.exists()
    assert "Fabric" in lens_path.read_text(encoding="utf-8")
    assert "BiliNote" in lens_path.read_text(encoding="utf-8")
    assert "video-analysis-lenses.md" in Path(
        "skills/video-semantics-analyzer/SKILL.md"
    ).read_text(encoding="utf-8")
    assert "video-analysis-lenses.md" in Path("skills/video-note-summarizer/SKILL.md").read_text(
        encoding="utf-8"
    )
    assert "video-analysis-lenses.md" in Path(
        "skills/creator-profile-aggregator/SKILL.md"
    ).read_text(encoding="utf-8")


def test_video_prompts_include_shared_lenses_and_evidence_anchors(tmp_path):
    transcript_path = tmp_path / "demo.transcript.md"
    transcript_path.write_text(
        """---
title: Demo
---

# Transcript

## Chunk 1 (00:00:03)
This opening frames the audience problem.

## Chunk 2 (00:01:10)
This section explains the method.
""",
        encoding="utf-8",
    )
    visual_notes_path = tmp_path / "demo.visual.md"
    visual_notes_path.write_text(
        f"""---
frames:
  - {tmp_path / "frame-001.jpg"}
---

# Visual Notes

The first keyframe shows the demo screen.
""",
        encoding="utf-8",
    )
    semantics_path = tmp_path / "demo.video-semantics.md"
    semantics_path.write_text(
        """---
owner: demo-owner
---

# Video Semantics

## Main Claims

- The method improves review quality. [T1]
""",
        encoding="utf-8",
    )

    video_prompt = build_video_semantics_prompt(
        transcript_path=transcript_path,
        skill_path=Path("skills/video-semantics-analyzer/SKILL.md"),
        visual_notes_path=visual_notes_path,
    )
    summary_prompt = build_summary_prompt(
        transcript_path=transcript_path,
        skill_path=Path("skills/video-note-summarizer/SKILL.md"),
        visual_notes_path=visual_notes_path,
    )
    profile_prompt = build_creator_profile_prompt(
        semantics_paths=[semantics_path],
        skill_path=Path("skills/creator-profile-aggregator/SKILL.md"),
        owner="demo-owner",
    )

    assert "<analysis_lenses>" in video_prompt
    assert "<evidence_anchors>" in video_prompt
    assert "T1: Transcript chunk 1 at 00:00:03" in video_prompt
    assert "V1: Visual notes at" in video_prompt
    assert "F1: Keyframe" in video_prompt
    assert "Use these IDs in the final artifact" in summary_prompt
    assert "<analysis_lenses>" in profile_prompt
