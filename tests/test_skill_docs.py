from pathlib import Path

from seed.domains.finance import build_finance_signals_prompt
from seed.domains.news import build_news_semantics_prompt
from seed.domains.earnings import build_earnings_semantics_prompt
from seed.semantics.aggregator import build_creator_profile_prompt
from seed.semantics.analyzer import build_video_semantics_prompt
from seed.summarizers.codex_runner import build_summary_prompt
from seed.skill_refs import read_video_analysis_lenses


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


def test_finance_domain_lenses_are_injected(tmp_path):
    transcript_path = tmp_path / "finance.transcript.md"
    transcript_path.write_text("# Transcript\n\n## Chunk 1 (00:00:01)\nWatch AAPL.", encoding="utf-8")
    semantics_path = tmp_path / "finance.video-semantics.md"
    semantics_path.write_text(
        """---
owner: finance-owner
---

## Methods And Principles

- Watch AAPL because earnings may be a catalyst. [T1]
""",
        encoding="utf-8",
    )

    lenses = read_video_analysis_lenses(domains=["finance"])
    video_prompt = build_video_semantics_prompt(
        transcript_path=transcript_path,
        skill_path=Path("skills/video-semantics-analyzer/SKILL.md"),
        domain="finance",
    )
    profile_prompt = build_creator_profile_prompt(
        semantics_paths=[semantics_path],
        skill_path=Path("skills/creator-profile-aggregator/SKILL.md"),
        owner="finance-owner",
        domain="finance",
    )
    signals_prompt = build_finance_signals_prompt(
        semantics_path=semantics_path,
        title="Finance Demo",
        owner="finance-owner",
        platform="bilibili",
    )

    assert "Finance Domain Lenses" in lenses
    assert "Recommendation signal" in video_prompt
    assert "- Domain: finance" in profile_prompt
    assert '"recommendations"' in signals_prompt
    assert '"viewpoint_events"' in signals_prompt
    assert "not as advice from Seed" in signals_prompt


def test_news_and_earnings_domain_lenses_are_injected(tmp_path):
    semantics_path = tmp_path / "domain.video-semantics.md"
    semantics_path.write_text(
        """---
owner: domain-owner
---

## Main Claims

- A company reported revenue growth after an industry event. [T1]
""",
        encoding="utf-8",
    )

    news_lenses = read_video_analysis_lenses(domains=["news"])
    earnings_lenses = read_video_analysis_lenses(domains=["earnings"])
    news_prompt = build_news_semantics_prompt(
        semantics_path=semantics_path,
        title="News Demo",
        owner="domain-owner",
        platform="bilibili",
    )
    earnings_prompt = build_earnings_semantics_prompt(
        semantics_path=semantics_path,
        title="Earnings Demo",
        owner="domain-owner",
        platform="bilibili",
    )

    assert "News Domain Lenses" in news_lenses
    assert "Separate factual claims" in news_prompt
    assert "Earnings Domain Lenses" in earnings_lenses
    assert "needs_sec_verification" in earnings_prompt
